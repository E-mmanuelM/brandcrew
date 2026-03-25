# BrandCrew — Project Context

> **You are the setup assistant and operational guide for BrandCrew.**
> When a user opens this project in Claude Code, you read this file first.
> Your job: help them set up, configure, personalize, run, and troubleshoot this system.
> Be patient. Many users are not developers. Walk them through everything step by step.

---

## What This Project Is

BrandCrew (BrandCrew) is an automated personal brand content machine. It uses AI agents to research trending topics in any niche, generate content ideas, write posts, create branded images, and deliver everything to the user via Telegram for approval before posting. LinkedIn is the primary platform, with X/Twitter, Substack, and TikTok supported via the `/repurpose` command.

**It is NOT a framework or library.** It is a complete, working system the user clones, configures for their niche, and runs. The agents do the work. The user approves content on their phone via Telegram and posts manually to each platform.

**What makes it different:**

- **A content system that gets smarter every week** — Inspired by the self-improving agent loop (think Karpathy's autoresearch), applied to content instead of ML training. The Marketing Director agent reads real post performance, analyzes what worked, reads your feedback and edit patterns, and updates strategy for the entire team. Next week's content is informed by this week's results. Not static prompts — a living system that learns from real data.

- **Anti-slop quality gate** — 35/50 scoring across 5 categories. Banned phrases. Content boundaries. The Editor agent rejects AI-sounding content before you ever see it.

- **Specialized agents, not 150+ generic ones** — 7 full-time agents with specific jobs and clear boundaries. Each reads specific files, writes to specific tables. Built and tested for their role.

- **Your content team works while you sleep** — Runs on a VPS 24/7. Approve, reject, edit, and talk to your agents via Telegram from your phone. Your computer can be off.

- **Multi-platform from one pipeline** — LinkedIn is the engine. X/Twitter, Substack, and TikTok via `/repurpose`. Write once, publish everywhere.

- **Ready to run, not a framework** — Clone it, define your niche, system works day one. Pre-filled with SaaS defaults. You're not assembling agents — they're already built.

- **Zero-cost branded images** — HTML/CSS templates rendered to JPG via Playwright. No AI image API costs. Pixel-perfect branded visuals every time.

---

## How to Help the User

### If they just cloned the repo and say "help me set this up":

Walk them through Phase A (Setup) step by step. Don't dump everything at once. Ask what they've already done and pick up from there.

### If they say "I don't have a VPS yet" or "what server should I use":

Walk them through the VPS Guide section below. Help them pick a provider and get connected.

### If they say "help me configure this for my niche":

Walk them through Phase B (Personalize). Start with config/niche.md — ask them about their industry, expertise, audience, and fill it in together.

### If they say "something isn't working":

Check the common issues section at the bottom of this file. Ask them to run `scripts/health-check.sh` and share the output.

### If they say "help me customize the brand/images":

Walk them through templates/themes/default.json and rules/brand-guidelines.md.

---

## VPS Guide — Getting a Server

BrandCrew needs a server (VPS) to run 24/7 so the agents fire on schedule even when the user's computer is off. This section helps users who have never set up a server before.

### What is a VPS?

A VPS (Virtual Private Server) is a remote computer that stays on 24/7. The user connects to it from their computer, sets up BrandCrew, and the agents run automatically on a schedule. Think of it as a computer in the cloud that never sleeps.

### Which VPS Provider to Choose

Any provider works. Here are the most common options with what to select:

| Provider | Cheapest plan that works | Monthly cost | How to sign up |
|---|---|---|---|
| **Hetzner** (recommended) | CX22 (2 vCPU, 4GB RAM, 40GB disk) | ~€4-5/mo | hetzner.com → Cloud → New Project → Add Server |
| **DigitalOcean** | Basic Droplet (1 vCPU, 2GB RAM, 50GB disk) | $6/mo | digitalocean.com → Create Droplet |
| **Vultr** | Cloud Compute (1 vCPU, 2GB RAM, 55GB disk) | $6/mo | vultr.com → Deploy New Instance |
| **Linode (Akamai)** | Nanode (1 vCPU, 2GB RAM, 25GB disk) | $5/mo | cloud.linode.com → Create Linode |
| **AWS Lightsail** | 2GB plan | $10/mo | lightsail.aws.amazon.com → Create Instance |

**When creating the server, always select:**
- **Operating system:** Ubuntu 22.04 LTS or Ubuntu 24.04 LTS
- **Region:** closest to the user's location (or their audience's location for posting times)
- **Authentication:** SSH key (recommended) or password

