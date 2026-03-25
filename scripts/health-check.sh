#!/bin/bash
# BrandCrew — Health Check — runs every 6 hours via cron

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
TS=$(date '+%Y-%m-%d %H:%M:%S')
ERRORS=0
WARNINGS=0

echo "[$TS] Health check starting..."

# Check claude is installed
command -v claude &> /dev/null && echo "[$TS] OK: claude installed" || { echo "[$TS] ERROR: claude not found — install with: npm install -g @anthropic-ai/claude-code"; ERRORS=$((ERRORS+1)); }

# Check CLAUDE.md exists
[ -f "$PROJECT_DIR/CLAUDE.md" ] && echo "[$TS] OK: CLAUDE.md exists" || { echo "[$TS] ERROR: CLAUDE.md missing"; ERRORS=$((ERRORS+1)); }

# Check .env exists
[ -f "$PROJECT_DIR/.env" ] && echo "[$TS] OK: .env exists" || { echo "[$TS] ERROR: .env missing — copy from .env.example: cp .env.example .env"; ERRORS=$((ERRORS+1)); }

# Check critical config files
[ -f "$PROJECT_DIR/config/niche.md" ] && echo "[$TS] OK: config/niche.md exists" || { echo "[$TS] ERROR: config/niche.md missing"; ERRORS=$((ERRORS+1)); }
[ -f "$PROJECT_DIR/config/voice.md" ] && echo "[$TS] OK: config/voice.md exists" || { echo "[$TS] ERROR: config/voice.md missing"; ERRORS=$((ERRORS+1)); }

# Check agent SKILL.md files
for agent in research ideation marketing_director writer quality social_media_designer repurposing; do
  [ -f "$PROJECT_DIR/agents/$agent/SKILL.md" ] || { echo "[$TS] ERROR: agents/$agent/SKILL.md missing"; ERRORS=$((ERRORS+1)); }
done

# Check templates
TEMPLATE_COUNT=$(ls -1 "$PROJECT_DIR/templates/"*.html 2>/dev/null | wc -l)
[ "$TEMPLATE_COUNT" -ge 6 ] && echo "[$TS] OK: $TEMPLATE_COUNT templates found" || { echo "[$TS] WARNING: only $TEMPLATE_COUNT templates found (expected 6)"; WARNINGS=$((WARNINGS+1)); }

# Check theme file
[ -f "$PROJECT_DIR/templates/themes/default.json" ] && echo "[$TS] OK: default theme exists" || { echo "[$TS] ERROR: templates/themes/default.json missing"; ERRORS=$((ERRORS+1)); }

# Check logs directory
[ -d "$PROJECT_DIR/logs" ] || { mkdir -p "$PROJECT_DIR/logs"; echo "[$TS] FIXED: logs dir created"; }

# Check generated_images directory
[ -d "$PROJECT_DIR/generated_images" ] || { mkdir -p "$PROJECT_DIR/generated_images"; echo "[$TS] FIXED: generated_images dir created"; }

# Check Telegram bot is running
if pgrep -fa bot.py > /dev/null 2>&1; then
  echo "[$TS] OK: bot.py is running"
else
  echo "[$TS] WARNING: bot.py is not running — start it with: cd telegram && nohup python3 bot.py >> logs/bot.log 2>&1 &"
  WARNINGS=$((WARNINGS+1))
fi

# Check Playwright is installed
if python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
  echo "[$TS] OK: Playwright installed"
else
  echo "[$TS] WARNING: Playwright not installed — images won't render. Run: pip install playwright && playwright install chromium"
  WARNINGS=$((WARNINGS+1))
fi

echo ""
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo "[$TS] Health check PASSED — all clear"
elif [ $ERRORS -eq 0 ]; then
  echo "[$TS] Health check PASSED with $WARNINGS warning(s)"
else
  echo "[$TS] Health check FAILED — $ERRORS error(s), $WARNINGS warning(s)"
fi
