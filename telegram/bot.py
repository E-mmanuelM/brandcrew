#!/usr/bin/env python3
"""
BrandCrew — Telegram Bot
Handles all human-in-the-loop interactions for the content pipeline.

Security: Every message checked against APPROVED_TELEGRAM_IDS whitelist.
Unknown IDs are silently ignored — no reply, no action, no exception.

State machine:
  IDLE                      — no active workflow
  AWAITING_IDEA_SELECTION   — bot sent 10 content ideas, waiting for multi-select
  AWAITING_DRAFT_APPROVAL   — bot sent a scored draft, waiting for approval
  AWAITING_IMAGE_APPROVAL   — image delivered, waiting for APPROVE or /regenerate_image

Image system:
  Social Media Designer Agent picks HTML template + fills variables →
  render_template.py renders JPG at 1080x1350 via Playwright →
  sends to Telegram for approval.

Idea selection flow:
  10 ideas arrive → user replies e.g. "1,3,5,7,9" → those 5 approved → rest rejected
  User can reply MORE for fresh batch, NONE to reject all, DONE to confirm and lock week
  Approved count always comes from Supabase (source of truth), not bot memory.

Draft flow after quality pass:
  Quality PASS → Telegram shows post text + score → human APPROVE → Image generates →
  Telegram shows image → human APPROVE → status=finalized → /get_post to grab for LinkedIn

Multi-platform repurposing:
  After posting to LinkedIn → /repurpose to create X thread + Substack draft + TikTok slides
  /repurpose x — just X/Twitter thread
  /repurpose substack — just Substack draft
  Repurposed content saved to Supabase repurposed_content table.

Run: python3 bot.py
Requires: .env with TELEGRAM_BOT_TOKEN, APPROVED_TELEGRAM_IDS,
          SUPABASE_URL, SUPABASE_SECRET_KEY
"""

import os
import sys
import json
import time
import logging
import subprocess
from datetime import datetime, timezone
from dotenv import load_dotenv

import requests
from supabase import create_client, Client

# ── Setup ──────────────────────────────────────────────────────────────────────

