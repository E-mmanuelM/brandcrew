#!/bin/bash
# BrandCrew — Content Strategist (Ideation Agent) Runner
# Runs on the planning day defined in config/schedule.md, after Research Agent and Marketing Director
# Usage: bash agents/ideation/run.sh

set -euo pipefail

# Use PROJECT_DIR from .env or default
REPO_DIR="${PROJECT_DIR:-/projects/brandcrew}"
LOG_PREFIX="[ideation $(date '+%Y-%m-%d %H:%M:%S')]"
LOCK_FILE="/tmp/BrandCrew-ideation.lock"

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

echo "$LOG_PREFIX Starting Content Strategist (Ideation Agent)"

# ── Run Claude Code with the ideation agent prompt ────────────────────────────────
cd "$REPO_DIR"

claude -p "You are the Content Strategist (Ideation Agent). Read agents/ideation/SKILL.md and execute the full process as defined. Follow every step exactly:

1. Load required files: config/niche.md, rules/quality-standards.md, rules/content-boundaries.md, rules/linkedin-playbook.md
2. Load docs/cross-niche-formats.md (skip if first line says PLACEHOLDER)
3. Load docs/content-gaps.md (skip if first line says PLACEHOLDER)
4. Load performance-patterns.md (skip if first line says PLACEHOLDER)
5. Query Supabase research_topics WHERE used = false ORDER BY relevance_score DESC LIMIT 20
6. Query Supabase ip_library — scan for entries whose tags overlap with top research topics (max 5 entries). If table is empty or does not exist, note 'no IP yet' and continue.
7. Query Supabase content_drafts WHERE created_at > now() - 30 days — avoid repeating recent angles. Pay attention to the HOOKS specifically — if a draft used a similar hook or angle, do NOT generate an idea that would produce similar content.
8. Generate 10 DISTINCT content angles with relevance scores (1-10). Mix content types:
   - At least 3 Practical/How-to
   - At least 3 Opinion/Take
   - At least 2 Story/Case study
   - Remaining 2 any type
   Each idea should come from a DIFFERENT research topic where possible.
   Relevance score = how well this combines audience interest + the content owner's unique expertise.
9. For each idea write: relevance score, hook line, angle description, content type, suggested format (from linkedin-playbook.md benchmarks), IP connection
10. Save all 10 to Supabase content_ideas with status = 'pending'. For each idea, save:
    - research_topic_id = UUID of the research topic it was derived from
    - relevance_score = the 1-10 score
    - hook = the hook line
    - angle_description = the angle description
    - angle = the content type (practical/opinion/story)
    - suggested_format = format recommendation
11. AFTER saving all 10 ideas: UPDATE Supabase research_topics SET used = true WHERE id IN (the research_topic_ids you used). This prevents the same topics from appearing in the next run.
12. Send Telegram message using this EXACT format:

📋 Content ideas for this week (10 total):

1. {score} [Hook line]
→ [Angle description]
📌 Type: [type] | Format: [format]

2. {score} [Hook line]
→ [Angle description]
📌 Type: [type] | Format: [format]

(... all 10 ideas ...)

Reply with your picks (e.g. 1,3,5,7,9)
Reply NONE to reject all
Reply MORE for fresh ideas

13. CRITICAL — SET BOT STATE: After sending the Telegram message, update the bot state file so the bot knows to expect idea selection replies:
    - Read the 10 content_idea IDs you just saved to Supabase (the UUIDs from step 10)
    - Read APPROVED_TELEGRAM_IDS from .env (comma-separated list)
    - Write \$REPO_DIR/logs/bot_state.json with one entry per approved user ID:
      {
        \"USER_ID\": {
          \"state\": \"AWAITING_IDEA_SELECTION\",
          \"updated_at\": \"[current ISO timestamp]\",
          \"context\": {
            \"idea_ids\": [\"uuid-1\", \"uuid-2\", ..., \"uuid-10\"]
          }
        }
      }
    Replace USER_ID with the actual numeric IDs from APPROVED_TELEGRAM_IDS.
    Replace uuid values with the actual Supabase content_idea UUIDs.
14. Log to Supabase agent_logs (agent_name: content_strategist, action: weekly_ideation, status: completed)

Use .env for all credentials. Never log credentials. Ideas must be SPECIFIC — not generic topics." \
  --dangerously-skip-permissions \
  --max-turns 25 \
  --output-format text \
  2>&1

EXIT_CODE=$?

echo "$LOG_PREFIX Finished with exit code $EXIT_CODE"

if [ $EXIT_CODE -ne 0 ]; then
  echo "$LOG_PREFIX ERROR — Claude Code exited with code $EXIT_CODE"
fi
