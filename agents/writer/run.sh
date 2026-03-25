#!/bin/bash
# BrandCrew — Content Creator (Writer Agent) Runner
# Runs Mon-Fri on the posting schedule defined in config/schedule.md
# Usage: bash agents/writer/run.sh

set -euo pipefail

# Use PROJECT_DIR from .env or default
REPO_DIR="${PROJECT_DIR:-/projects/brandcrew}"
LOG_PREFIX="[writer $(date '+%Y-%m-%d %H:%M:%S')]"
LOCK_FILE="/tmp/BrandCrew-writer.lock"

# ── Prevent overlapping runs ──────────────────────────────────────────────────────────
if [ -f "$LOCK_FILE" ]; then
  LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "$LOCK_FILE") ))
  if [ "$LOCK_AGE" -lt 3600 ]; then
    echo "$LOG_PREFIX SKIPPED — lock file exists (age: ${LOCK_AGE}s). Another run may be active."
    exit 0
  else
    echo "$LOG_PREFIX WARNING — stale lock file (age: ${LOCK_AGE}s). Removing and proceeding."
    rm -f "$LOCK_FILE"
  fi
fi
trap 'rm -f "$LOCK_FILE"' EXIT
touch "$LOCK_FILE"

# ── Ensure logs directory exists ──────────────────────────────────────────────────────
mkdir -p "$REPO_DIR/logs"

echo "$LOG_PREFIX Starting Content Creator (Writer Agent)"

# ── Pre-extract approved idea from Supabase ───────────────────────────────────
# This runs BEFORE Claude Code launches so we can inject the idea directly
# into the prompt as a hard constraint. Prevents the writer from drifting.
cd "$REPO_DIR"

