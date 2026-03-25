# BrandCrew

**An autonomous content marketing team. Talk to your agents on Telegram. Always on. Auto-improving.**

BrandCrew is an open-source multi-agent system that runs your entire LinkedIn content pipeline — from niche research to post design — with AI agents you direct through Telegram. Every week, the agents research, strategize, write, score, design, and deliver. Every cycle, they get smarter from your feedback.

No orchestrator. No dashboard to babysit. You talk to your crew on Telegram. They do the work.

---

## How It Works

**7 full-time agents** run on a VPS via cron. Each has a defined role, reads specific files, writes to specific outputs, and never talks to another agent directly. The filesystem is the communication layer.

```
Sunday     Research → Direction → 10 Ideas → You pick (Telegram)
Mon–Fri    Write → Score (35/50 pass) → You approve → Design → Deliver
Every cycle  Marketing Director reads all feedback, adjusts strategy
```

You make 3 decisions per week via Telegram:
1. **Pick ideas** — 10 ideas arrive, you multi-select your favorites
2. **Approve drafts** — read the post, approve or send notes
3. **Review designs** — see the image, approve or request changes

Everything else is automated.

---

## The Crew

| Code | Agent | Role |
|------|-------|------|
| FT.01 | Niche Content Researcher | Scans your niche weekly for trending topics |
| FT.02 | Marketing Director | Synthesizes all data into weekly strategic direction |
| FT.03 | Content Strategist | Generates 10 ideas from research for your selection |
| FT.04 | Content Creator | Writes posts in your voice from approved ideas |
| FT.05 | Content Editor | Scores drafts on 5 dimensions — 35/50 to pass |
| FT.06 | Social Media Designer | Selects templates and renders branded visuals via Playwright |
| FT.07 | Content Repurposer | Adapts posts for X, newsletters, blog |

Plus **4 part-time research agents** for deep niche intelligence, and **1 interactive agent** for extracting your expertise through guided interviews.

---

## Self-Improving Feedback Loops

This is not a "generate and forget" system. Three feedback loops run continuously: 
Built on an auto-research framework — agents continuously gather niche intelligence, analyze what's working, and feed insights back into the pipeline before any content is created.


- **Content quality loop** — Every draft is scored. Scores feed back into the Marketing Director's weekly analysis. Low-performing patterns get flagged. High-performing patterns get amplified.
- **Design quality loop** — You review every image. Feedback goes to the Designer's rules file. The system learns your visual preferences over time.
- **Strategic direction loop** — You can send strategic notes anytime via `/marketing_director` on Telegram. The Director reads these alongside performance data to adjust the entire pipeline's direction.

The agents don't have memory. They have **files** — shared knowledge files that get updated based on feedback, read by the agents that need them, and version-controlled in this repo.

---

## Stack

| Component | What | Cost |
|-----------|------|------|
| AI | Claude (via Claude Code) | API usage |
| Database | Supabase (Postgres) | Free tier |
| Server | Hetzner VPS (Ubuntu) | ~$5/mo |
| Scheduling | Cron | Free |
| Communication | Telegram Bot | Free |
| Design | HTML templates + Playwright | $0 |
| Code | This repo | Open source |

No proprietary frameworks. No LangChain. No vector databases. Agents are SKILL.md files executed by Claude Code via bash scripts. The simplest architecture that works.

---

## Project Structure

```
brandcrew/
├── agents/
│   ├── research/          # FT.01 — Niche researcher
│   ├── marketing_director/ # FT.02 — Weekly strategist
│   ├── ideation/          # FT.03 — Idea generator
│   ├── writer/            # FT.04 — Post creator
│   ├── quality/           # FT.05 — Scoring editor
│   ├── designer/          # FT.06 — Visual designer
│   ├── repurposer/        # FT.07 — Multi-platform adapter
│   └── ip_extractor/      # IA.01 — Expertise interviewer
├── shared/                # Shared knowledge files (agent memory)
│   ├── voice.md           # Your voice profile
│   ├── performance-patterns.md  # Weekly direction
│   ├── brand-guidelines-skill.md # Design rules
│   └── quality-standards.md     # Anti-slop filter
├── templates/             # 6 HTML post templates
├── telegram/              # Bot with 12 commands
├── scripts/               # Design renderer (Playwright)
├── supabase/              # Schema (5 tables)
└── docs/                  # Research reports & blueprints
```

Every agent folder contains a `SKILL.md` (instructions) and `run.sh` (cron runner).

---

## Niche-Agnostic

BrandCrew is configured for a specific niche through a few files:
- `shared/niche.md` — audience, keywords, competitive landscape
- `shared/voice.md` — your writing voice and perspective
- `shared/boundaries.md` — topics that are off-limits

Swap these files and the entire system adapts to a different B2B industry.

