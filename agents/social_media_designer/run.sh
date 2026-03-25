#!/bin/bash
# BrandCrew — Social Media Designer Agent Runner
# Triggered by: bot.py after human APPROVE on text
# Job: Read the approved draft, pick template, fill variables, render image, send to Telegram.
# Usage: bash agents/social_media_designer/run.sh [draft_id]

set -euo pipefail

# Use PROJECT_DIR from .env or default
REPO_DIR="${PROJECT_DIR:-/projects/brandcrew}"
LOG_PREFIX="[social_media_designer $(date '+%Y-%m-%d %H:%M:%S')]"
LOCK_FILE="/tmp/BrandCrew-social-media-designer.lock"
FEEDBACK_FILE="/tmp/BrandCrew-image-feedback.txt"
STATE_FILE="$REPO_DIR/logs/bot_state.json"

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

# ── Ensure directories exist ───────────────────────────────────────────────────────
mkdir -p "$REPO_DIR/logs"
mkdir -p "$REPO_DIR/generated_images"

DRAFT_ID="${1:-}"
echo "$LOG_PREFIX Starting Social Media Designer Agent${DRAFT_ID:+ (draft: $DRAFT_ID)}"

# ── Build the draft query instruction ─────────────────────────────────────────
if [ -n "$DRAFT_ID" ]; then
  DRAFT_QUERY="2. Query Supabase content_drafts WHERE id = '$DRAFT_ID' LIMIT 1."
else
  DRAFT_QUERY="2. Query Supabase content_drafts WHERE status = 'approved' AND (template_name IS NULL OR template_name = '') ORDER BY created_at ASC LIMIT 1."
fi

# ── Check for user feedback (from /regenerate_image command) ──────────────────
FEEDBACK_INSTRUCTION=""
if [ -f "$FEEDBACK_FILE" ]; then
  USER_FEEDBACK=$(cat "$FEEDBACK_FILE")
  rm -f "$FEEDBACK_FILE"
  echo "$LOG_PREFIX Found user feedback for regeneration: $USER_FEEDBACK"
  FEEDBACK_INSTRUCTION="

CRITICAL — REGENERATION WITH USER FEEDBACK:
The user has requested a regeneration with this specific feedback:
\"$USER_FEEDBACK\"

This means:
- Read the draft's EXISTING template_name and template_vars from Supabase.
- Apply the user's feedback PRECISELY. Change ONLY the parts the user mentioned.
- If the user says 'make the headline bigger' — that's a template issue, note it but keep the current template.
- If the user says 'change the headline' — rewrite only the headline in template_vars.
- If the user says 'use a different template' — pick a new template_name.
- After applying changes, re-run render_template.py."
else
  echo "$LOG_PREFIX No feedback file found — fresh design."
fi

# ── Run Claude Code to design the image ───────────────────────────────────────
cd "$REPO_DIR"