IDEA_DATA=$(python3 -c "
from supabase import create_client
from dotenv import load_dotenv
import os, json
load_dotenv('$REPO_DIR/.env')
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SECRET_KEY'))

# Get approved idea
ideas = sb.table('content_ideas').select('id,hook,angle_description,angle,content_type,suggested_format').eq('status', 'approved').order('created_at', desc=True).limit(1).execute()
if not ideas.data:
    print(json.dumps({'error': 'no_idea'}))
else:
    idea = ideas.data[0]
    # Get recent draft hooks for dedup
    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
    drafts = sb.table('content_drafts').select('draft_text').gte('created_at', cutoff).order('created_at', desc=True).limit(5).execute()
    recent_hooks = []
    for d in (drafts.data or []):
        text = d.get('draft_text', '')
        # Extract first 2 lines as hook
        lines = [l.strip() for l in text.split('\\n') if l.strip()][:2]
        if lines:
            recent_hooks.append(' '.join(lines))
    idea['recent_hooks'] = recent_hooks
    print(json.dumps(idea))
" 2>/dev/null)

# Check if we got an idea
HAS_ERROR=$(echo "$IDEA_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print('yes' if 'error' in d else 'no')" 2>/dev/null || echo "yes")

if [ "$HAS_ERROR" = "yes" ]; then
  echo "$LOG_PREFIX No approved idea found — skipping"
  # Log and notify via quick Claude call
  claude -p "Log to Supabase agent_logs: agent_name=content_creator, action=weekly_draft, status=skipped, notes='No approved idea found in queue'. Then send Telegram message: 'No approved idea in queue. Select an idea first.' Use .env for credentials." \
    --dangerously-skip-permissions --max-turns 5 --output-format text 2>&1
  exit 0
fi

# Extract fields for prompt injection
IDEA_ID=$(echo "$IDEA_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
IDEA_HOOK=$(echo "$IDEA_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('hook',''))" 2>/dev/null)
IDEA_ANGLE=$(echo "$IDEA_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('angle_description',''))" 2>/dev/null)
IDEA_TYPE=$(echo "$IDEA_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('angle',''))" 2>/dev/null)
IDEA_FORMAT=$(echo "$IDEA_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('suggested_format',''))" 2>/dev/null)
RECENT_HOOKS=$(echo "$IDEA_DATA" | python3 -c "
import sys,json
data = json.load(sys.stdin)
hooks = data.get('recent_hooks', [])
for i,h in enumerate(hooks,1):
    print(f'{i}. {h}')
" 2>/dev/null)

echo "$LOG_PREFIX Approved idea: $IDEA_HOOK"
echo "$LOG_PREFIX Angle: $IDEA_ANGLE"
echo "$LOG_PREFIX Type: $IDEA_TYPE"

# ── Build dedup block ─────────────────────────────────────────────────────────────
DEDUP_BLOCK=""
if [ -n "$RECENT_HOOKS" ]; then
  DEDUP_BLOCK="
DEDUPLICATION — RECENT HOOKS (your new post MUST NOT resemble any of these):
$RECENT_HOOKS
If your draft's hook or core argument overlaps with any of the above, STOP and rewrite with a completely different angle."
fi

# ── Run Claude Code with the writer agent prompt ───────────────────────────────
claude -p "You are the Content Creator (Writer Agent). Read agents/writer/SKILL.md and execute the full process as defined.

═════════════════════════════════════════════════════════════════
YOUR ASSIGNMENT — THIS IS THE IDEA YOU MUST WRITE ABOUT:
═════════════════════════════════════════════════════════════════
Idea ID: $IDEA_ID
Hook: $IDEA_HOOK
Angle: $IDEA_ANGLE
Content Type: $IDEA_TYPE
Suggested Format: $IDEA_FORMAT
═════════════════════════════════════════════════════════════════

You MUST write a post about the SPECIFIC angle described above.
Do NOT drift to adjacent topics. Do NOT generalize.
The hook above is your STARTING POINT — use it or improve it, but stay on THIS angle.
If you find yourself writing about something else, STOP and return to this angle.
$DEDUP_BLOCK

Now follow these steps:

1. Load required files IN ORDER: config/voice.md, config/niche.md, rules/quality-standards.md, rules/linkedin-playbook.md
2. Load performance-patterns.md (skip if first line says PLACEHOLDER) — this contains the Marketing Director's weekly direction. Pay attention to content type instructions, what to avoid, and any specific format guidance.
3. Load agents/writer/references/post-examples.md (skip if first line says PLACEHOLDER)
4. The approved idea is provided above — do NOT re-query Supabase for it. Use the hook, angle, and content type exactly as given.
5. Query Supabase ip_library WHERE tags overlap with the idea (max 3 entries). If table is empty or does not exist, continue without IP.
6. Draft the post following the structure in SKILL.md:
   - Hook (lines 1-2): stop-the-scroll, never open with a question, never open with 'I'
   - Body: 3-5 short paragraphs, 1-2 lines each, real substance
   - Insight: specific takeaway with a number, system, or before/after
   - CTA: only if it earns its place
   - If performance-patterns.md said to use a specific format or approach, follow it
7. Self-check before saving:
   - Re-read rules/quality-standards.md — does the post fail any filter? Rewrite if yes.
   - Re-read config/voice.md — does it sound like the content owner? Rewrite if not.
   - Re-read rules/linkedin-playbook.md — does it follow format rules? Correct if not.
   - Is the hook strong enough? Try 3 alternatives and pick the best.
   - Does this post match the ASSIGNED ANGLE above? If not, rewrite.
   - Does this post follow the Marketing Director's direction from performance-patterns.md? If not, adjust.
8. Target 900-1300 characters. No hashtags.
9. Save to Supabase content_drafts with status = 'draft'. IMPORTANT: also save content_idea_id = '$IDEA_ID' on the draft row.
10. Log to Supabase agent_logs (agent_name: content_creator, action: weekly_draft, status: completed)
11. Send Telegram notification: 'Draft ready for quality review.'

Use .env for all credentials. Never log credentials." \
  --dangerously-skip-permissions \
  --max-turns 25 \
  --output-format text \
  2>&1

EXIT_CODE=$?

echo "$LOG_PREFIX Finished with exit code $EXIT_CODE"

if [ $EXIT_CODE -ne 0 ]; then
  echo "$LOG_PREFIX ERROR — Claude Code exited with code $EXIT_CODE"
else
  # ── Auto-chain: trigger Quality Agent if a draft was saved ────────────────
  DRAFT_EXISTS=$(cd "$REPO_DIR" && python3 -c "
from supabase import create_client
from dotenv import load_dotenv
import os
load_dotenv('$REPO_DIR/.env')
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SECRET_KEY'))
r = sb.table('content_drafts').select('id').eq('status', 'draft').limit(1).execute()
print('yes' if r.data else 'no')
" 2>/dev/null)

  if [ "$DRAFT_EXISTS" = "yes" ]; then
    echo "$LOG_PREFIX Draft found — chaining to Quality Agent"
    bash "$REPO_DIR/agents/quality/run.sh" >> "$REPO_DIR/logs/quality.log" 2>&1
    echo "$LOG_PREFIX Quality Agent finished"
  else
    echo "$LOG_PREFIX No draft with status=draft found — skipping quality chain"
  fi
fi