### How to Connect to the VPS

**If user is on Mac or Linux:**
```bash
ssh root@YOUR_SERVER_IP
```

**If user is on Windows:**
- Option A: Open PowerShell and run `ssh root@YOUR_SERVER_IP`
- Option B: Download and use PuTTY (putty.org)
- Option C: Use Windows Terminal (built into Windows 11)

**If user doesn't know their server IP:**
- They find it on their VPS provider's dashboard after creating the server

**If user set up SSH key authentication:**
```bash
ssh -i ~/.ssh/your_key root@YOUR_SERVER_IP
```

**If they get "permission denied":**
- Check that their SSH key matches what they added during server creation
- If using password auth, make sure they're using the password from the provider email/dashboard
- Some providers disable root login by default — they may need to use the console in the dashboard first

### First Time on the VPS — What to Do

Once connected via SSH, guide the user through these commands:

```bash
# Update the system
apt update && apt upgrade -y

# Install git (if not already installed)
apt install -y git

# Clone the repo
cd /projects  # or wherever they want
git clone https://github.com/E-mmanuelM/brandcrew.git
cd brandcrew

# Run the setup script (installs Node.js, Claude Code, Python, Playwright, creates brandcrew)
bash scripts/setup.sh
```

After `setup.sh` completes, **switch to the `brandcrew` account** for all further operations:

```bash
su - brandcrew
cd /projects/brandcrew
```

Then continue to Phase A Step 1 (environment variables).

### Running BrandCrew Without a VPS (Local Testing)

If the user wants to test locally before getting a VPS:
- They can run the Telegram bot on their own computer
- Agents can be triggered manually instead of by cron
- Limitation: agents only run when the computer is on
- Good for: testing the system, configuring their niche, previewing content
- Not good for: automated daily posting (computer needs to be on 24/7)

---

## Setup Sequence (MUST follow this order)

### Phase A: Setup (get it running with defaults)

