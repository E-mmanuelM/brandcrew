# FAQ — Common Questions and Troubleshooting

---

## Setup Questions

### Do I need to be a developer to use this?
No. If you can follow step-by-step instructions and edit text files, you can set this up. Claude Code (the AI that runs inside the project) will walk you through everything interactively. Just open the project in Claude Code and say "help me set this up."

### Do I need Docker?
No. The system runs directly on a VPS with Claude Code, Python, and cron jobs. No containers needed.

### How much does it cost to run?
- **VPS:** $4-6/month (Hetzner, DigitalOcean, etc.)
- **Anthropic API:** varies by usage. The agents make ~10-15 API calls per day during the Mon-Fri cycle, plus ~20-30 on Sundays. Typical cost: $10-30/month depending on your plan.
- **Supabase:** free tier is enough for most users
- **Images:** $0 — HTML templates, no AI image API
- **Total:** roughly $15-35/month for a fully automated content team

### Can I run this on my own computer instead of a VPS?
Yes, for testing. But agents only run when your computer is on. For automated daily posting, you need a VPS that stays on 24/7.

### Does this work for any industry?
Yes. The system is niche-agnostic. All industry-specific content comes from `config/niche.md` which you fill in during setup. The pre-filled SaaS example is just a starting point.

### What is brandcrew and why do I need it?
Claude Code refuses to run with `--dangerously-skip-permissions` as root (this is a security restriction built into Claude Code). All agents use this flag when running on cron. The setup script (`scripts/setup.sh`) automatically creates a dedicated `brandcrew` account with everything it needs — Claude Code, Node.js, Python, Playwright browsers, project ownership. After running setup.sh as root, you switch to brandcrew (`su - brandcrew`) and do everything else from there. Only the initial setup.sh needs root.

### Can I SSH directly as brandcrew?
Yes. The setup script copies your root SSH keys to brandcrew. After setup, you can connect directly: `ssh brandcrew@YOUR_SERVER_IP`. This skips root entirely and lands you in the right user context.

---

## Content Questions

### How many posts does it produce per week?
By default: 10 ideas generated on Sunday, you pick 5, one post drafted per weekday (Mon-Fri). You can adjust the cadence in `config/schedule.md`.

### Will the content sound like AI wrote it?
The system has an anti-slop quality gate. The Editor agent scores every draft on a 50-point rubric and rejects anything that sounds generic or AI-generated. It checks for banned phrases, clichés, and empty language. The pass threshold is 35/50.

The biggest factor is `config/voice.md`. If your voice file is specific and detailed, the content sounds like you. If it's generic, the content will be too.

### Can I edit drafts before they post?
Yes. When a draft arrives on Telegram, you can reply with edit notes instead of APPROVE. The Writer rewrites it with your feedback. You can go back and forth as many times as you want.

### How does the system get better over time?
The Marketing Director agent runs weekly and reads real performance data (impressions, comments, reposts that you log via `/marketing_director`), your edit patterns, and which ideas you rejected. It updates the strategy for next week. The Writer and Strategist read this updated strategy, so content improves based on what actually worked.

### Can I use this for platforms other than LinkedIn?
Yes. LinkedIn is the primary pipeline (automated daily drafts). After posting to LinkedIn, use `/repurpose` on Telegram to create:
- X/Twitter thread (5-7 tweets)
- Substack newsletter draft (800-1500 words)
- TikTok slide concepts (image-based, no video)

Each platform version follows platform-specific best practices defined in `rules/x-playbook.md` and `rules/substack-playbook.md`.

---

## Troubleshooting

### "Claude Code won't run" / "--dangerously-skip-permissions" error
This is the most common issue. Claude Code refuses `--dangerously-skip-permissions` when run as root.

**Solution:** Switch to brandcrew (created by setup.sh):
```bash
su - brandcrew
cd /projects/brandcrew
```

**If cron jobs were installed as root:**
```bash
# Remove root's cron jobs
sudo crontab -r

# Switch to brandcrew and reinstall
su - brandcrew
cd /projects/brandcrew
bash scripts/cron-setup.sh
```

**Quick check:** Run `whoami` — it should show `brandcrew`, not `root`.

