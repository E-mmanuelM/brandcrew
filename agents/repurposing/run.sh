#!/bin/bash
# BrandCrew — Content Repurposer Runner
# Transforms published LinkedIn posts into X threads, Substack drafts, TikTok slides
#
# Usage: bash agents/repurposing/run.sh [draft_id]
#   draft_id (optional) — specific draft to repurpose. If omitted, picks the latest published post.
#
# Trigger: manual via Telegram /repurpose command, or run after /get_post
# Not on cron by default — add to cron-setup.sh if you want automated repurposing

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
LOCK_FILE="/tmp/BrandCrew-repurposing.lock"
DRAFT_ID="${1:-}"

# Prevent overlapping runs
if [ -f "$LOCK_FILE" ]; then
  LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || stat -f %m "$LOCK_FILE" 2>/dev/null) ))
  if [ "$LOCK_AGE" -lt 3600 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') SKIPPED — lock file exists (age: ${LOCK_AGE}s)"
    exit 0
  fi
  echo "$(date '+%Y-%m-%d %H:%M:%S') Stale lock file (age: ${LOCK_AGE}s) — removing"
  rm -f "$LOCK_FILE"
fi

trap 'rm -f "$LOCK_FILE"' EXIT
touch "$LOCK_FILE"

echo "$(date '+%Y-%m-%d %H:%M:%S') Content Repurposer starting..."

if [ -n "$DRAFT_ID" ]; then
  PROMPT="Read agents/repurposing/SKILL.md. Repurpose the published LinkedIn post with draft_id=$DRAFT_ID into X/Twitter thread, Substack newsletter draft, and TikTok slide concept. Read the platform playbooks in rules/ before writing each version. Save all outputs to Supabase repurposed_content table. Send a Telegram summary when done."
else
  PROMPT="Read agents/repurposing/SKILL.md. Find the most recently published LinkedIn post (content_drafts where posted=true, ordered by updated_at desc, limit 1). Repurpose it into X/Twitter thread, Substack newsletter draft, and TikTok slide concept. Read the platform playbooks in rules/ before writing each version. Save all outputs to Supabase repurposed_content table. Send a Telegram summary when done."
fi

cd "$PROJECT_DIR"
claude -p "$PROMPT" \
  --allowedTools "Bash,Read,Write" \
  --dangerously-skip-permissions \
  --max-turns 25

echo "$(date '+%Y-%m-%d %H:%M:%S') Content Repurposer finished."