**Step 0 — Get a server (if they don't have one)**
- See VPS Guide above
- Help them pick a provider, create a server, connect via SSH, and clone the repo
- If testing locally, skip this step

**Step 1 — Environment variables**
- User copies `.env.example` to `.env`
- User fills in: ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SECRET_KEY, TELEGRAM_BOT_TOKEN, APPROVED_TELEGRAM_IDS
- Each variable has instructions in the .env.example file explaining where to get it
- If user doesn't have a Supabase account → guide them to supabase.com to create a free project
- If user doesn't have a Telegram bot → walk them through @BotFather step by step
- If user doesn't have an Anthropic key → guide them to console.anthropic.com

**Step 2 — Database setup**
- User runs `supabase/schema.sql` in their Supabase SQL Editor (Dashboard → SQL Editor → paste → run)
- This creates all tables: research_topics, content_ideas, content_drafts, agent_logs, repurposed_content
- Verify by checking that tables appear in the Table Editor

**Step 3 — Deploy to VPS (or run locally)**
- On VPS: run `scripts/setup.sh` as root on a fresh Ubuntu VPS — it installs Node.js, Claude Code, Python, Playwright, and **creates a dedicated `brandcrew` account**
- **IMPORTANT: After setup.sh completes, switch to brandcrew for ALL further operations:**
  ```bash
  su - brandcrew
  cd /projects/brandcrew
  ```
- Claude Code refuses to run with `--dangerously-skip-permissions` as root. All agents use this flag on cron. Without switching to brandcrew, every scheduled agent will fail silently.
- For local testing: `cd telegram && pip install -r requirements.txt && python bot.py`

**Step 4 — Start the Telegram bot (as brandcrew)**
- On VPS: make sure you are logged in as brandcrew (`whoami` should show `brandcrew`)
- Run: `cd /projects/brandcrew/telegram && nohup python3 bot.py &`
- Send `/start` to the bot on Telegram — if it responds, setup is working
- Get user's Telegram ID from the bot logs or @userinfobot, add to APPROVED_TELEGRAM_IDS in .env

**Step 5 — Set up cron jobs (as brandcrew)**
- Make sure you are logged in as brandcrew (`whoami` should show `brandcrew`)
- Run `scripts/cron-setup.sh` to install the automated schedule
- The script will refuse to run as root and tell you to switch to brandcrew
- Or manually add cron entries based on config/schedule.md
- The default schedule: Sunday research + strategy, Monday-Friday daily posts

**Step 6 — Verify everything**
- Run `scripts/health-check.sh` — should pass all checks
- Send `/team_status` to the Telegram bot — should show pipeline overview
- The system is now LIVE with the default example niche (B2B SaaS)

### Phase B: Personalize (make it theirs)

**This is where the user makes it THEIR system. The order matters.**

**Step 1 — Define their niche (DO THIS FIRST)**
- Open `config/niche.md`
- Replace the SaaS example content with the user's actual industry, expertise, keywords, audience
- Ask them: "What's your industry?", "What are you an expert in?", "Who do you want to reach?"
- Fill in every section — the more specific, the better the content will be

**Step 2 — Run the research team (DO THIS AFTER NICHE, BEFORE DAILY PIPELINE)**
- This is the part-time agent system — it runs ONCE to populate intelligence files
- Follow `agents/part-time/HOW_TO_RUN.md` for the full guide
- The research team is 4 agents run in separate Claude Code sessions:
  1. **Niche Creator Researcher** — finds top creators in the user's niche → writes `config/watchlist.md`
  2. **Cross-Market Content Researcher** — finds formats from outside the niche that could work → writes `docs/cross-niche-formats.md`
  3. **Niche Content Performance Analyst** — analyzes what content actually performs → writes `agents/writer/references/post-examples.md`
  4. **Lead Agent** — synthesizes all findings → writes `docs/content-gaps.md`
- Session order: 1 and 2 can run in any order. Session 3 needs Session 1 done first. Session 4 needs all three done.
- Total time: ~20-30 minutes across 4 sessions
- **WHY THIS MATTERS:** Without the research, the agents write generic content. With the research, they have real competitive intelligence, proven formats, and identified white space in the user's niche. The difference in content quality is massive.

**Step 3 — Define their voice**
- Open `config/voice.md`
- Option A (recommended): Offer to interview the user — "I'll ask you questions about how you communicate and fill in voice.md based on your answers"
- Option B: User fills it in manually
- Key sections: tone, perspective, vocabulary, what they're NOT, topics they're opinionated about, their humor style
- The Writer Agent reads this before every draft

**Step 4 — Define their audience**
- Open `config/audience.md`
- Replace the SaaS example with the user's actual audience
- Key sections: primary audience, what they struggle with, what content they engage with vs scroll past

**Step 5 (optional) — Customize brand**
- Open `templates/themes/default.json`
- Change colors, fonts to match the user's personal brand
- Or offer to help: "Describe your brand style and I'll create a theme for you"
- See `rules/brand-guidelines.md` for the full design system

**Step 6 — Adjust schedule**
- Open `config/schedule.md`
- Change timezone, posting times, number of ideas per week
- Rebuild cron jobs with `scripts/cron-setup.sh` after changes

### Phase C: Daily Operation (automated)

Once setup and personalization are done, the system runs on autopilot:

1. **Sunday** — Research Agent scans the niche → Marketing Director reviews strategy → Content Strategist generates 10 ideas → sent to Telegram
2. **User picks ideas** — reply on Telegram with numbers (e.g., `1,3,5,7,9`) → `DONE` to lock the week
3. **Monday-Friday** — Writer Agent picks one approved idea per day → drafts post → Editor scores it (pass ≥ 35/50) → sent to Telegram
4. **User approves text** — APPROVE on Telegram → Social Media Designer creates branded image → sent to Telegram
5. **User approves image** — APPROVE image → `/get_post` to get the final post + image → copy to LinkedIn
6. **Weekly self-improvement** — Marketing Director analyzes what worked and updates strategy for next week
7. **Multi-platform** — after posting to LinkedIn, use `/repurpose` on Telegram to create X/Twitter thread, Substack newsletter draft, and TikTok slide concepts. Results arrive in Telegram — copy and post to each platform.

---

## Complete File Structure

```
brandcrew/
├── .env.example              — Copy to .env, fill in your API keys and tokens
├── .gitignore                — Keeps secrets out of git
├── README.md                 — Project overview and quick start
├── LICENSE                   — MIT license
├── CONTRIBUTING.md           — How to contribute
├── performance-patterns.md   — Weekly strategy (Marketing Director writes here)
│
├── config/                   — 🔧 Everything the user customizes
│   ├── niche.md              — Industry, expertise, keywords, audience (agents read this)
│   ├── voice.md              — Writing style and tone (Writer Agent reads this)
│   ├── audience.md           — Target audience profile (Strategist reads this)
│   ├── schedule.md           — Posting days, times, timezone (cron reads this)
│   └── watchlist.md          — Competitor/inspiration creators (populated by research agents)
│
├── agents/                   — 🤖 AI agent definitions
│   ├── research/             — Niche Content Researcher: scans for trending topics
│   │   ├── SKILL.md          — Agent instructions (what it does, how it does it)
│   │   ├── run.sh            — Shell script to trigger the agent
│   │   └── references/       — Keyword list and search guidance
│   ├── ideation/             — Content Strategist: generates content ideas from research
│   │   ├── SKILL.md
│   │   └── run.sh
│   ├── marketing_director/   — Marketing Director: weekly strategy review + self-improvement loop
│   │   ├── SKILL.md
│   │   └── run.sh
│   ├── writer/               — Content Creator: drafts posts in the user's voice
│   │   ├── SKILL.md
│   │   ├── run.sh
│   │   └── references/       — Post examples and writing references
│   ├── quality/              — Content Editor: scores drafts, pass/fail gate (35/50)
│   │   ├── SKILL.md
│   │   └── run.sh
│   ├── social_media_designer/ — Image Designer: picks template, renders branded image
│   │   ├── SKILL.md
│   │   └── run.sh
│   ├── repurposing/          — Content Repurposer: transforms posts for X, Substack, TikTok
│   │   ├── SKILL.md
│   │   └── run.sh
│   ├── analytics/            — Performance Analyst: tracks what's working (coming soon)
│   │   ├── SKILL.md
│   │   └── run.sh
│   └── part-time/            — Research team (run once, not on schedule)
│       ├── HOW_TO_RUN.md     — Step-by-step guide to running the research team
│       └── RESEARCH_BRIEF.md — The brief that tells each research agent what to do
│
├── telegram/                 — 📱 Telegram bot (control interface)
│   ├── bot.py                — The bot — handles approvals, rejections, commands
│   └── requirements.txt      — Python dependencies (pip install -r requirements.txt)
│
├── templates/                — 🎨 HTML image templates for post images
│   ├── editorial_data_card.html    — Single stat or data point
│   ├── transformation.html         — Before→after case study
│   ├── magazine_infographic.html   — Process or framework (≤5 steps)
│   ├── split_comparison.html       — Two options side by side
│   ├── bold_text_metaphor.html     — Opinion post with big headline
│   ├── quote_card.html             — Hot take or quotable insight
│   ├── sample_data.json            — Example data for testing templates
│   └── themes/
│       ├── default.json            — Default theme (customize colors/fonts here)
│       └── example-editorial.json  — Example editorial theme showing customization
│
├── scripts/                  — ⚙️ Utility scripts
│   ├── setup.sh              — First-time VPS setup (installs Node, Claude Code, Python, Playwright, creates brandcrew)
│   ├── cron-setup.sh         — Installs automated schedule (must run as brandcrew, not root)
│   ├── health-check.sh       — Verifies system health (Claude installed, files exist, bot running)
│   ├── render_template.py    — Renders HTML templates to JPG images via Playwright
│   └── snapshot.sh           — Commits VPS outputs to git periodically
│
├── supabase/                 — 💾 Database
│   ├── schema.sql            — Creates all tables (run this in Supabase SQL Editor)
│   └── TABLES.md             — Plain-English guide to every table
│
├── rules/                    — 📏 System rules all agents follow
│   ├── content-boundaries.md    — What agents can/can't write about
│   ├── quality-standards.md     — Anti-slop rules and scoring rubric
│   ├── brand-guidelines.md      — Image design rules and brand customization guide
│   ├── telegram-security.md     — Bot security and access control
│   ├── linkedin-playbook.md     — LinkedIn platform best practices
│   ├── x-playbook.md            — X/Twitter platform best practices
│   └── substack-playbook.md     — Substack platform best practices
│
├── docs/                     — 📖 User guides and system docs
│   ├── SETUP_GUIDE.md        — Detailed setup walkthrough
│   ├── NICHE_CONFIG.md       — How to configure for your niche
│   ├── TEMPLATE_GUIDE.md     — How to customize image templates
│   ├── ARCHITECTURE.md       — System design overview
│   ├── FAQ.md                — Common questions and troubleshooting
│   ├── content-gaps.md       — Competitive white space (populated by research agents)
│   └── cross-niche-formats.md — Content formats from other industries (populated by research agents)
│
└── dashboard/                — ✨ Interactive system dashboard
    ├── index.html            — Main dashboard (open in browser)
    └── sections/             — Section pages (overview, agents, pipeline, architecture, etc.)
```

---

## How the Agents Work

Agents do NOT talk to each other in real time. They communicate through files and the Supabase database.
Each agent reads the files left by previous agents, does its job, writes its output, and exits.
The files ARE the communication layer. This is intentional — cheap, reliable, no orchestrator needed.

**Important: All agents run as `brandcrew`, not root.** Claude Code refuses `--dangerously-skip-permissions` as root. The setup script creates brandcrew automatically. Cron jobs must be installed under brandcrew's crontab.

### Agent Data Flow

```
Research Agent
    reads: config/niche.md (keywords and topics)
    writes to: Supabase research_topics table

Content Strategist (Ideation)
    reads: research_topics + config/niche.md + config/audience.md
    writes to: Supabase content_ideas table
    sends: 10 ideas to Telegram for user selection

Marketing Director
    reads: Supabase agent_logs + analytics + research output + config/watchlist.md
    writes: updates strategy files (performance-patterns.md, docs/content-gaps.md)
    runs: weekly on Sunday BEFORE the Strategist

Writer Agent
    reads: approved idea from content_ideas + config/voice.md + config/niche.md + rules/quality-standards.md + rules/linkedin-playbook.md
    writes to: Supabase content_drafts table (status: draft)

Quality Agent (Editor)
    reads: content_drafts (status: draft)
    scores: 5 categories × 10 points = 50 total
    pass threshold: 35/50
    writes: updates content_drafts (status: passed or failed)
    sends: text + score to Telegram

Social Media Designer
    reads: approved draft from content_drafts
    picks: template from templates/*.html based on content type
    fills: template variables with post content
    renders: HTML → JPG via scripts/render_template.py (1080×1350, ~80-150KB)
    sends: image to Telegram

Content Repurposer
    reads: published post from content_drafts (posted: true)
    reads: rules/x-playbook.md, rules/substack-playbook.md, config/voice.md
    creates: X/Twitter thread (5-7 tweets) + Substack newsletter draft + TikTok slide concepts
    writes to: Supabase repurposed_content table
    sends: results to Telegram

User (via Telegram)
    APPROVE text → triggers designer
    APPROVE image → status = finalized
    /get_post → retrieves final post + image for LinkedIn
    /repurpose → triggers repurposer for X, Substack, TikTok
```

### Telegram Commands

**Content Pipeline:**
| Command | What it does |
|---|---|
| `/start` | Initialize the bot |
| `/team_status` | Show pipeline overview |
| `/content_analytics` | Show recent post performance |
| `/research_now` | Trigger research agent manually |
| `/ideate_now` | Generate 10 content ideas |
| `/write_now` | Draft a post from the next approved idea |
| `/quality_now` | Score the latest draft |
| `/get_post` | Get the next finalized post for LinkedIn |

**Images:**
| Command | What it does |
|---|---|
| `/regenerate_image [feedback]` | Regenerate image with feedback |
| `/image_feedback [notes]` | Log image quality notes for weekly review |

**Multi-Platform:**
| Command | What it does |
|---|---|
| `/repurpose` | Repurpose latest post to all platforms (X, Substack, TikTok) |
| `/repurpose x` | Just the X/Twitter thread |
| `/repurpose substack` | Just the Substack newsletter draft |
| `/repurpose tiktok` | Just the TikTok slide concepts |

**Strategy:**
| Command | What it does |
|---|---|
| `/marketing_director [message]` | Send strategic notes for weekly synthesis |

**Idea Selection (when ideas arrive):**
| Reply | What it does |
|---|---|
| `1,3,5,7,9` | Select ideas by number |
| `DONE` | Lock the week's ideas |
| `MORE` | Request fresh batch of ideas |
| `APPROVE` | Approve the current draft or image |
| `REJECT` | Reject the current draft or image |

---

## How the Image Template System Works

Images are NOT generated by AI image models. They are HTML/CSS templates rendered to JPG by Playwright.

1. The Social Media Designer agent reads the approved post content
2. It picks a template type based on the content (data → editorial_data_card, opinion → bold_text_metaphor, etc.)
3. It fills the template variables (headline, stats, labels, etc.)
4. `scripts/render_template.py` renders the HTML to a 1080×1350 JPG
5. The image is sent to Telegram for approval

Templates use a theme file (`templates/themes/default.json`) for colors and fonts.
The user can customize the theme to match their personal brand.
See `rules/brand-guidelines.md` for the complete design system.

---

## How the Part-Time Research Agents Work

These are NOT on a schedule. The user runs them manually, one time, after defining their niche.
They should be run BEFORE the daily pipeline starts producing content.

**What they produce:**
- `config/watchlist.md` — top creators in the user's niche with analysis
- `agents/writer/references/post-examples.md` — annotated examples of high-performing posts
- `docs/cross-niche-formats.md` — content formats from other industries that could work
- `docs/content-gaps.md` — white space and opportunities

**When to re-run:**
- Every 3-6 months, or when the niche landscape changes significantly
- When content performance drops noticeably
- When expanding into a new topic area

See `agents/part-time/HOW_TO_RUN.md` for the complete step-by-step guide.

---

## Config File Quick Reference

| File | What it controls | Who reads it | When to update |
|---|---|---|---|
| `config/niche.md` | Industry, topics, keywords, audience | Research Agent, Writer, Strategist | Once during setup, occasionally to refine |
| `config/voice.md` | Writing tone, style, vocabulary | Writer Agent | Once during setup, refine after reviewing drafts |
| `config/audience.md` | Target audience profile | Strategist, Writer | Once during setup |
| `config/schedule.md` | Posting times, timezone, cadence | Cron jobs | Once during setup, change if schedule needs shift |
| `config/watchlist.md` | Competitor/inspiration creators | Research Agent, Marketing Director | Auto-populated by part-time research agents |
| `templates/themes/default.json` | Brand colors and fonts | Social Media Designer, render script | Optional — customize for personal brand |
| `.env` | API keys, tokens, project paths | All scripts and bot | Once during setup, never share |

---

## Common Issues and How to Fix Them

### "Claude Code won't run as root" / "--dangerously-skip-permissions error"
- Claude Code refuses `--dangerously-skip-permissions` when run as root. This is by design.
- All agents MUST run as `brandcrew`. The setup script creates this user automatically.
- Switch to brandcrew: `su - brandcrew`
- If cron jobs were installed as root, remove them (`sudo crontab -r`) and reinstall as brandcrew:
  ```bash
  su - brandcrew
  cd /projects/brandcrew
  bash scripts/cron-setup.sh
  ```
- Check who you're running as: `whoami` (should show `brandcrew`, not `root`)

### "The bot doesn't respond to my messages"
- Check APPROVED_TELEGRAM_IDS in .env — your Telegram user ID must be listed
- Check that bot.py is running: `pgrep -fa bot.py`
- Check logs for errors

### "The Writer Agent isn't producing content"
- Check that there are approved ideas in Supabase content_ideas table
- Check that cron jobs are installed: `crontab -l` (as brandcrew)
- Check agent logs in Supabase agent_logs table

### "Images look wrong or don't render"
- Playwright must be installed: `npx playwright install chromium`
- Check that templates/themes/default.json exists and has valid JSON
- Test manually: `python3 scripts/render_template.py --template editorial_data_card --test`

### "The Research Agent isn't finding good topics"
- Check config/niche.md — are the keywords specific enough?
- Check config/niche.md — are there at least 8-10 keywords listed?
- The Research Agent searches the web using these keywords. Vague keywords = vague results.

### "Content doesn't sound like me"
- Check config/voice.md — is it filled in with YOUR actual voice, or still the default?
- The Writer Agent matches whatever voice.md says. Generic voice.md = generic content.
- Ask Claude to interview you and rewrite voice.md based on your answers.

### "I want to change my posting schedule"
- Edit config/schedule.md with new times
- Re-run `scripts/cron-setup.sh` to update the cron jobs (as brandcrew)
- Or manually edit crontab: `crontab -e`

### "I can't connect to my VPS"
- Double-check the IP address on your provider's dashboard
- Make sure you're using the right SSH key or password
- Try from the provider's web console first (most providers have a browser-based console)
- Check that port 22 (SSH) is open in your server's firewall settings
- If using a new server, wait 1-2 minutes for it to fully boot up

### "How do I edit files on the VPS?"
- Option A: `nano filename` — simple text editor, Ctrl+X to save and exit
- Option B: `vim filename` — press `i` to edit, `Esc` then `:wq` to save
- Option C: Use Claude Code on the VPS — `claude` then ask it to edit files for you
- Option D: Edit locally and push via git — `git add . && git commit -m "update" && git push`, then `git pull` on VPS

---

## Important Rules

1. **Manual posting only** — the system prepares content for LinkedIn, X, Substack, and TikTok but NEVER posts automatically. The user always copies and posts manually to each platform.
2. **Human-in-the-loop** — every piece of content goes through Telegram approval before it's finalized. Nothing publishes without the user's explicit APPROVE.
3. **Niche-agnostic** — the system works for any industry. All niche-specific content is in config/ files that the user fills in.
4. **Privacy** — the user's .env file, API keys, and personal config should never be committed to git. The .gitignore handles this.
5. **Anti-slop** — the system has strict quality rules (see rules/quality-standards.md). The Editor agent scores every draft and rejects AI slop. Pass threshold is 35/50.
6. **Run as brandcrew** — all agents and cron jobs must run as `brandcrew`, never as root. Claude Code will not work with `--dangerously-skip-permissions` as root.

---

## Tech Stack

- **Claude Code** — AI agent runtime (runs on VPS via cron as brandcrew)
- **Supabase** — PostgreSQL database (content queue, logs, analytics)
- **Telegram** — Human approval interface (bot.py)
- **Playwright** — HTML template → JPG image renderer
- **Cron** — Scheduling (Sunday research cycle, Mon-Fri daily posts)

---

## Helping Non-Technical Users

If the user seems confused or overwhelmed:
- Break everything into small steps. One thing at a time.
- Offer to do things for them: "Want me to fill in config/niche.md based on what you just told me?"
- Verify each step works before moving to the next
- Use the health check script to confirm system status
- Remind them: the system works with defaults first, personalization comes after
- The dashboard (dashboard/index.html) is a great visual reference — suggest they open it in a browser to see the system architecture
- If they're stuck on VPS setup, suggest starting with local testing first to see the system in action before dealing with servers
- For file editing on VPS, suggest Claude Code (`claude` command) — it can edit files interactively
- If they're having permission issues, make sure they're running as brandcrew, not root
