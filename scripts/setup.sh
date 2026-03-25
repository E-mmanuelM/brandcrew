#!/bin/bash
# BrandCrew — VPS Initial Setup
# Run once on fresh Ubuntu 22.04+ as root
# Usage: bash scripts/setup.sh

set -e

echo "=== BrandCrew VPS Setup ==="

# ── System packages ────────────────────────────────────────────────────────────
apt-get update && apt-get upgrade -y

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "$TIMESTAMP - Installing pre-requisites"

# Install pre-requisites for Playwright (must come before pip install)
apt-get install -y python3 python3-pip curl gnupg apt-transport-https tmux git

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Install Python packages
pip install playwright Pillow python-dotenv supabase requests --break-system-packages

# Install Playwright system dependencies (as root — needs apt)
playwright install-deps

# ── Create non-root user for Claude Code ───────────────────────────────────────
# Claude Code refuses --dangerously-skip-permissions as root for security reasons.
# All agents run via Claude Code, so they MUST run as a non-root user.
if id "brandcrew" &>/dev/null; then
  echo "User 'brandcrew' already exists — skipping creation"
else
  echo "Creating non-root user 'brandcrew' for Claude Code agent execution..."
  useradd -m -s /bin/bash brandcrew
  echo "User 'brandcrew' created."
fi

# ── Set up project directory ───────────────────────────────────────────────────
PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/outputs"
mkdir -p "$PROJECT_DIR/generated_images"

# Give brandcrew ownership of the project
chown -R brandcrew:brandcrew "$PROJECT_DIR"
echo "Project directory ownership set to brandcrew."

# ── Fix git safe.directory for brandcrew ─────────────────────────────────────────
# Root clones the repo, but brandcrew needs to pull updates.
# Without this, git refuses to operate in a directory owned by a different user.
su - brandcrew -c "git config --global --add safe.directory '$PROJECT_DIR'"
echo "Git safe.directory configured for brandcrew."

# ── Install Playwright browsers for brandcrew ────────────────────────────────────
# Playwright browsers must be installed by the user who runs them.
# Root installed system deps above, but the browser binaries go in ~/.cache/
echo "Installing Playwright browsers for brandcrew..."
su - brandcrew -c "playwright install chromium"
echo "Playwright Chromium installed for brandcrew."

# ── Install Claude Code for brandcrew ────────────────────────────────────────────
# Use local npm prefix so brandcrew doesn't need root permissions.
# PATH is added to both .bashrc (interactive) and .profile (cron/non-interactive).
echo "Installing Claude Code for brandcrew..."
su - brandcrew -c "mkdir -p ~/.npm-global && npm config set prefix '~/.npm-global'"
su - brandcrew -c "npm install -g @anthropic-ai/claude-code"

# Add npm-global to PATH for interactive shells
su - brandcrew -c "grep -q 'npm-global/bin' ~/.bashrc || echo 'export PATH=~/.npm-global/bin:\$PATH' >> ~/.bashrc"
# Add npm-global to PATH for cron and non-interactive shells
su - brandcrew -c "grep -q 'npm-global/bin' ~/.profile || echo 'export PATH=~/.npm-global/bin:\$PATH' >> ~/.profile"

# Verify Claude Code installation
if su - brandcrew -c "~/.npm-global/bin/claude --version" &>/dev/null; then
  echo "Claude Code installed successfully: $(su - brandcrew -c '~/.npm-global/bin/claude --version')"
else
  echo "WARNING: Claude Code installation may have failed. Try running: su - brandcrew -c 'npm install -g @anthropic-ai/claude-code'"
fi

# ── Make scripts executable ────────────────────────────────────────────────────
chmod +x "$PROJECT_DIR"/agents/*/run.sh 2>/dev/null || true
chmod +x "$PROJECT_DIR"/scripts/*.sh 2>/dev/null || true
echo "Agent and script files set to executable."

# ── Copy SSH keys if running as root ───────────────────────────────────────────
if [ -f /root/.ssh/authorized_keys ]; then
  mkdir -p /home/brandcrew/.ssh
  cp /root/.ssh/authorized_keys /home/brandcrew/.ssh/authorized_keys
  chown -R brandcrew:brandcrew /home/brandcrew/.ssh
  chmod 700 /home/brandcrew/.ssh
  chmod 600 /home/brandcrew/.ssh/authorized_keys
  echo "SSH keys copied to brandcrew for remote access."
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "IMPORTANT: Claude Code agents must run as 'brandcrew', not root."
echo "Switch to brandcrew now:  su - brandcrew"
echo "Then cd to your project: cd $PROJECT_DIR"
echo ""
echo "Next steps (as brandcrew):"
echo "1. Authenticate Claude Code: claude  (follow the login prompts)"
echo "2. Copy .env.example to .env: cp .env.example .env"
echo "3. Fill in your API keys in .env: nano .env"
echo "4. Run the database schema in Supabase SQL Editor (supabase/schema.sql)"
echo "5. Start the Telegram bot: cd telegram && nohup python3 bot.py &"
echo "6. Install the cron schedule: bash scripts/cron-setup.sh"
echo ""
echo "Or tell Claude Code: 'Help me set up BrandCrew'"
