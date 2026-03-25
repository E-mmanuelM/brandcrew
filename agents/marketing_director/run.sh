#!/bin/bash
# BrandCrew — Marketing Director Runner
# Runs on the planning day AFTER Research Agent, BEFORE Content Strategist
# Usage: bash agents/marketing_director/run.sh

set -euo pipefail

# Use PROJECT_DIR from .env or default
REPO_DIR="${PROJECT_DIR:-/projects/brandcrew}"
LOG_PREFIX="[marketing_director $(date '+%Y-%m-%d %H:%M:%S')]"
LOCK_FILE="/tmp/BrandCrew-marketing-director.lock"

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

echo "$LOG_PREFIX Starting Marketing Director"

# ── Run Claude Code with the marketing director prompt ───────────────────────────
cd "$REPO_DIR"

claude -p "You are the Marketing Director. Read agents/marketing_director/SKILL.md and execute the full process as defined. Follow every step exactly:

1. Load ALL reference files listed in SKILL.md:
   - performance-patterns.md (you wrote this — you're updating it)
   - docs/content-gaps.md (competitive white space — populated by part-time research agents)
   - docs/cross-niche-formats.md (formats from other industries — populated by part-time research agents)
   - config/niche.md
   - rules/content-boundaries.md
   - rules/linkedin-playbook.md
   - rules/brand-guidelines.md (image style direction — you may update this based on image feedback)
   For any file that is empty or has only placeholder content, skip it and note that it needs populating.

2. Query Supabase for ALL of these:
   - research_topics WHERE created_at > now() - 7 days (this week's fresh research)
   - content_drafts WHERE created_at > now() - 30 days (recent drafts — check quality_score, status, edit_notes, angle/content_type)
   - content_ideas WHERE created_at > now() - 30 days (what was generated, selected, rejected)
   - agent_logs WHERE agent_name = 'marketing_director' AND action = 'operator_feedback' (your Telegram inbox — includes both strategic notes AND post performance data like impressions, likes, comments, reposts)
   - agent_logs WHERE action = 'idea_adjustment' (operator rejected/adjusted ideas)
   - agent_logs WHERE action = 'edit_requested' (operator edit notes on drafts)
   - agent_logs WHERE action IN ('image_feedback', 'image_quality_feedback') (operator image preferences — both /regenerate_image and /image_feedback logs)
   - agent_logs WHERE status = 'failed' AND created_at > now() - 7 days (what broke)
   - agent_logs WHERE agent_name = 'social_media_analyst' ORDER BY completed_at DESC LIMIT 1 (latest analytics if any)

3. Analyze post performance data:
   - The operator logs LinkedIn performance via /marketing_director command
   - Parse these messages and extract metrics per post
   - Cross-reference with content_drafts and content_ideas to connect performance back to idea type, hook style, and topic
   - Build a performance picture: which content types, topics, and hook styles perform best?
   - If no performance data exists yet, note this and rely on operator feedback + content mix analysis

4. Analyze content mix over last 4 weeks:
   - Count Opinion/Take vs Practical/How-to vs Story/Case study
   - Flag imbalance if any type is over 50%
   - Check which formats from docs/cross-niche-formats.md have NOT been tried yet
   - Pay special attention to whether tutorial/how-to content is being generated — if not, this must be corrected

5. Analyze operator feedback patterns:
   - What did they reject? What did they edit? What direction did they give via /marketing_director?
   - Look for PATTERNS across multiple pieces of feedback

6. Analyze image feedback patterns:
   - Read ALL image_feedback and image_quality_feedback entries
   - What visual direction is the operator consistently asking for?
   - Common themes: metaphor quality, depth, text readability, composition
   - If you see clear patterns (e.g. same feedback appearing 3+ times), update rules/brand-guidelines.md with a note in the relevant section
   - If no clear pattern yet, just note the feedback in performance-patterns.md for tracking

7. Analyze agent performance and research signal:
   - Quality check failures — what common reasons?
   - Writer issues — recurring weaknesses?
   - Image generation issues — prompt quality, rendering failures?

8. Update performance-patterns.md with specific direction for this week:
   - Post performance summary with specific numbers if available
   - Content type to prioritize (be specific: 'this week MUST include a how-to')
   - Format to try from cross-niche research
   - What to stop doing
   - Operator preferences synthesized
   - Agent performance notes (if the writer keeps failing on hooks, note it)
   - Image direction summary (what visual patterns the operator wants)
   - PRESERVE the file's section structure — update within sections

9. Update docs/content-gaps.md ONLY if gaps have meaningfully changed. Most weeks, skip this.

10. Log to agent_logs (agent_name: marketing_director, action: weekly_synthesis, status: completed)

11. Send Telegram summary message with this week's direction including post performance data and image quality section.

Use .env for all credentials. Never log credentials." \
  --dangerously-skip-permissions \
  --max-turns 30 \
  --output-format text \
  2>&1

EXIT_CODE=$?

echo "$LOG_PREFIX Finished with exit code $EXIT_CODE"

if [ $EXIT_CODE -ne 0 ]; then
  echo "$LOG_PREFIX ERROR — Claude Code exited with code $EXIT_CODE"
fi
