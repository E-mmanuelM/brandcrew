#!/bin/bash
# snapshot.sh — Commits VPS outputs to GitHub every 3-5 days
# Cron: 0 6 */4 * * cd $PROJECT_DIR && bash scripts/snapshot.sh >> logs/snapshot.log 2>&1

set -e

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
LOG_PREFIX="[snapshot.sh $(date '+%Y-%m-%d %H:%M:%S')]"

echo "$LOG_PREFIX Starting output snapshot"

cd "$PROJECT_DIR"

# Check if there's anything new in outputs/
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard outputs/)" ]; then
  echo "$LOG_PREFIX No changes in outputs/ — skipping commit"
  exit 0
fi

# Stage only the outputs directory
git add outputs/

CHANGED=$(git diff --cached --name-only | wc -l)
echo "$LOG_PREFIX Staging $CHANGED file(s) from outputs/"

git commit -m "chore: snapshot VPS outputs $(date '+%Y-%m-%d')"

git push origin main

echo "$LOG_PREFIX Snapshot pushed to GitHub"
