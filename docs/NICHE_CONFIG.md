# Niche Configuration — Make It Yours

The system ships with a B2B SaaS example niche that works on day one. This guide shows you how to replace it with YOUR industry, expertise, and audience.

Estimated time: 10-15 minutes.

**Tip:** If you're using Claude Code, just say "help me configure this for my niche" and it will interview you and fill in the files based on your answers.

---

## Which Files to Edit

There are 4 config files. Edit them in this order:

| File | What it controls | Priority |
|---|---|---|
| `config/niche.md` | Your industry, topics, keywords | **Must edit** — everything reads this |
| `config/voice.md` | How you write and communicate | **Must edit** — Writer Agent reads this |
| `config/audience.md` | Who you're writing for | **Should edit** — improves targeting |
| `config/schedule.md` | When posts are created and approved | Optional — defaults are fine |

`config/watchlist.md` is auto-populated by the research agents. Don't edit it manually.

---

## config/niche.md — Your Industry

This is the most important file. Every agent reads it to understand what your niche is.

**What to fill in:**

- **Industry/domain** — what field are you in? Be specific. "Manufacturing" is OK, "automotive parts manufacturing" is better.
- **Your expertise** — what specifically do you know better than most people? What have you done for 5-10+ years?
- **Core topics** — the 5-10 topics your content will cover. These become the keywords the Research Agent uses to find trending content.
- **Topic Acceptance Categories** — what types of content are allowed. The Research Agent uses these to filter what it finds. The default categories (tools in practice, niche workflows, efficiency, practitioner reality) work for most industries.
- **What's off-limits** — topics you will never cover. Industry politics? Competitor bashing? Vendor comparisons? Define the boundaries.

**Example for a cybersecurity professional:**
```markdown
## Industry
Cybersecurity — specifically cloud security and DevSecOps

## Your Expertise
12 years in enterprise security. Built security programs at 3 companies.
Deep in AWS security, container security, and incident response.

## Core Topics
- Cloud security architecture
- DevSecOps pipelines
- Container and Kubernetes security
- Security automation
- Incident response playbooks
- Compliance as code (SOC2, ISO 27001)
- Security tools (Snyk, Wiz, Prisma Cloud)
- Team building for security orgs

## Off-Limits
- No vendor bashing or competitive comparisons
- No fear-mongering about breaches without practical takeaways
- No content targeting specific companies' security failures
```

---

## config/voice.md — Your Writing Style

The Writer Agent reads this before every draft. The more specific you are, the more the content sounds like you.

**Two ways to fill this in:**

**Option A (recommended): Let Claude interview you.** Open Claude Code and say: "Interview me about my communication style and fill in config/voice.md based on my answers." It will ask you 5-8 questions about how you write, what words you use, what you avoid, your humor style, and your perspective.

**Option B: Fill it in manually.** Key sections:

- **Tone** — professional but casual? Academic? Conversational? Provocative?
- **Perspective** — first person ("I did this")? Third person? Teaching style? Peer-to-peer?
- **Words you use** — industry jargon you like, phrases that are "you"
- **Words you never use** — AI slop words ("leverage", "synergy", "game-changer"), corporate speak you hate
- **Humor** — dry? Self-deprecating? None? Sarcastic?
- **Opinions** — what are you known for being opinionated about?

**The test:** After the Writer produces a few drafts, read them and ask: "Would my colleagues believe I wrote this?" If no, refine voice.md.

---

## config/audience.md — Who You're Writing For

**What to fill in:**

- **Primary audience** — job titles, seniority level, industry. "Mid-level operations managers in manufacturing" is better than "business professionals."
- **What they struggle with** — their daily pain points, what keeps them up at night
- **What content they engage with** — do they like tactical how-tos? Big-picture strategy? Personal stories?
- **What they scroll past** — generic advice? Long essays? Clickbait?

---

## config/schedule.md — When and How Often

The defaults work for most people:
- Sunday: research + ideation (10 ideas generated)
- Monday-Friday: one post per day
- Timezone: UTC (adjust for yours)

Change this if you want a different cadence (e.g., 3 posts per week instead of 5).

After editing, rebuild the cron schedule:
```bash
bash scripts/cron-setup.sh
```

---

## After Configuring: Run the Research Team

Once your niche is defined, run the part-time research team BEFORE the daily pipeline starts. This populates:
- Competitive intelligence (who's winning in your niche)
- Content formats that work
- White space opportunities

See `agents/part-time/HOW_TO_RUN.md` for the step-by-step guide. Takes ~20-30 minutes across 4 Claude Code sessions.

---

## How Agents Use Your Config

| Agent | Reads | Why |
|---|---|---|
| Research Agent | niche.md | Searches for topics using your keywords |
| Content Strategist | niche.md, audience.md | Generates ideas relevant to your industry and audience |
| Marketing Director | niche.md, watchlist.md | Reviews strategy in context of your niche |
| Writer Agent | voice.md, niche.md, audience.md | Writes in your voice, for your audience, about your topics |
| Content Repurposer | voice.md, audience.md | Maintains your voice across platforms |

The more specific your config files are, the better every agent performs. Generic config = generic content.
