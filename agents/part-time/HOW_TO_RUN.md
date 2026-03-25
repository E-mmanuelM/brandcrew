# How to Run the Part-Time Research Team

Run four separate Claude Code sessions back to back — one per agent.
Each session is self-contained, cheap, and safe. If one dies, just rerun that agent alone.
No Agent Teams needed — agents don't need to talk to each other in real time.
They communicate through files, which is exactly what the brief was designed for.

---

## Why Sequential Instead of Agent Teams

Agent Teams run all agents simultaneously with shared context windows — expensive and unpredictable cost.
Sequential sessions run one agent at a time — each reads the brief, does its job, writes its file, done.
The only "communication" needed is file handoff, which happens naturally when you run them in order.

**Token cost per session:** roughly equivalent to a heavy Claude Code coding session.
**Total for all 4 sessions:** manageable — spread across separate runs, not all at once.

---

## Prerequisites

- Claude Code installed and authenticated on your PC
- Repo cloned locally: `git clone <your-repo-url>`
- GitHub MCP configured in your local `.mcp.json` (so Lead Agent can push files)
- Check your usage at claude.ai → Settings → Usage before starting — you want weekly at under 60%

---

## The Run Order

```
Session 1: Niche Creator Researcher         (no dependencies — run first)
Session 2: Cross-Market Content Researcher  (no dependencies — run in parallel or after Session 1)
Session 3: Niche Content Performance Analyst (needs Session 1 output — run after Session 1)
Session 4: Lead Agent                        (needs all 3 outputs — run last)
```

Sessions 1 and 2 have no dependencies — you can run them on the same day in either order.
Session 3 must wait for Session 1 to finish.
Session 4 must wait for all three to finish.

---

## Session 1 — Niche Creator Researcher

**Navigate to the project and start Claude Code:**
```bash
cd $PROJECT_DIR
claude
```

**Paste this prompt exactly:**
```
Read agents/part-time/RESEARCH_BRIEF.md in full before doing anything.

You are the Niche Creator Researcher from the Part-Time Agent Team.

Your job, output file, exact file format, and research approach are all 
specified in the brief under the "Niche Creator Researcher" section.

Read that section carefully. Then confirm your understanding of:
- What file you will write
- How many creators you will find (exact number)
- What format you will use

Wait for my confirmation before starting research.
```

**Check its plan — it should say:**
- Output: `config/watchlist.md`
- 15 creators (10 established + 5 momentum)
- Exact format from the brief

**Confirm:** "Go ahead."

**When done:** Check `config/watchlist.md` exists with real content. Close session.

---

## Session 2 — Cross-Market Content Researcher

**Start a fresh Claude Code session:**
```bash
claude
```

**Paste this prompt exactly:**
```
Read agents/part-time/RESEARCH_BRIEF.md in full before doing anything.

You are the Cross-Market Content Researcher from the Part-Time Agent Team.

Your job, output file, exact file format, and research approach are all 
specified in the brief under the "Cross-Market Content Researcher" section.

Read that section carefully. Then confirm your understanding of:
- What file you will write
- How many outside creators you will profile (exact number)
- How many transplantable formats you will identify (exact number)
- That you must include the multi-platform section (LinkedIn, YouTube, X, Substack)

Wait for my confirmation before starting research.
```

**Check its plan — it should say:**
- Output: `docs/CROSS_NICHE_TRANSPLANTS.md`
- 8 outside creators
- 6 transplantable formats
- Multi-platform section included
- YouTube research explicitly included

**Confirm:** "Go ahead."

**When done:** Check `docs/CROSS_NICHE_TRANSPLANTS.md` exists with real content. Close session.

---

## Session 3 — Niche Content Performance Analyst

**Only run this after Session 1 is complete and `config/watchlist.md` exists.**

**Start a fresh Claude Code session:**
```bash
claude
```

**Paste this prompt exactly:**
```
Read agents/part-time/RESEARCH_BRIEF.md in full before doing anything.

You are the Niche Content Performance Analyst from the Part-Time Agent Team.

Your job, output file, exact file format, and research approach are all 
specified in the brief under the "Niche Content Performance Analyst" section.

Before starting: read config/watchlist.md — this is the creator 
watchlist the Niche Creator Researcher already produced. Use it as your 
starting point for finding real post examples.

Then confirm your understanding of:
- What file you will write
- How many post examples you will annotate (exact number)
- That you are looking for 2026 engagement signals (saves/shares, not just likes)

Wait for my confirmation before starting research.
```

**Check its plan — it should say:**
- Output: `agents/writer/references/post-examples.md`
- 10 annotated post examples
- Starting from the watchlist
- Looking for saves/shares/comments as signals

**Confirm:** "Go ahead."

**When done:** Check output file exists. Close session.

---

## Session 4 — Lead Agent (Synthesis)

**Only run this after Sessions 1, 2, and 3 are all complete.**

**Start a fresh Claude Code session:**
```bash
claude
```

**Paste this prompt exactly:**
```
Read agents/part-time/RESEARCH_BRIEF.md in full before doing anything.

You are the Lead Agent from the Part-Time Agent Team.

The three researchers have completed their work. These files now exist:
- config/watchlist.md (from Niche Creator Researcher)
- docs/CROSS_NICHE_TRANSPLANTS.md (from Cross-Market Content Researcher)
- agents/writer/references/post-examples.md (from Niche Content Performance Analyst)

Your job is Part 2 — Synthesis. Read all three files, then produce:
- docs/CONTENT_GAPS.md
- docs/INITIAL_RESEARCH_REPORT.md

Both file formats are specified exactly in the brief under "Lead Agent — Coordination and Synthesis".

Read all three input files first. Then confirm your understanding of both 
output formats before writing anything.

Wait for my confirmation before writing.
```

**Check its plan — it should say:**
- Will read all 3 files first
- Will produce both output files
- Understands both exact formats

**Confirm:** "Go ahead. When both files are written, push all 5 output files to your repo via the GitHub MCP tool."

---

## Reviewing the Output

When Session 4 is done, check `docs/INITIAL_RESEARCH_REPORT.md` and ask:
- Do the recommended content pillars feel right for your actual expertise?
- Does the gap analysis surface anything surprising?
- Are the post examples genuinely good, or generic filler?
- Does the cross-market section have specific, actionable format ideas?
- Is the YouTube audience intelligence section useful?

If something is off — open a new session, point it at the specific file, and ask it to go deeper on that section only.

---

## What This Session Produces

| File | Used By |
|---|---|
| `config/watchlist.md` | Niche Content Researcher (weekly monitoring) |
| `agents/writer/references/post-examples.md` | Content Creator |
| `docs/CROSS_NICHE_TRANSPLANTS.md` | Content Strategist |
| `docs/CONTENT_GAPS.md` | Content Strategist, Marketing Director |
| `docs/INITIAL_RESEARCH_REPORT.md` | All agents as reference + operator review |

---

## If a Session Dies Midway

Don't panic. Whatever was written to the output file is saved.
Just start a new session for that agent and tell it:
```
Read agents/part-time/RESEARCH_BRIEF.md.
You are the [Agent Name]. Your output file already has partial content.
Read what's there, then continue from where it stopped without repeating completed sections.
```

---

## When to Run Again

- 3+ months have passed and the niche landscape may have shifted
- Content performance starts degrading noticeably
- You want to expand into a new topic area
- Major LinkedIn algorithm change

Before re-running: rename existing output files with a date suffix to preserve them.
Example: `INITIAL_RESEARCH_REPORT_2026-03.md`
