# Architecture — How the System Works

This document explains how BrandCrew is designed, how the agents communicate, and how data flows through the system.

---

## Design Philosophy

**Agents communicate through files and a database, not in real time.**

Each agent reads files left by previous agents, does its job, writes its output, and exits. The files ARE the communication layer. This is intentional:

- No orchestrator needed
- No complex message queues
- Cheap and reliable
- Easy to debug (just read the files)
- Any agent can be re-run independently

---

## System Components

```
┌─────────────────┐
│   Claude Code    │  AI agent runtime — runs on VPS via cron
│   (on VPS)       │  Each agent is a Claude Code session with a SKILL.md prompt
└────────┬────────┘
         │
         │ reads/writes
         ▼
┌─────────────────┐
│    Supabase      │  PostgreSQL database — content queue, logs, analytics
│    (cloud)       │  Source of truth for all content state
└────────┬────────┘
         │
         │ reads/writes
         ▼
┌─────────────────┐
│  Telegram Bot    │  Human approval interface — runs 24/7 on VPS
│  (bot.py)        │  All content goes through here before it's final
└────────┬────────┘
         │
         │ approve/reject/edit
         ▼
┌─────────────────┐
│      You         │  Approve on your phone, post manually
│  (via phone)     │  Computer can be off — VPS handles everything
└─────────────────┘
```

---

## The Agent Team

### Full-Time Agents (run on schedule)

| Agent | Job | Runs |
|---|---|---|
| **Research Agent** | Scans the niche for trending topics | Sunday |
| **Marketing Director** | Reviews performance, updates strategy | Sunday (after research) |
| **Content Strategist** | Generates 10 content ideas from research | Sunday (after director) |
| **Writer Agent** | Drafts one post per day from approved ideas | Mon-Fri |
| **Quality Agent** | Scores drafts on a 50-point rubric. Pass ≥ 35. | After each draft |
| **Social Media Designer** | Picks template, fills variables, renders branded image | After text approval |
| **Content Repurposer** | Transforms published posts for X, Substack, TikTok | On demand via /repurpose |
| **Analytics Agent** | Tracks post performance (coming soon) | Weekly |

### Part-Time Agents (run once manually)

| Agent | Job | When |
|---|---|---|
| **Niche Creator Researcher** | Finds top creators in your niche | After defining niche |
| **Cross-Market Researcher** | Finds formats from outside your niche | After defining niche |
| **Content Performance Analyst** | Analyzes what content performs best | After creator research |
| **Lead Agent** | Synthesizes all research into strategy | After all research done |

---

## Data Flow

### Weekly Cycle (Sunday)

```
Research Agent → Supabase research_topics
       │
       ▼
Marketing Director reads performance + feedback → updates performance-patterns.md
       │
       ▼
Content Strategist reads research + strategy → generates 10 ideas → Supabase content_ideas
       │
       ▼
Telegram: user selects ideas (e.g., "1,3,5,7,9" → DONE)
```

### Daily Cycle (Mon-Fri)

```
Writer Agent reads approved idea + voice.md + niche.md → Supabase content_drafts (draft)
       │
       ▼
Quality Agent scores draft (5 categories × 10 pts = 50) → pass ≥ 35
       │
       ▼
Telegram: user sees text + score → APPROVE / REJECT / edit notes
       │
       ▼ (if approved)
Social Media Designer picks template → renders JPG → Telegram
       │
       ▼
User APPROVEs image → status = finalized
       │
       ▼
/get_post → final text + image delivered for LinkedIn
       │
       ▼ (optional)
/repurpose → X thread + Substack draft + TikTok slides → Telegram
```

### The Self-Improving Loop

```
Posts go live on LinkedIn
       │
       ▼
User logs performance via /marketing_director (impressions, comments, reposts)
       │
       ▼
Marketing Director reads performance + edit patterns + rejected ideas
       │
       ▼
Updates performance-patterns.md with new strategy
       │
       ▼
Writer + Strategist read updated strategy next cycle
       │
       ▼
Content gets better every week based on real data
```

This is the closed feedback loop. The system improves without you changing any code.

---

## Cron Schedule

All times UTC. Adjust for your timezone in `crontab -e`.

| Time | Day | Agent |
|---|---|---|
| 2:00pm | Sunday | Research Agent |
| 2:30pm | Sunday | Marketing Director |
| 3:00pm | Sunday | Content Strategist |
| 10:00am | Mon-Fri | Writer (auto-chains to Quality Agent) |
| Every 6h | Daily | Health check |
| 6:00am | Every 4 days | Snapshot (git commit) |

The Content Repurposer is NOT on cron — it's triggered manually via `/repurpose` after you post to LinkedIn.

---

## Database Tables (Supabase)

| Table | Purpose | Who writes | Who reads |
|---|---|---|---|
| `research_topics` | Trending topics found by research | Research Agent | Content Strategist |
| `content_ideas` | Generated content ideas | Content Strategist | Writer Agent, Telegram bot |
| `content_drafts` | Post drafts with scores and images | Writer, Quality, Designer | Telegram bot, Repurposer |
| `agent_logs` | All agent activity and operator feedback | All agents, Telegram bot | Marketing Director |
| `repurposed_content` | Cross-platform versions of posts | Content Repurposer | Telegram bot |

See `supabase/TABLES.md` for the complete schema reference.

---

## File-Based Communication

Agents also communicate through markdown files on disk:

| File | Written by | Read by |
|---|---|---|
| `performance-patterns.md` | Marketing Director | Writer, Strategist |
| `docs/content-gaps.md` | Lead Agent (part-time) | Marketing Director, Strategist |
| `docs/cross-niche-formats.md` | Cross-Market Researcher | Marketing Director |
| `config/watchlist.md` | Niche Creator Researcher | Research Agent |
| `agents/writer/references/post-examples.md` | Performance Analyst | Writer Agent |

These files persist between sessions. When the Marketing Director updates strategy on Sunday, the Writer reads it Monday morning.

---

## Security Model

- **Telegram whitelist** — only approved user IDs can interact with the bot (see `rules/telegram-security.md`)
- **No auto-posting** — content is never published automatically. Manual posting to every platform.
- **Credentials in .env only** — never in code, never in git. The .gitignore handles this.
- **VPS isolation** — agents run in their own Claude Code sessions with defined tool permissions