DESIGN_OUTPUT=$(claude -p "You are the Social Media Designer Agent. Read agents/social_media_designer/SKILL.md and execute the full process as defined. Follow every step exactly:

1. Load and read rules/brand-guidelines.md, rules/content-boundaries.md, and performance-patterns.md.
$DRAFT_QUERY
3. If no draft found:
   - Log to agent_logs (agent_name: social_media_designer, action: design_image, status: skipped, notes: no approved draft found)
   - Send Telegram message: 'Social Media Designer: no approved draft found to design image for.'
   - Stop.
4. Read the full draft_text of the draft.
5. Follow the 5-step design process from SKILL.md exactly:
   - Step 1: Read the post deeply — identify type, tension, key data
   - Step 2: Pick the best template
   - Step 3: Write a scroll-stopping headline (MUST pass boundaries check)
   - Step 4: Fill ALL template variables as JSON
   - Step 5: Save to Supabase and render
6. UPDATE content_drafts SET template_name = '[your chosen template]', template_vars = '[your JSON]'::jsonb WHERE id = '[draft_id]'
7. Run: python3 scripts/render_template.py --draft-id [draft_id]
8. Verify the image was created — check that image_url is now set in content_drafts for this draft.
9. Log to agent_logs (agent_name: social_media_designer, action: design_image, status: completed, output_summary: template used + first 100 chars of headline)
$FEEDBACK_INSTRUCTION
Output the template_name and headline you chose, nothing else." \
  --dangerously-skip-permissions \
  --max-turns 25 \
  --output-format text \
  2>&1)

EXIT_CODE=$?
echo "$DESIGN_OUTPUT"
echo "$LOG_PREFIX Claude Code finished with exit code $EXIT_CODE"

# ── Check if image was generated and send to Telegram ─────────────────────
if [ $EXIT_CODE -eq 0 ]; then
  # Get the image path from Supabase
  IMAGE_CHECK=$(claude -p "Query Supabase content_drafts WHERE id = '${DRAFT_ID:-}' and return ONLY the image_url value. If no draft_id was provided, query WHERE status = 'approved' ORDER BY updated_at DESC LIMIT 1 and return its image_url. Output ONLY the file path, nothing else." \
    --dangerously-skip-permissions \
    --max-turns 5 \
    --output-format text \
    2>&1)

  IMAGE_PATH=$(echo "$IMAGE_CHECK" | grep -oP "$REPO_DIR/generated_images/[^\\s]+" | head -1)

  if [ -n "$IMAGE_PATH" ] && [ -f "$IMAGE_PATH" ]; then
    echo "$LOG_PREFIX Image saved to: $IMAGE_PATH"

    # Send to Telegram and set AWAITING_IMAGE_APPROVAL state
    claude -p "You are the Social Media Designer Agent completing the final delivery step.

1. Query Supabase content_drafts WHERE image_url = '$IMAGE_PATH' LIMIT 1. Get the draft_id and draft_text.
2. Do NOT change the draft status — it is already 'approved' from the bot.py APPROVE flow.
3. CRITICAL — SET BOT STATE: Read the file $STATE_FILE. Update the JSON so that ALL user entries have state='AWAITING_IMAGE_APPROVAL' and context={'draft_id': '[that draft id]'}. Write the updated JSON back to $STATE_FILE.
4. Send a Telegram message to all approved users in this EXACT format:

🖼 <b>Image ready — review it below</b>

Reply APPROVE to finalize this post for LinkedIn.
Reply with edit notes to regenerate with changes.
Or use /regenerate_image [feedback] for specific fixes.

5. Then call the Telegram sendPhoto API directly to send the image file at $IMAGE_PATH to all approved users. Use the draft_text (first 200 chars) as the photo caption.
6. Do NOT update the draft status to finalized — that only happens when the human replies APPROVE.

Use .env for all credentials. Never log credentials." \
      --dangerously-skip-permissions \
      --max-turns 15 \
      --output-format text \
      >> "$REPO_DIR/logs/social_media_designer.log" 2>&1

    echo "$LOG_PREFIX Image pipeline complete — delivered to Telegram, AWAITING_IMAGE_APPROVAL state set"

  else
    echo "$LOG_PREFIX WARNING — no image file found after rendering."
    echo "$LOG_PREFIX Image check output: $IMAGE_CHECK"

    claude -p "Send a Telegram message to all approved users:

⚠️ <b>Image rendering failed</b>

The post text is approved but the image could not be rendered.
Try /regenerate_image [feedback] to retry.

Log this to agent_logs: agent_name=social_media_designer, action=render_image, status=failed, notes=no image file found after render_template.py.

Use .env for all credentials." \
      --dangerously-skip-permissions \
      --max-turns 10 \
      --output-format text \
      >> "$REPO_DIR/logs/social_media_designer.log" 2>&1
  fi
else
  echo "$LOG_PREFIX ERROR — Claude Code exited with code $EXIT_CODE"
fi
