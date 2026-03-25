#!/bin/bash
# BrandCrew — Install Cron Jobs
# Run after confirming agents work manually first
# IMPORTANT: Run this as brandcrew, NOT as root
#
# Schedule overview (all times UTC — adjust for your timezone in config/schedule.md):
#   Sunday:   Research → Marketing Director → Content Strategist (within 1 hour)
#   Mon-Fri:  Writer → Editor auto-chain (one post per day)
#   Every 4d: Snapshot (commit outputs to GitHub)
#   Every 6h: Health check

set -e

# ── Root check — refuse to run as root ────────────────────────────────────────
if [ "$(id -u)" -eq 0 ]; then
  echo ""
  echo "================================================================"
  echo "  ERROR: Do not run cron-setup.sh as root!"
  echo "================================================================"
  echo ""
  echo "  Claude Code refuses --dangerously-skip-permissions as root."
  echo "  All agents use this flag. Running cron as root = silent failures."
  echo ""
  echo "  The setup script (scripts/setup.sh) created an 'brandcrew' account."
  echo "  Switch to it and re-run:"
  echo ""
  echo "    su - brandcrew"
  echo "    cd /projects/brandcrew"
  echo "    bash scripts/cron-setup.sh"
  echo ""
  echo "================================================================"
  echo ""
  exit 1
fi

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"

echo "=== Installing Cron Jobs ==="
echo "Project directory: $PROJECT_DIR"
echo "Running as user: $(whoami)"

crontab -l 2>/dev/null > /tmp/current_cron || true

cat >> /tmp/current_cron << EOF

# BrandCrew — Content Pipeline
# ========================================

# SUNDAY — Research + Ideation (fire within 1 hour)
# Research Agent — Sunday 2:00pm UTC
0 14 * * 0 cd $PROJECT_DIR && bash agents/research/run.sh >> logs/research.log 2>&1

# Marketing Director — Sunday 2:30pm UTC
30 14 * * 0 cd $PROJECT_DIR && bash agents/marketing_director/run.sh >> logs/marketing_director.log 2>&1

# Content Strategist — Sunday 3:00pm UTC
0 15 * * 0 cd $PROJECT_DIR && bash agents/ideation/run.sh >> logs/ideation.log 2>&1

# MONDAY-FRIDAY — Daily post (Writer auto-chains to Editor)
# Writer + Editor — Mon-Fri 10:00am UTC
0 10 * * 1-5 cd $PROJECT_DIR && bash agents/writer/run.sh >> logs/writer.log 2>&1

# MAINTENANCE
# Snapshot — commit VPS outputs to GitHub every 4 days at 6am UTC
0 6 */4 * * cd $PROJECT_DIR && bash scripts/snapshot.sh >> logs/snapshot.log 2>&1

# Health check — every 6 hours
0 */6 * * * cd $PROJECT_DIR && bash scripts/health-check.sh >> logs/health.log 2>&1
EOF

crontab /tmp/current_cron
rm /tmp/current_cron

echo "=== Done ==="
echo ""
echo "Installed cron schedule:"
crontab -l | grep -v '^#' | grep -v '^$'
echo ""
echo "Adjust times in crontab -e if your timezone differs."
echo "See config/schedule.md for the posting schedule."
