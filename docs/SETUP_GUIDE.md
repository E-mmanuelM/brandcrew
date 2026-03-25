# Setup Guide — From Zero to First Post

This guide walks you through setting up BrandCrew from scratch. If you're using Claude Code, it will walk you through this interactively — just say "help me set this up."

Estimated time: 20-30 minutes for the core setup.

---

## What You Need Before Starting

- **An Anthropic API key** — sign up at console.anthropic.com
- **A Supabase account** — free tier at supabase.com
- **A Telegram account** — for the approval interface
- **A VPS** (recommended) or your own computer for local testing

You do NOT need Docker. The system runs directly on a VPS with Claude Code and cron jobs. No containers needed.

---

## Step 1: Get a Server

BrandCrew runs 24/7 so your agents fire on schedule even when your computer is off. A VPS costs $4-6/month.

**Recommended:** Hetzner CX22 (~€4-5/mo) — 2 vCPU, 4GB RAM, 40GB disk. Other options: DigitalOcean, Vultr, Linode, AWS Lightsail.

**When creating the server, select:**
- Ubuntu 22.04 LTS or Ubuntu 24.04 LTS
- Region closest to you or your audience
- SSH key authentication (add your public key during server creation — this is important)

**Connect to your server:**
```bash
ssh root@YOUR_SERVER_IP
```

**If you get "REMOTE HOST IDENTIFICATION HAS CHANGED" error:** This happens if you deleted and recreated a server with the same IP. Fix with: `ssh-keygen -R YOUR_SERVER_IP` then try again.

See the VPS Guide in CLAUDE.md for detailed instructions on connecting from Mac, Linux, or Windows.

**Want to test locally first?** Skip the VPS for now. You can run the bot on your own computer — agents just won't fire automatically when your computer is off.

---

## Step 2: Clone and Install

```bash
# On your VPS (as root — setup.sh needs root to install system packages)
cd /projects  # or wherever you prefer
git clone https://github.com/E-mmanuelM/brandcrew.git
cd brandcrew

# Run the setup script — installs everything:
# Node.js, Claude Code, Python, Playwright, creates brandcrew
bash scripts/setup.sh
```

The setup script handles ALL dependencies including git, Node.js, Python packages, Playwright browsers, and creates a dedicated `brandcrew` account. All agents must run as this user because Claude Code refuses `--dangerously-skip-permissions` as root.

**After setup.sh completes, switch to brandcrew:**
```bash
su - brandcrew
cd /projects/brandcrew
```

**Or SSH directly as brandcrew** (works if setup.sh copied your SSH keys):
```bash
ssh brandcrew@YOUR_SERVER_IP
cd /projects/brandcrew
```

**Stay as brandcrew for all remaining steps.** You only need root for the initial setup.sh.

---

## Step 3: Create Your Supabase Project

1. Go to supabase.com and create a free project
2. Once the project is ready, go to **Project Settings → API**
3. Copy the **Project URL** and the **service_role key** (not the anon key)
4. Go to **SQL Editor**, paste the contents of `supabase/schema.sql`, and click **Run**
5. Verify: check **Table Editor** — you should see tables: research_topics, content_ideas, content_drafts, agent_logs, repurposed_content

See `supabase/TABLES.md` for a plain-English guide to what each table does.

---

## Step 4: Create Your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts to name your bot
3. BotFather gives you a **bot token** — save this
4. To get your **user ID**: search for @userinfobot on Telegram, send `/start`, copy the number

---

## Step 5: Set Up Environment Variables

```bash
# Make sure you're logged in as brandcrew
cp .env.example .env
nano .env  # or vim, or use Claude Code to edit
```

Fill in:
- `ANTHROPIC_API_KEY` — from console.anthropic.com
- `SUPABASE_URL` — your project URL from Step 3
- `SUPABASE_SECRET_KEY` — the service_role key from Step 3
- `TELEGRAM_BOT_TOKEN` — from BotFather in Step 4
- `APPROVED_TELEGRAM_IDS` — your user ID from Step 4

Every variable has instructions in `.env.example` explaining where to get it.

**If the bot starts and shows errors about placeholder values:** the error message tells you exactly which values still need to be replaced.

---

## Step 6: Start the Telegram Bot

```bash
# As brandcrew:
cd /projects/brandcrew
nohup python3 telegram/bot.py >> logs/bot.log 2>&1 &
```

Now open Telegram and send `/start` to your bot. If it responds with the command list, your setup is working.

---

## Step 7: Install the Cron Schedule

```bash
# As brandcrew (the script will refuse to run as root):
cd /projects/brandcrew
bash scripts/cron-setup.sh
```

This installs the automated schedule:
- **Sunday 2:00pm UTC** — Research Agent scans for topics
- **Sunday 2:30pm UTC** — Marketing Director reviews strategy
- **Sunday 3:00pm UTC** — Content Strategist generates 10 ideas
- **Mon-Fri 10:00am UTC** — Writer drafts one post per day
- **Every 6 hours** — Health check
- **Every 4 days** — Snapshot (commits outputs to git)

Adjust times in `crontab -e` for your timezone. See `config/schedule.md`.

**If you get a permissions error:** Make sure you're running as `brandcrew`, not root. Check with `whoami`.

---

## Step 8: Verify Everything Works

```bash
bash scripts/health-check.sh
```

This checks that Claude Code is installed, required files exist, the bot is running, and the .env is configured.

Also send `/team_status` on Telegram — you should see the pipeline overview with all zeros (nothing has run yet).

**Test image rendering:**
```bash
python3 scripts/render_template.py --preview editorial_data_card
```
You should see a JPG generated in `generated_images/`. If this works, your image pipeline is ready.

---

## What Happens Next

Your system is now live with the default B2B SaaS example niche. It will work, but the content will be generic because it's not configured for YOUR industry yet.

**To make it yours, follow this order:**

1. **Define your niche** — edit `config/niche.md` (see docs/NICHE_CONFIG.md)
2. **Run the research team** — follow `agents/part-time/HOW_TO_RUN.md` to populate competitive intelligence
3. **Define your voice** — edit `config/voice.md` (Claude Code can interview you and fill this in)
4. **Define your audience** — edit `config/audience.md`
5. **Customize your brand** (optional) — edit `templates/themes/default.json`

Once personalized, the system runs on autopilot. Ideas arrive on Sunday, drafts arrive Monday-Friday, you approve on Telegram, post to LinkedIn manually.

---

## Quick Reference

| What you want to do | Where to go |
|---|---|
| Configure for your niche | docs/NICHE_CONFIG.md |
| Customize image templates | docs/TEMPLATE_GUIDE.md |
| Understand the system design | docs/ARCHITECTURE.md |
| Fix something that's broken | docs/FAQ.md |
| See the full command list | CLAUDE.md → Telegram Commands |