PROJECT_DIR = os.environ.get("PROJECT_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv(os.path.join(PROJECT_DIR, ".env"))

log = logging.getLogger("aom_bot")
if not log.handlers:
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    log_dir = os.path.join(PROJECT_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    fh = logging.FileHandler(os.path.join(log_dir, "bot.log"))
    fh.setFormatter(fmt)
    log.addHandler(fh)

# ── Config with startup validation ─────────────────────────────────────────────

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")

# Validate required env vars before proceeding
_startup_errors = []

if not BOT_TOKEN or BOT_TOKEN == "your-bot-token-here":
    _startup_errors.append(
        "TELEGRAM_BOT_TOKEN is missing or still set to the placeholder value.\n"
        "  → Open .env and paste your bot token from @BotFather on Telegram."
    )

if not SUPABASE_URL or "your-project-ref" in (SUPABASE_URL or ""):
    _startup_errors.append(
        "SUPABASE_URL is missing or still set to the placeholder value.\n"
        "  → Open .env and paste your Supabase project URL.\n"
        "  → Find it at: Supabase Dashboard → Project Settings → API → URL"
    )

if not SUPABASE_KEY or SUPABASE_KEY == "your-service-role-key-here":
    _startup_errors.append(
        "SUPABASE_SECRET_KEY is missing or still set to the placeholder value.\n"
        "  → Open .env and paste your Supabase service_role key (not anon key).\n"
        "  → Find it at: Supabase Dashboard → Project Settings → API → service_role"
    )

_raw_ids = os.getenv("APPROVED_TELEGRAM_IDS", "")
APPROVED_IDS = set()

if not _raw_ids or _raw_ids == "your-telegram-user-id":
    _startup_errors.append(
        "APPROVED_TELEGRAM_IDS is missing or still set to the placeholder value.\n"
        "  → Open .env and set your Telegram user ID (a number like 123456789).\n"
        "  → To find your ID: search for @userinfobot on Telegram, send /start, copy the number."
    )
else:
    try:
        APPROVED_IDS = set(int(i.strip()) for i in _raw_ids.split(",") if i.strip())
    except ValueError:
        _startup_errors.append(
            f"APPROVED_TELEGRAM_IDS contains non-numeric values: '{_raw_ids}'\n"
            "  → This must be a number (your Telegram user ID), e.g.: 123456789\n"
            "  → Multiple IDs can be comma-separated: 123456789,987654321\n"
            "  → To find your ID: search for @userinfobot on Telegram, send /start, copy the number."
        )

if _startup_errors:
    print("\n" + "=" * 60)
    print("BrandCrew — Bot Startup Failed")
    print("=" * 60)
    print("\nYour .env file has placeholder values that need to be replaced.\n")
    print("How to fix:")
    print("  1. Open your .env file:  nano .env")
    print("  2. Replace the placeholder values listed below with your real keys.")
    print("  3. Save and restart:  python3 telegram/bot.py\n")
    for i, err in enumerate(_startup_errors, 1):
        print(f"  {i}. {err}\n")
    print("=" * 60)
    sys.exit(1)

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

STATE_FILE = os.path.join(PROJECT_DIR, "logs", "bot_state.json")
SEEN_UPDATES_FILE = os.path.join(PROJECT_DIR, "logs", "bot_seen_updates.json")
MAX_MESSAGE_LENGTH = 1000

AGENT_SCRIPTS = {
    "research":               os.path.join(PROJECT_DIR, "agents", "research", "run.sh"),
    "ideation":               os.path.join(PROJECT_DIR, "agents", "ideation", "run.sh"),
    "writer":                 os.path.join(PROJECT_DIR, "agents", "writer", "run.sh"),
    "quality":                os.path.join(PROJECT_DIR, "agents", "quality", "run.sh"),
    "social_media_designer":  os.path.join(PROJECT_DIR, "agents", "social_media_designer", "run.sh"),
    "repurposing":            os.path.join(PROJECT_DIR, "agents", "repurposing", "run.sh"),
}

# ── Supabase ───────────────────────────────────────────────────────────────────

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Helpers ────────────────────────────────────────────────────────────────────

def get_approved_idea_count() -> int:
    """Query Supabase for the total number of approved ideas."""
    try:
        sb = get_supabase()
        result = sb.table("content_ideas").select("id").eq("status", "approved").execute()
        return len(result.data)
    except Exception as e:
        log.error(f"Error counting approved ideas: {e}")
        return 0

# ── Update deduplication ───────────────────────────────────────────────────────

def load_seen_updates() -> set:
    if os.path.exists(SEEN_UPDATES_FILE):
        try:
            with open(SEEN_UPDATES_FILE, "r") as f:
                data = json.load(f)
                return set(data.get("seen", []))
        except (json.JSONDecodeError, ValueError) as e:
            log.error(f"Corrupt seen_updates file, resetting: {e}")
            return set()
    return set()

def save_seen_updates(seen: set):
    seen_list = sorted(seen)[-200:]
    with open(SEEN_UPDATES_FILE, "w") as f:
        json.dump({"seen": seen_list}, f)

def is_duplicate_update(update_id: int) -> bool:
    seen = load_seen_updates()
    if update_id in seen:
        return True
    seen.add(update_id)
    save_seen_updates(seen)
    return False

# ── Input validation ───────────────────────────────────────────────────────────

def sanitize_input(text: str) -> str:
    text = text.strip()
    if len(text) > MAX_MESSAGE_LENGTH:
        text = text[:MAX_MESSAGE_LENGTH]
        log.warning(f"Input truncated to {MAX_MESSAGE_LENGTH} chars")
    return text

def sanitize_text(text: str) -> str:
    return text.encode("utf-8", errors="surrogatepass").decode("utf-8", errors="replace")

# ── State management ───────────────────────────────────────────────────────────

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError) as e:
            log.error(f"Corrupt bot_state.json, treating as empty: {e}")
            return {}
    return {}

def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def get_user_state(user_id: int) -> str:
    state = load_state()
    return state.get(str(user_id), {}).get("state", "IDLE")

def set_user_state(user_id: int, new_state: str, context: dict = None):
    state = load_state()
    state[str(user_id)] = {
        "state": new_state,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "context": context or {}
    }
    save_state(state)
    log.info(f"State for {user_id} -> {new_state}")

def get_user_context(user_id: int) -> dict:
    state = load_state()
    return state.get(str(user_id), {}).get("context", {})

def set_all_approved_users_state(new_state: str, context: dict = None):
    state = load_state()
    for uid in APPROVED_IDS:
        state[str(uid)] = {
            "state": new_state,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "context": context or {}
        }
    save_state(state)
    log.info(f"State for all approved users -> {new_state}")

# ── Telegram helpers ───────────────────────────────────────────────────────────

def send_message(chat_id: int, text: str, parse_mode: str = "HTML"):
    text = sanitize_text(text)
    resp = requests.post(f"{TELEGRAM_API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }, timeout=10)
    if not resp.ok:
        log.error(f"Failed to send message to {chat_id}: {resp.text}")

def send_photo(chat_id: int, image_path: str, caption: str = "", parse_mode: str = "HTML"):
    try:
        caption = sanitize_text(caption)
        if len(caption) > 1024:
            caption = caption[:1020] + "..."
        with open(image_path, "rb") as photo:
            resp = requests.post(
                f"{TELEGRAM_API}/sendPhoto",
                data={"chat_id": chat_id, "caption": caption, "parse_mode": parse_mode},
                files={"photo": photo},
                timeout=30
            )
        if not resp.ok:
            log.error(f"Failed to send photo to {chat_id}: {resp.text}")
            send_message(chat_id,
                "\u26a0\ufe0f Image exists but Telegram rejected it.\n"
                f"Path: <code>{image_path}</code>\n"
                "Try <code>/get_post</code> again or check logs."
            )
            return False
        return True
    except FileNotFoundError:
        log.error(f"Image file not found: {image_path}")
        send_message(chat_id,
            f"\u26a0\ufe0f Image file missing on VPS:\n<code>{image_path}</code>\n"
            "The file may have been cleaned up. Use /regenerate_image to create a new one."
        )
        return False
    except Exception as e:
        log.error(f"Error sending photo: {e}")
        send_message(chat_id,
            "\u26a0\ufe0f Could not send image due to an encoding or file error.\n"
            f"Error: <code>{type(e).__name__}</code>\n"
            "Check logs for details."
        )
        return False

def get_updates(offset: int = 0) -> list:
    resp = requests.get(f"{TELEGRAM_API}/getUpdates", params={
        "offset": offset,
        "timeout": 30
    }, timeout=35)
    if resp.ok:
        return resp.json().get("result", [])
    return []

# ── Security ───────────────────────────────────────────────────────────────────

def is_approved(user_id: int) -> bool:
    return user_id in APPROVED_IDS

# ── Agent trigger helpers ──────────────────────────────────────────────────────

def is_agent_running(agent_name: str) -> bool:
    try:
        sb = get_supabase()
        result = sb.table("agent_logs").select("id, started_at").eq(
            "agent_name", agent_name
        ).eq("status", "running").execute()
        return len(result.data) > 0
    except Exception as e:
        log.error(f"Error checking agent status: {e}")
        return False

def trigger_agent(agent_name: str, args: list = None) -> bool:
    script = AGENT_SCRIPTS.get(agent_name)
    if not script or not os.path.exists(script):
        log.error(f"Runner script not found for agent: {agent_name}")
        return False
    try:
        clean_env = {k: v for k, v in os.environ.items()
                     if k not in ("CLAUDECODE", "CLAUDE_CODE_SESSION", "CLAUDE_CODE")}
        clean_env["PROJECT_DIR"] = PROJECT_DIR
        cmd = ["bash", script] + (args or [])
        log_path = os.path.join(PROJECT_DIR, "logs", f"{agent_name}.log")
        subprocess.Popen(
            cmd,
            stdout=open(log_path, "a"),
            stderr=subprocess.STDOUT,
            env=clean_env
        )
        log.info(f"Triggered agent: {agent_name} {' '.join(args or [])}")
        return True
    except Exception as e:
        log.error(f"Failed to trigger {agent_name}: {e}")
        return False

# ── Pipeline status ────────────────────────────────────────────────────────────

def get_pipeline_status() -> str:
    try:
        sb = get_supabase()
        ideas = sb.table("content_ideas").select("id").eq("status", "pending").execute()
        ideas_approved = sb.table("content_ideas").select("id").eq("status", "approved").execute()
        drafts_draft = sb.table("content_drafts").select("id").eq("status", "draft").execute()
        drafts_passed = sb.table("content_drafts").select("id").eq("status", "passed").execute()
        drafts_approved = sb.table("content_drafts").select("id").eq("status", "approved").execute()
        drafts_finalized = sb.table("content_drafts").select("id").eq("status", "finalized").eq("posted", False).execute()
        drafts_posted = sb.table("content_drafts").select("id").eq("posted", True).execute()
        topics = sb.table("research_topics").select("id").eq("used", False).execute()

        lines = [
            "\ud83d\udcca <b>Pipeline Status</b>",
            "",
            f"\ud83d\udd0d Research topics available: {len(topics.data)}",
            f"\ud83d\udca1 Ideas pending selection: {len(ideas.data)}",
            f"\ud83d\udca1 Ideas approved (queue): {len(ideas_approved.data)}",
            f"\u270d\ufe0f Drafts in progress: {len(drafts_draft.data)}",
            f"\u2705 Drafts passed quality: {len(drafts_passed.data)}",
            f"\ud83d\uddbc Awaiting image approval: {len(drafts_approved.data)}",
            f"\ud83d\udcec Posts ready (unposted): {len(drafts_finalized.data)}",
            f"\ud83d\udce4 Posts already posted: {len(drafts_posted.data)}",
            "",
            f"\ud83d\udd50 Checked: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC"
        ]
        return "\n".join(lines)
    except Exception as e:
        log.error(f"Error getting pipeline status: {e}")
        return "\u26a0\ufe0f Could not retrieve pipeline status. Check logs."

# ── Analytics summary ──────────────────────────────────────────────────────────

def get_analytics_summary() -> str:
    try:
        sb = get_supabase()
        result = sb.table("agent_logs").select("output_summary, completed_at").eq(
            "agent_name", "social_media_analyst"
        ).order("completed_at", desc=True).limit(1).execute()

        if not result.data:
            return (
                "\ud83d\udcc8 <b>Analytics</b>\n\n"
                "No analytics data yet. The Analytics Agent will appear here "
                "once posts are live and tracked."
            )

        latest = result.data[0]
        return (
            f"\ud83d\udcc8 <b>Latest Analytics</b>\n"
            f"<i>From: {latest['completed_at'][:10]}</i>\n\n"
            f"{latest.get('output_summary', 'No summary available.')}"
        )
    except Exception as e:
        log.error(f"Error getting analytics: {e}")
        return "\u26a0\ufe0f Could not retrieve analytics. Check logs."

# ── Command handlers ───────────────────────────────────────────────────────────

def handle_start(chat_id: int, user_id: int):
    send_message(chat_id,
        f"\ud83e\udd16 <b>BrandCrew \u2014 Your Content Team</b>\n\n"
        f"You're approved. Your Telegram ID: <code>{user_id}</code>\n\n"
        f"<b>Content Pipeline:</b>\n"
        f"/team_status \u2014 pipeline overview\n"
        f"/content_analytics \u2014 recent post performance\n"
        f"/research_now \u2014 scan for fresh topics\n"
        f"/ideate_now \u2014 generate 10 content ideas from research\n"
        f"/write_now \u2014 draft a post from the next approved idea\n"
        f"/quality_now \u2014 score the latest draft\n"
        f"/get_post \u2014 grab the next finalized post for LinkedIn\n\n"
        f"<b>Images:</b>\n"
        f"/regenerate_image [feedback] \u2014 regenerate image with feedback\n"
        f"/image_feedback [notes] \u2014 log image quality notes\n\n"
        f"<b>Multi-Platform:</b>\n"
        f"/repurpose \u2014 repurpose latest post to X, Substack, TikTok\n"
        f"/repurpose x \u2014 just the X/Twitter thread\n"
        f"/repurpose substack \u2014 just the Substack draft\n\n"
        f"<b>Strategy:</b>\n"
        f"/marketing_director [message] \u2014 note to your Marketing Director\n\n"
        f"Ideas and drafts arrive here automatically \u2014 just reply when they do."
    )

def handle_status(chat_id: int):
    send_message(chat_id, get_pipeline_status())

def handle_analytics(chat_id: int):
    send_message(chat_id, get_analytics_summary())

def handle_run_research(chat_id: int):
    if is_agent_running("niche_content_researcher"):
        send_message(chat_id, "\ud83d\udd04 Niche Content Researcher is already running.\nCheck back in ~10 minutes.")
        return
    success = trigger_agent("research")
    if success:
        send_message(chat_id, "\ud83d\udd0d <b>Niche Content Researcher triggered.</b>\nWill scan for trending topics and save to Supabase.\nYou'll get a summary when it completes.")
    else:
        send_message(chat_id, "\u26a0\ufe0f Could not trigger Research Agent.\nRunner script may not be installed yet. Check logs.")

def handle_run_writer(chat_id: int):
    if is_agent_running("content_creator"):
        send_message(chat_id, "\ud83d\udd04 Content Creator is already running.\nCheck back in ~5 minutes.")
        return
    try:
        sb = get_supabase()
        ideas = sb.table("content_ideas").select("id, hook").eq("status", "approved").order("created_at").limit(1).execute()
        if not ideas.data:
            send_message(chat_id, "\ud83d\udca1 No approved ideas in the queue.\nSelect ideas first, then trigger the writer.")
            return
        idea = ideas.data[0]
        trigger_agent("writer")
        send_message(chat_id, f"\u270d\ufe0f <b>Content Creator triggered.</b>\nWriting post for: <i>{idea.get('hook', 'approved idea')}</i>\nDraft will arrive here when ready.")
    except Exception as e:
        log.error(f"Error triggering writer: {e}")
        send_message(chat_id, "\u26a0\ufe0f Error triggering Content Creator. Check logs.")

def handle_get_post(chat_id: int):
    try:
        sb = get_supabase()
        drafts = sb.table("content_drafts").select(
            "id, draft_text, quality_score, image_url"
        ).eq("status", "finalized").eq("posted", False).order("created_at").limit(1).execute()

        if not drafts.data:
            send_message(chat_id, "\ud83d\udced No unposted finalized posts ready.\n\nA post needs both text APPROVE and image APPROVE before it's ready.\nCheck /team_status for pipeline state.")
            return

        draft = drafts.data[0]
        score = draft.get("quality_score") or "\u2014"
        image_url = draft.get("image_url")

        remaining = sb.table("content_drafts").select("id").eq("status", "finalized").eq("posted", False).execute()
        queue_count = len(remaining.data) - 1

        post_text = (
            f"\ud83d\ude80 <b>Ready for LinkedIn</b> (score: {score}/50)\n"
            f"Copy the text below and paste into LinkedIn:\n\n"
            f"\u2014\u2014\u2014\n\n"
            f"{draft['draft_text']}\n\n"
            f"\u2014\u2014\u2014\n\n"
            f"<i>Draft ID: <code>{draft['id'][:8]}</code> | "
            f"{queue_count} more in queue</i>"
        )

        if image_url and os.path.exists(image_url):
            sent = send_photo(chat_id, image_url, caption=post_text)
            if not sent:
                send_message(chat_id, post_text + "\n\n\u26a0\ufe0f <i>Image could not be sent.</i>")
        else:
            send_message(chat_id, post_text, parse_mode="HTML")
            if not image_url:
                send_message(chat_id, "\u2139\ufe0f <i>No image attached to this post.</i>")

        sb.table("content_drafts").update({"posted": True}).eq("id", draft["id"]).execute()
        log.info(f"Post {draft['id'][:8]} marked as posted. {queue_count} remaining in queue.")

    except Exception as e:
        log.error(f"Error getting post: {e}")
        send_message(chat_id, "\u26a0\ufe0f Could not retrieve post. Check logs.")

def handle_repurpose(chat_id: int, user_id: int, platform: str):
    """Repurpose the latest published LinkedIn post to other platforms."""
    if is_agent_running("repurposing"):
        send_message(chat_id, "\ud83d\udd04 Content Repurposer is already running.\nCheck back in ~10 minutes.")
        return
    try:
        sb = get_supabase()
        posts = sb.table("content_drafts").select("id, draft_text").eq(
            "posted", True
        ).order("updated_at", desc=True).limit(1).execute()

        if not posts.data:
            send_message(chat_id, "\ud83d\udced No published posts to repurpose.\nPost to LinkedIn first using /get_post, then use /repurpose.")
            return

        draft = posts.data[0]
        draft_id = draft["id"]
        preview = draft.get("draft_text", "")[:80]

        # Build args — draft_id is always first, platform filter is optional
        args = [draft_id]
        if platform:
            args.append(platform)

        success = trigger_agent("repurposing", args)
        if success:
            platform_label = platform.upper() if platform else "all platforms (X, Substack, TikTok)"
            send_message(chat_id,
                f"\ud83d\udd04 <b>Content Repurposer triggered</b>\n\n"
                f"Repurposing to: {platform_label}\n"
                f"Source: <i>{preview}...</i>\n\n"
                f"Results will arrive here when ready."
            )
            log.info(f"Repurposing triggered for draft {draft_id[:8]}, platform: {platform or 'all'}")
        else:
            send_message(chat_id, "\u26a0\ufe0f Could not trigger Content Repurposer.\nCheck that agents/repurposing/run.sh exists and is executable.")
    except Exception as e:
        log.error(f"Error triggering repurpose: {e}")
        send_message(chat_id, "\u26a0\ufe0f Error triggering Content Repurposer. Check logs.")

def handle_regenerate_image(chat_id: int, user_id: int, feedback: str):
    try:
        sb = get_supabase()
        draft = None
        for check_status in ("approved", "passed"):
            result = sb.table("content_drafts").select(
                "id, draft_text, image_url"
            ).eq("status", check_status).order("created_at", desc=True).limit(1).execute()
            if result.data:
                draft = result.data[0]
                break
        if not draft:
            send_message(chat_id, "\u26a0\ufe0f No draft found to regenerate an image for.\nThe pipeline needs to produce an approved draft first.")
            return

        draft_id = draft["id"]
        sb.table("agent_logs").insert({
            "agent_name": "social_media_designer", "action": "image_feedback",
            "status": "human_feedback", "input_data": feedback,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "notes": f"Image regeneration feedback for draft {draft_id}"
        }).execute()

        with open("/tmp/BrandCrew-image-feedback.txt", "w") as f:
            f.write(feedback)

        success = trigger_agent("social_media_designer", [draft_id])
        if success:
            send_message(chat_id, f"\ud83c\udfa8 <b>Regenerating image...</b>\n\nFeedback noted: <i>\"{feedback}\"</i>\n\nNew image will arrive here shortly.\n\n<i>(Feedback logged \u2014 will improve future images automatically)</i>")
        else:
            send_message(chat_id, "\u26a0\ufe0f Could not trigger Social Media Designer.\nCheck that agents/social_media_designer/run.sh exists and is executable.")
    except Exception as e:
        log.error(f"Error handling regenerate_image: {e}")
        send_message(chat_id, "\u26a0\ufe0f Error triggering image regeneration. Check logs.")

def handle_image_feedback(chat_id: int, user_id: int, feedback: str):
    try:
        sb = get_supabase()
        draft = None
        for check_status in ("finalized", "approved", "passed"):
            result = sb.table("content_drafts").select("id, image_url").eq(
                "status", check_status
            ).order("created_at", desc=True).limit(1).execute()
            if result.data and result.data[0].get("image_url"):
                draft = result.data[0]
                break

        draft_id = draft["id"] if draft else "no_draft"
        sb.table("agent_logs").insert({
            "agent_name": "social_media_designer", "action": "image_quality_feedback",
            "status": "human_feedback", "input_data": feedback,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "notes": f"Image quality feedback for draft {draft_id} \u2014 does NOT trigger regeneration."
        }).execute()

        send_message(chat_id, f"\ud83d\udcdd <b>Image feedback logged:</b>\n<i>\"{feedback}\"</i>\n\nSaved for the Marketing Director's Sunday review.\n\n<i>Want a new image now? Use /regenerate_image [feedback] instead.</i>")
    except Exception as e:
        log.error(f"Error logging image feedback: {e}")
        send_message(chat_id, "\u26a0\ufe0f Could not log image feedback. Check logs.")

def handle_run_ideation(chat_id: int):
    if is_agent_running("ideation"):
        send_message(chat_id, "\ud83d\udd04 Content Strategist is already running.\nCheck back in ~10 minutes.")
        return
    try:
        sb = get_supabase()
        topics = sb.table("research_topics").select("id").eq("used", False).limit(1).execute()
        if not topics.data:
            send_message(chat_id, "\ud83d\udd0d No unused research topics available.\nRun /research_now first to scan for fresh topics.")
            return
        success = trigger_agent("ideation")
        if success:
            send_message(chat_id, "\ud83d\udca1 <b>Content Strategist triggered.</b>\nWill generate 10 content ideas from research topics.\nIdeas will arrive here when ready.")
        else:
            send_message(chat_id, "\u26a0\ufe0f Could not trigger Content Strategist.\nCheck logs for details.")
    except Exception as e:
        log.error(f"Error triggering ideation: {e}")
        send_message(chat_id, "\u26a0\ufe0f Error triggering Content Strategist. Check logs.")

def handle_run_quality(chat_id: int):
    if is_agent_running("quality"):
        send_message(chat_id, "\ud83d\udd04 Quality Agent is already running.\nCheck back in ~5 minutes.")
        return
    try:
        sb = get_supabase()
        drafts = sb.table("content_drafts").select("id").eq("status", "draft").order("created_at", desc=True).limit(1).execute()
        if not drafts.data:
            send_message(chat_id, "\u270d\ufe0f No drafts waiting for quality review.\nThe writer needs to create a draft first.")
            return
        draft_id = drafts.data[0]["id"]
        success = trigger_agent("quality")
        if success:
            send_message(chat_id, f"\ud83d\udd0d <b>Quality Agent triggered.</b>\nScoring draft <code>{draft_id[:8]}...</code>\nResults will arrive here when ready.")
        else:
            send_message(chat_id, "\u26a0\ufe0f Could not trigger Quality Agent.\nCheck logs for details.")
    except Exception as e:
        log.error(f"Error triggering quality: {e}")
        send_message(chat_id, "\u26a0\ufe0f Error triggering Quality Agent. Check logs.")

def handle_marketing_director(chat_id: int, user_id: int, text: str):
    try:
        sb = get_supabase()
        sb.table("agent_logs").insert({
            "agent_name": "marketing_director", "action": "operator_feedback",
            "status": "human_input", "input_data": text,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "notes": "Strategic feedback from operator via Telegram"
        }).execute()
        send_message(chat_id, f"\ud83d\udccb <b>Marketing Director noted:</b>\n<i>\"{text}\"</i>\n\nLogged to Supabase. Will be factored into Sunday's guidance update.")
        log.info(f"Marketing Director input logged from {user_id}: {text}")
    except Exception as e:
        log.error(f"Error logging MD input: {e}")
        send_message(chat_id, "\u26a0\ufe0f Could not log message. Check logs.")

# ── State-based handlers ───────────────────────────────────────────────────────

def handle_idea_selection(chat_id: int, user_id: int, text: str):
    """Handle replies when in AWAITING_IDEA_SELECTION state."""
    text_upper = text.strip().upper()
    context = get_user_context(user_id)
    idea_ids = context.get("idea_ids", [])

    if text_upper == "MORE":
        try:
            sb = get_supabase()
            for idea_id in idea_ids:
                sb.table("content_ideas").update({"status": "rejected"}).eq("id", idea_id).eq("status", "pending").execute()
        except Exception as e:
            log.error(f"Error rejecting pending ideas before MORE: {e}")

        total_approved = get_approved_idea_count()
        set_user_state(user_id, "IDLE")
        success = trigger_agent("ideation")
        if success:
            send_message(chat_id, f"\ud83d\udd04 <b>Generating fresh ideas...</b>\n\nYou have {total_approved} idea(s) approved so far.\nContent Strategist is running. New batch will arrive shortly.")
        else:
            send_message(chat_id, "\u26a0\ufe0f Could not trigger Content Strategist. Check logs.")
        return

    if text_upper == "DONE":
        try:
            sb = get_supabase()
            pending = sb.table("content_ideas").select("id").eq("status", "pending").execute()
            rejected_count = 0
            for row in pending.data:
                sb.table("content_ideas").update({"status": "rejected"}).eq("id", row["id"]).execute()
                rejected_count += 1
            total_approved = get_approved_idea_count()
            set_user_state(user_id, "IDLE")
            send_message(chat_id, f"\ud83d\udd12 <b>Week locked in.</b>\n\n{total_approved} ideas approved, {rejected_count} rejected.\nWriter starts on the next weekday. First draft arrives when scheduled.")
            log.info(f"Week locked: {total_approved} approved, {rejected_count} rejected")
        except Exception as e:
            log.error(f"Error locking week: {e}")
            send_message(chat_id, "\u26a0\ufe0f Error locking selections. Check logs.")
        return

    if text_upper in ("0", "NONE", "REJECT"):
        try:
            sb = get_supabase()
            for idea_id in idea_ids:
                sb.table("content_ideas").update({"status": "rejected"}).eq("id", idea_id).execute()
        except Exception as e:
            log.error(f"Error rejecting ideas: {e}")

        total_approved = get_approved_idea_count()
        set_user_state(user_id, "IDLE")
        send_message(chat_id, f"\u274c <b>All ideas in this batch rejected.</b>\n\nYou have {total_approved} idea(s) approved so far.\nReply MORE for fresh ideas or /research_now to refresh topics first.")
        return

    cleaned = text.replace(" ", "")
    parts = cleaned.split(",")
    
    try:
        indices = [int(p) for p in parts if p]
        max_index = len(idea_ids)
        invalid = [i for i in indices if i < 1 or i > max_index]
        if invalid:
            send_message(chat_id, f"\u26a0\ufe0f Invalid numbers: {', '.join(str(i) for i in invalid)}\nValid range is 1-{max_index}. Try again.")
            return

        indices = sorted(set(indices))

        try:
            sb = get_supabase()
            approved_names = []
            for idx in indices:
                idea_id = idea_ids[idx - 1]
                sb.table("content_ideas").update({"status": "approved"}).eq("id", idea_id).execute()
                approved_names.append(str(idx))

            total_approved = get_approved_idea_count()
            picks_str = ", ".join(approved_names)
            send_message(chat_id,
                f"\u2705 <b>{len(indices)} idea(s) approved: {picks_str}</b>\n\n"
                f"Total approved this week: {total_approved}\n\n"
                f"Pick more numbers, or reply:\n"
                f"\u2022 <b>DONE</b> \u2014 lock the week (rejects all unpicked)\n"
                f"\u2022 <b>MORE</b> \u2014 generate fresh ideas"
            )
            log.info(f"Ideas approved: {picks_str} (total from Supabase: {total_approved})")
        except Exception as e:
            log.error(f"Error approving ideas: {e}")
            send_message(chat_id, "\u26a0\ufe0f Error saving selection. Check logs.")
        return

    except ValueError:
        pass

    try:
        sb = get_supabase()
        sb.table("agent_logs").insert({
            "agent_name": "content_strategist", "action": "idea_adjustment",
            "status": "human_adjustment", "input_data": text,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "notes": "Operator requested idea adjustment via Telegram"
        }).execute()
        send_message(chat_id, f"\ud83d\udcdd <b>Adjustment noted:</b> <i>\"{text}\"</i>\n\nLogged for the Content Strategist.\nYou can still pick numbers, reply MORE, or DONE.")
    except Exception as e:
        log.error(f"Error logging idea adjustment: {e}")
        send_message(chat_id, "\u26a0\ufe0f Error logging adjustment. Check logs.")

def handle_draft_review(chat_id: int, user_id: int, text: str):
    text_upper = text.strip().upper()
    context = get_user_context(user_id)
    draft_id = context.get("draft_id")

    if not draft_id:
        send_message(chat_id, "\u26a0\ufe0f No active draft found. State may have reset.")
        set_user_state(user_id, "IDLE")
        return

    try:
        sb = get_supabase()

        if text_upper == "APPROVE":
            sb.table("content_drafts").update({"status": "approved"}).eq("id", draft_id).execute()
            set_user_state(user_id, "IDLE")
            success = trigger_agent("social_media_designer", [draft_id])
            if success:
                send_message(chat_id, "\u2705 <b>Text approved \u2014 designing image now.</b>\n\nThe Social Media Designer is creating a branded visual.\nWhen the image arrives, reply APPROVE to finalize or\nuse /regenerate_image [feedback] for changes.")
                log.info(f"Social Media Designer triggered for approved draft {draft_id}")
            else:
                send_message(chat_id, "\u2705 <b>Text approved.</b>\n\n\u26a0\ufe0f Could not trigger Social Media Designer.\nCheck logs and retry with /regenerate_image.")

        elif text_upper == "REJECT":
            sb.table("content_drafts").update({"status": "rejected"}).eq("id", draft_id).execute()
            set_user_state(user_id, "IDLE")
            send_message(chat_id, "\u274c <b>Draft rejected.</b>\n\nDiscarded. The Content Strategist will generate new ideas on Sunday.")

        else:
            current = sb.table("content_drafts").select("retry_count").eq("id", draft_id).execute()
            retry_count = 0
            if current.data:
                retry_count = (current.data[0].get("retry_count") or 0) + 1
            sb.table("content_drafts").update({
                "status": "draft", "edit_notes": text, "retry_count": retry_count
            }).eq("id", draft_id).execute()
            sb.table("agent_logs").insert({
                "agent_name": "content_creator", "action": "edit_requested",
                "status": "edit_requested", "input_data": text,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "notes": f"Edit notes for draft {draft_id}"
            }).execute()
            set_user_state(user_id, "IDLE")
            trigger_agent("writer")
            send_message(chat_id, f"\u270f\ufe0f <b>Edit notes saved:</b> <i>\"{text}\"</i>\n\nContent Creator is rewriting now. New draft coming shortly.\n<i>(Edit logged \u2014 Marketing Director uses this to improve future drafts)</i>")

    except Exception as e:
        log.error(f"Error handling draft review: {e}")
        send_message(chat_id, "\u26a0\ufe0f Error processing response. Check logs.")

def handle_image_review(chat_id: int, user_id: int, text: str):
    text_upper = text.strip().upper()
    context = get_user_context(user_id)
    draft_id = context.get("draft_id")

    if not draft_id:
        send_message(chat_id, "\u26a0\ufe0f No active draft found. State may have reset.")
        set_user_state(user_id, "IDLE")
        return

    try:
        sb = get_supabase()

        if text_upper == "APPROVE":
            sb.table("content_drafts").update({"status": "finalized"}).eq("id", draft_id).execute()
            set_user_state(user_id, "IDLE")
            send_message(chat_id, "\u2705 <b>Post finalized!</b>\n\nBoth text and image are locked in.\nUse /get_post to grab it for LinkedIn.\nAfter posting, use /repurpose to create versions for X, Substack, and TikTok.")
            log.info(f"Draft {draft_id} finalized")

        elif text_upper == "REJECT":
            sb.table("content_drafts").update({
                "image_url": None, "template_name": None, "template_vars": None
            }).eq("id", draft_id).execute()
            set_user_state(user_id, "IDLE")
            send_message(chat_id, "\u274c <b>Image rejected.</b>\n\nImage cleared. Use /regenerate_image [feedback] to try again\nwith specific notes on what you want changed.")
            log.info(f"Image rejected for draft {draft_id}")

        else:
            feedback = text.strip()
            with open("/tmp/BrandCrew-image-feedback.txt", "w") as f:
                f.write(feedback)
            sb.table("agent_logs").insert({
                "agent_name": "social_media_designer", "action": "image_feedback",
                "status": "human_feedback", "input_data": feedback,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "notes": f"Image edit feedback for draft {draft_id}"
            }).execute()
            set_user_state(user_id, "IDLE")
            trigger_agent("social_media_designer", [draft_id])
            send_message(chat_id, f"\ud83c\udfa8 <b>Regenerating image with your feedback:</b>\n<i>\"{feedback}\"</i>\n\nNew image will arrive shortly.")
            log.info(f"Image regeneration for draft {draft_id}: {feedback}")

    except Exception as e:
        log.error(f"Error handling image review: {e}")
        send_message(chat_id, "\u26a0\ufe0f Error processing response. Check logs.")

# ── Main message router ────────────────────────────────────────────────────────

def route_message(message: dict):
    user_id = message["from"]["id"]
    chat_id = message["chat"]["id"]
    raw_text = message.get("text", "").strip()

    if not is_approved(user_id):
        return

    text = sanitize_input(raw_text)
    if not text:
        return

    log.info(f"Message from {user_id}: {text[:50]}")

    # ── Slash commands ─────────────────────────────────────────────────────
    if text.startswith("/start"):
        handle_start(chat_id, user_id)
        return
    if text.startswith("/team_status"):
        handle_status(chat_id)
        return
    if text.startswith("/content_analytics"):
        handle_analytics(chat_id)
        return
    if text.startswith("/research_now"):
        handle_run_research(chat_id)
        return
    if text.startswith("/write_now"):
        handle_run_writer(chat_id)
        return
    if text.startswith("/get_post"):
        handle_get_post(chat_id)
        return
    if text.startswith("/ideate_now"):
        handle_run_ideation(chat_id)
        return
    if text.startswith("/quality_now"):
        handle_run_quality(chat_id)
        return

    if text.lower().startswith("/repurpose"):
        platform_arg = text[len("/repurpose"):].strip().lower()
        valid_platforms = ("x", "twitter", "substack", "tiktok", "all", "")
        if platform_arg == "twitter":
            platform_arg = "x"
        if platform_arg == "all":
            platform_arg = ""
        if platform_arg not in valid_platforms:
            send_message(chat_id,
                "Usage: /repurpose [platform]\n\n"
                "Examples:\n"
                "\u2022 /repurpose \u2014 all platforms (X, Substack, TikTok)\n"
                "\u2022 /repurpose x \u2014 just the X/Twitter thread\n"
                "\u2022 /repurpose substack \u2014 just the Substack draft\n"
                "\u2022 /repurpose tiktok \u2014 just TikTok slides"
            )
            return
        handle_repurpose(chat_id, user_id, platform_arg)
        return

    if text.lower().startswith("/regenerate_image"):
        feedback = text[len("/regenerate_image"):].strip()
        if feedback:
            handle_regenerate_image(chat_id, user_id, feedback)
        else:
            send_message(chat_id, "Usage: /regenerate_image [your feedback]\n\nExamples:\n\u2022 /regenerate_image make the headline bolder\n\u2022 /regenerate_image use a different template")
        return

    if text.lower().startswith("/image_feedback"):
        feedback = text[len("/image_feedback"):].strip()
        if feedback:
            handle_image_feedback(chat_id, user_id, feedback)
        else:
            send_message(chat_id, "Usage: /image_feedback [your notes]\n\nLogs quality notes for the Marketing Director's Sunday review.\n\nWant a new image now? Use /regenerate_image [feedback] instead.")
        return

    if text.lower().startswith("/marketing_director "):
        md_text = text[len("/marketing_director "):].strip()
        if md_text:
            handle_marketing_director(chat_id, user_id, md_text)
        else:
            send_message(chat_id, "Usage: /marketing_director [your message]")
        return

    # ── State-based routing ────────────────────────────────────────────────
    current_state = get_user_state(user_id)

    if current_state == "AWAITING_IDEA_SELECTION":
        handle_idea_selection(chat_id, user_id, text)
        return
    if current_state == "AWAITING_DRAFT_APPROVAL":
        handle_draft_review(chat_id, user_id, text)
        return
    if current_state == "AWAITING_IMAGE_APPROVAL":
        handle_image_review(chat_id, user_id, text)
        return

    if current_state == "IDLE":
        text_upper = text.strip().upper()
        draft_keywords = ("APPROVE", "REJECT", "EDIT")
        looks_like_draft_reply = any(text_upper.startswith(k) for k in draft_keywords)

        if looks_like_draft_reply:
            try:
                sb = get_supabase()
                approved_with_image = sb.table("content_drafts").select("id, image_url").eq(
                    "status", "approved"
                ).order("created_at", desc=True).limit(1).execute()
                if approved_with_image.data and approved_with_image.data[0].get("image_url"):
                    draft_id = approved_with_image.data[0]["id"]
                    set_user_state(user_id, "AWAITING_IMAGE_APPROVAL", {"draft_id": draft_id})
                    handle_image_review(chat_id, user_id, text)
                    return

                for check_status in ("draft", "passed"):
                    pending = sb.table("content_drafts").select("id").eq(
                        "status", check_status
                    ).order("created_at", desc=True).limit(1).execute()
                    if pending.data:
                        draft_id = pending.data[0]["id"]
                        set_user_state(user_id, "AWAITING_DRAFT_APPROVAL", {"draft_id": draft_id})
                        handle_draft_review(chat_id, user_id, text)
                        return
            except Exception as e:
                log.error(f"Error checking for pending drafts: {e}")

    # ── Fallback help ──────────────────────────────────────────────────────
    send_message(chat_id,
        "\ud83e\udd16 <b>BrandCrew \u2014 Your Content Team</b>\n\n"
        "<b>Content Pipeline:</b>\n"
        "/team_status \u2014 pipeline overview\n"
        "/content_analytics \u2014 recent post performance\n"
        "/research_now \u2014 scan for fresh topics\n"
        "/ideate_now \u2014 generate 10 content ideas from research\n"
        "/write_now \u2014 draft a post from the next approved idea\n"
        "/quality_now \u2014 score the latest draft\n"
        "/get_post \u2014 grab the next finalized post for LinkedIn\n\n"
        "<b>Images:</b>\n"
        "/regenerate_image [feedback] \u2014 regenerate image with feedback\n"
        "/image_feedback [notes] \u2014 log image quality notes\n\n"
        "<b>Multi-Platform:</b>\n"
        "/repurpose \u2014 repurpose latest post to X, Substack, TikTok\n"
        "/repurpose x \u2014 just the X/Twitter thread\n"
        "/repurpose substack \u2014 just the Substack draft\n\n"
        "<b>Strategy:</b>\n"
        "/marketing_director [message] \u2014 note to your Marketing Director\n\n"
        "Ideas and drafts arrive here automatically \u2014 just reply when they do."
    )

# ── Poll loop ──────────────────────────────────────────────────────────────────

def run():
    if not BOT_TOKEN:
        log.error("TELEGRAM_BOT_TOKEN not set in .env")
        return
    if not APPROVED_IDS:
        log.error("APPROVED_TELEGRAM_IDS not set in .env")
        return

    log.info(f"Bot starting. Approved user count: {len(APPROVED_IDS)}")
    offset = 0

    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                update_id = update["update_id"]
                offset = update_id + 1
                if is_duplicate_update(update_id):
                    continue
                if "message" in update:
                    route_message(update["message"])
        except KeyboardInterrupt:
            log.info("Bot stopped by user.")
            break
        except Exception as e:
            log.error(f"Polling error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run()
