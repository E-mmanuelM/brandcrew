#!/bin/bash
# BrandCrew — Content Editor (Quality Agent) Runner
# Runs after Writer Agent deposits a draft (auto-chained from writer/run.sh)
# On PASS: sends post text to Telegram for human approval. Image generates AFTER approval.
# On FAIL: sends back to Writer with feedback (up to 2 retries), then escalates.
# Usage: bash agents/quality/run.sh

set -euo pipefail

# Use PROJECT_DIR from .env or default
REPO_DIR="${PROJECT_DIR:-/projects/brandcrew}"
LOG_PREFIX="[quality $(date '+%Y-%m-%d %H:%M:%S')]"
LOCK_FILE="/tmp/BrandCrew-quality.lock"

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

echo "$LOG_PREFIX Starting Content Editor (Quality Agent)"

# ── Run Claude Code with the quality agent prompt ───────────────────────────────
cd "$REPO_DIR"

QUALITY_OUTPUT=$(claude -p "You are the Content Editor (Quality Agent). Read agents/quality/SKILL.md and execute the full process as defined. Follow every step exactly:

1. Load required files: rules/quality-standards.md, config/voice.md, rules/content-boundaries.md, agents/quality/references/scoring-rubric.md
2. Query Supabase content_drafts WHERE status = 'draft' ORDER BY created_at DESC LIMIT 1
3. If no draft with status 'draft' exists, log to agent_logs (agent_name: content_editor, action: quality_check, status: skipped, notes: no draft to score) and send Telegram message: 'No draft waiting for review.' Then stop.
4. Score the draft on 5 categories, each 0-10 with a one-line justification. Be honest, not generous:
   - Voice match: does this sound like the content owner — a real practitioner — or like AI?
   - Genuine usefulness: would someone in the target audience learn something actionable?
   - Specificity: real operational details, numbers, or examples — not vague generalities?
   - Hook quality: would someone in the target audience stop scrolling at line 1?
   - No slop markers: free of every banned phrase in rules/quality-standards.md?
5. Explicitly check every banned phrase in rules/quality-standards.md against the draft — check line by line, do not skim.
6. Run the boundary check from rules/content-boundaries.md — does the post target specific roles? If so, FAIL regardless of score.
7. Calculate total score.
8. If PASS (score >= 35 AND boundaries pass):
   - Update content_drafts status to 'passed'
   - Write the string QUALITY_PASS to /tmp/BrandCrew-quality-result.txt
   - Also write the draft ID to /tmp/BrandCrew-quality-draft-id.txt
   - Log to Supabase agent_logs (agent_name: content_editor, action: quality_check, status: completed, output_summary: score breakdown)
   - Send Telegram message to all approved users in this EXACT format:

✅ <b>POST READY FOR REVIEW</b>
Score: [X]/50

[Full post text]

---
Voice [X/10] | Useful [X/10] | Specific [X/10] | Hook [X/10] | Clean [X/10]

Reply APPROVE to generate image and queue for posting.
Reply REJECT to discard.
Or send edit notes to rewrite.

   - IMPORTANT: After sending the Telegram message, update the bot state file at \$REPO_DIR/logs/bot_state.json. Read the file, parse it as JSON, then for EACH user ID found in the APPROVED_TELEGRAM_IDS env variable, set their state to AWAITING_DRAFT_APPROVAL with context containing draft_id set to the draft's UUID. Write the updated JSON back. Use the dotenv library to read .env.

9. If FAIL (score < 35 OR boundaries fail):
   - Write the string QUALITY_FAIL to /tmp/BrandCrew-quality-result.txt
   - Check retry_count on the draft
   - If retry_count < 2: increment retry_count, add specific feedback to edit_notes (not vague — exact issues), update status to 'draft'. Send Telegram: 'Draft failed quality check (score X/50). Sending back to Writer with feedback.'
   - If retry_count >= 2: update status to 'failed'. Escalate to human via Telegram using the escalation format in SKILL.md. Do NOT attempt another rewrite.
10. Log to Supabase agent_logs (agent_name: content_editor, action: quality_check, status: completed, output_summary: score breakdown)

A score of 34 is a FAIL. Do not round up. When in doubt, FAIL.
Use .env for all credentials. Never log credentials." \
  --dangerously-skip-permissions \
  --max-turns 25 \
  --output-format text \
  2>&1)

EXIT_CODE=$?
echo "$QUALITY_OUTPUT"
echo "$LOG_PREFIX Finished with exit code $EXIT_CODE"

# ── On PASS: do NOT chain to image — wait for human approval via Telegram ─────
if [ -f "/tmp/BrandCrew-quality-result.txt" ]; then
  QUALITY_RESULT=$(cat /tmp/BrandCrew-quality-result.txt)
  rm -f "/tmp/BrandCrew-quality-result.txt"

  if [ "$QUALITY_RESULT" = "QUALITY_PASS" ]; then
    echo "$LOG_PREFIX Quality PASS — post text sent to Telegram for approval"
    echo "$LOG_PREFIX Image will generate AFTER human approves via Telegram"
    rm -f "/tmp/BrandCrew-quality-draft-id.txt"
  else
    echo "$LOG_PREFIX Quality FAIL — sent back to writer or escalated"
  fi
fi

if [ $EXIT_CODE -ne 0 ]; then
  echo "$LOG_PREFIX ERROR — Claude Code exited with code $EXIT_CODE"
fi
