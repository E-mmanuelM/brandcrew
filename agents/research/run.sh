#!/bin/bash
# BrandCrew — Niche Content Researcher Runner
# Runs weekly on the planning day defined in config/schedule.md
# Usage: bash agents/research/run.sh

set -euo pipefail

# Use PROJECT_DIR from .env or default
REPO_DIR="${PROJECT_DIR:-/projects/brandcrew}"
LOG_PREFIX="[research $(date '+%Y-%m-%d %H:%M:%S')]"
LOCK_FILE="/tmp/BrandCrew-research.lock"

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

echo "$LOG_PREFIX Starting Niche Content Researcher"

# ── Run Claude Code with the research agent prompt ────────────────────────────────────
cd "$REPO_DIR"

claude -p "You are the Niche Content Researcher. Read agents/research/SKILL.md and execute the full research process as defined. Follow every step exactly:

1. Load required files: config/niche.md, agents/research/references/niche-keywords.md
2. Load config/watchlist.md (skip if first line says PLACEHOLDER or template is blank)
3. Load performance-patterns.md (skip if first line says PLACEHOLDER)
4. Query Supabase research_topics WHERE used = false — do not duplicate existing topics
5. Query Supabase content_drafts WHERE status = 'published' AND created_at > now() - 30 days — avoid recent angles
6. Search for high-engagement content from the past 7 days that passes the Topic Acceptance Filter in SKILL.md
7. Apply the Automatic Reject filter — remove anything that fails
8. Score surviving topics 1-10 for relevance
9. Save top 5-10 topics to Supabase research_topics table
10. Log completion to Supabase agent_logs (agent_name: niche_content_researcher, action: weekly_research_scan, status: completed)
11. Send Telegram notification with topic summary

Use .env for all credentials. Never log credentials. Output compact topics only — no working notes." \
  --dangerously-skip-permissions \
  --max-turns 25 \
  --output-format text \
  2>&1

EXIT_CODE=$?

echo "$LOG_PREFIX Finished with exit code $EXIT_CODE"

if [ $EXIT_CODE -ne 0 ]; then
  echo "$LOG_PREFIX ERROR — Claude Code exited with code $EXIT_CODE"
fi