### "git pull" says "dubious ownership" or "detected dubious ownership"
This happens because root cloned the repo but brandcrew is trying to pull. The setup script fixes this automatically, but if you see it:
```bash
git config --global --add safe.directory /projects/brandcrew
```
Run this as whichever user is getting the error.

### Bot crashes with "invalid literal for int" on startup
Your `.env` file still has placeholder values. The bot now shows a friendly error message telling you exactly which values need to be replaced. Open `.env` with `nano .env` and replace the placeholder values with your real API keys and IDs.

### Agents run on cron but nothing happens (silent failures)
Most likely the agents are running as root. Cron jobs must be in brandcrew's crontab, not root's.

Check: `sudo crontab -l` (root's cron) vs `su - brandcrew -c 'crontab -l'` (brandcrew's cron).

If the cron entries are under root, move them:
```bash
sudo crontab -r
su - brandcrew
cd /projects/brandcrew
bash scripts/cron-setup.sh
```

### The bot doesn't respond to my messages
1. Check `APPROVED_TELEGRAM_IDS` in `.env` — your Telegram user ID must be listed
2. Check that bot.py is running: `pgrep -fa bot.py`
3. Check logs: `cat logs/bot.log | tail -50`
4. Restart the bot: `cd /projects/brandcrew && nohup python3 telegram/bot.py >> logs/bot.log 2>&1 &`

### Agents aren't running on schedule
1. Check cron is installed (as brandcrew): `crontab -l`
2. Check agent logs: `cat logs/research.log | tail -20` (or writer.log, etc.)
3. Check Claude Code is installed: `claude --version`
4. Re-install cron (as brandcrew): `bash scripts/cron-setup.sh`

### The Writer isn't producing drafts
1. Check that there are approved ideas: send `/team_status` on Telegram
2. If "Ideas approved (queue): 0" — no ideas are approved. Run `/ideate_now` or wait for Sunday.
3. Check writer logs: `cat logs/writer.log | tail -20`

### Images don't render or look broken
1. Check Playwright is installed: `playwright install chromium`
2. Check the theme file exists: `cat templates/themes/default.json`
3. Test manually: `python3 scripts/render_template.py --preview editorial_data_card`
4. Check designer logs: `cat logs/social_media_designer.log | tail -20`

### Content doesn't sound like me
1. Check `config/voice.md` — is it filled in with YOUR voice or still the SaaS default?
2. Let Claude interview you: open Claude Code, say "interview me and rewrite config/voice.md"
3. Give edit notes on drafts that don't sound right — the Marketing Director learns from your edits

### The Research Agent isn't finding good topics
1. Check `config/niche.md` — are keywords specific enough? "AI" is too broad. "AI-powered customer onboarding for fintech" is specific.
2. Make sure you have at least 8-10 keywords listed
3. Run the part-time research team first (see `agents/part-time/HOW_TO_RUN.md`)

### How do I check system health?
```bash
bash scripts/health-check.sh
```
This verifies Claude Code is installed, required files exist, the bot is running, and .env is configured.

### How do I see what's in the pipeline?
Send `/team_status` on Telegram. It shows counts for every stage: research topics, pending ideas, approved ideas, drafts in progress, posts ready, posts already published.

---

## Customization Questions

### How do I change posting frequency?
Edit `config/schedule.md` and re-run `bash scripts/cron-setup.sh` (as brandcrew). For example, to post 3 days a week instead of 5, change the cron to Mon/Wed/Fri.

### How do I add my own image template?
See `docs/TEMPLATE_GUIDE.md`. Create an HTML file in `templates/`, use CSS variables from the theme file, and update the Designer agent's SKILL.md.

### How do I change the brand colors?
Edit `templates/themes/default.json`. Change the color values and the next image will use your new colors.

### Can I run the agents manually instead of on cron?
Yes. Every agent has a Telegram command:
- `/research_now` — trigger research
- `/ideate_now` — generate ideas
- `/write_now` — draft a post
- `/quality_now` — score a draft
- `/repurpose` — repurpose to other platforms

### How do I contribute templates or improvements?
See `CONTRIBUTING.md`. Templates and niche configs are the easiest contributions.
