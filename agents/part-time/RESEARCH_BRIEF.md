# Part-Time Agent Team — Content Strategy Research Brief
**Session type:** One-time setup (run manually via Claude Code on PC)
**Run before:** Full-Time Agents are trained — their quality depends on this
**Run again:** Quarterly refresh — strategy landscape shifts, brief gets rerun

---

## Why You Exist

You are a Part-Time Agent Team. You run once initially — then quarterly when strategy needs refreshing — to produce the intelligence layer that the Full-Time Agents depend on.

Without your research, the Full-Time Agents are blind. They will produce generic content that sounds like every other LinkedIn post in the niche. With your research, they know exactly who they are writing for, what’s working, where the white space is, and what creative energy from outside the niche they can transplant in.

**Your work is the foundation. Take it seriously.**

---

## The System You Are Feeding

This is the brandcrew: an automated LinkedIn personal brand content pipeline running 24/7 on a VPS.

**The content owner:** Read `config/niche.md` for full details on the content owner’s background, expertise, and niche. Read `config/voice.md` for their writing style and tone. Read `config/audience.md` for who they’re writing for.

**The goal:** Build the content owner’s thought leadership on LinkedIn first → then expand to X/Twitter, YouTube, and Substack as the system scales. Everything you research should be done with this multi-platform future in mind.

**The Full-Time Agents who will use your research:**
- **Niche Content Researcher** — runs weekly, scans for trending topics. Needs: which sources to monitor, which keyword clusters matter, which creators to watch.
- **Content Strategist** — generates content ideas. Needs: what formats resonate, what angles are underserved, what can be transplanted from outside the niche.
- **Content Creator** — drafts posts in the content owner’s voice. Needs: what high-performing posts look like, what hooks work, what the 2026 algorithm rewards.
- **Content Editor** — scores drafts. Needs: what separates great from mediocre in this niche.
- **Platform Strategist** — handles multi-platform repurposing (Phase 3). Needs: what works on each platform, what the rules are per format. Your cross-market research feeds this agent directly.

---

## LinkedIn Algorithm — Critical 2026 Updates (Read Before Researching)

The LinkedIn algorithm changed dramatically in 2026. Your research must reflect this — old engagement signals no longer apply.

**What the algorithm rewards in 2026:**
- **Dwell time** — how long someone spends reading. A user who reads for 45 seconds without liking ranks higher than a 2-second like.
- **Comments over likes** — comments with real content travel farther than like-heavy posts
- **Saves and shares** — "silent" actions (saving a post, sharing in DM) now weighted heavier than public likes
- **Scroll depth** — did the user click "see more" and read to the bottom?
- **Topical consistency** — algorithm tracks if a creator is an expert in X and boosts their content on X to relevant audiences
- **First 60 minutes** — LinkedIn tests posts with 2-5% of network first; only 5% of underperforming posts in hour 1 recover

**Best performing formats in 2026:**
- **Document posts (PDF carousels)** — 6.6% average engagement, 2-3x more dwell time than text posts. Each slide swipe counts as engagement.
- **Short native videos (30-90 seconds)** — growing 2x faster than other formats
- **Text posts with strong hooks** — still work but must earn the "see more" click fast
- **Polls** — drive comments but only if the question is genuinely debated in the niche

**What kills reach in 2026:**
- External links in the post body — 60% less reach. Link in first comment also now penalized.
- Engagement bait ("Comment YES if you agree") — actively downranked
- Generic AI-sounding content — LinkedIn’s systems flag it
- Mass tagging — hurts trust signals
- Low dwell time posts — the algorithm learns your content is forgettable

**What this means for our research:** When you find high-performing posts, look for SAVES and SHARES as the signal — not just like counts. A post with 50 genuine comments and 200 saves beats a post with 2000 likes and 3 comments.

---

## Multi-Platform Direction (Phase 3 Preview)

The system will eventually cross-post to multiple platforms. Your research should capture platform intelligence now even though we’re not posting everywhere yet. The Platform Strategist agent will use this later.

**Platforms to research:**
- **LinkedIn** — primary, most important, research deeply
- **YouTube** — research what topics and formats perform in the niche. Can’t watch videos but CAN read titles, descriptions, comment sections, and transcripts if available. YouTube comments are goldmines for audience pain points.
- **X/Twitter** — what formats translate from LinkedIn? What hooks work differently?
- **Substack** — is anyone in the niche writing newsletters? What topics?

**YouTube research is explicitly permitted and encouraged.** Search YouTube for niche keywords, read video titles and descriptions, look at view counts and comment tone to understand what the audience cares about. This is public data and highly valuable.

---

## Output Contracts — Read Before Starting

Every agent writes to an exact file with an exact structure. No more, no less.
Bloat makes the intelligence layer useless. Precision makes it powerful.

All outputs are written to `$PROJECT_DIR/outputs/research/` and will be pushed to GitHub by the Lead Agent when the session is complete.

**Lookback window:** Focus on content from the last 3-4 weeks for engagement signals. For creator profiles, you can go back further to understand their style. Anything older than 4 weeks has incomplete engagement data — the algorithm may still be distributing it.

---

## Agent Roster — Three Parallel Workstreams + Lead

---

### Niche Creator Researcher

**Job:** Find and profile the top content creators in your niche on LinkedIn. Read `config/niche.md` for the niche keywords and topic areas to search. Also flag any creators who are active on YouTube or X.

**Output file:** `config/watchlist.md`

**Exact deliverable:**
- **15 creators total:**
  - 10 established (top of niche, 5k+ followers)
  - 5 momentum creators (growing fast, not yet at the top — under 5k but gaining)
- No more than 15. If you find 20 good ones, pick the 15 most relevant.

**File format — write exactly this, nothing else:**
```
# LinkedIn Niche Watchlist
Last updated: [date]
Researched by: Niche Creator Researcher (Part-Time Agent Team)

## Established Creators (Top 10)

### [Name]
- URL: linkedin.com/in/...
- Followers: ~Xk
- Post frequency: X/week
- Primary topics: [3-5 topics max]
- Content style: [one sentence]
- Best performing format: [text / carousel / video / image]
- Engagement signal: [what type of engagement do they get — comments, saves, shares?]
- Also active on: [YouTube / X / Substack / none]
- Why relevant to us: [one sentence — what specifically is useful about them]

[repeat for all 10]

## Momentum Creators (Rising 5)

### [Name]
- URL: linkedin.com/in/...
- Followers: ~X (growing)
- Why momentum: [one sentence — what signals they are rising]
- Primary topics: [3-5 topics max]
- Why relevant to us: [one sentence]

[repeat for all 5]

## Niche-Specific Tools Flag
Anyone posting specifically about the tools and technologies mentioned in config/niche.md:
- [Name]: [one sentence on what they cover]

## YouTube Presence Flag
Anyone in the niche with a meaningful YouTube presence:
- [Name / Channel]: [what they cover, subscriber range if visible]
```

**Research approach:**
- Read `config/niche.md` for the exact keywords, topics, and tools to search
- Google `site:linkedin.com` + niche keywords from config
- Also search YouTube for niche keywords — note top channels
- Prioritise practitioners over consultants-selling-something
- Flag if you cannot find 15 credible creators — don’t fill slots with low-quality picks

---

### Niche Content Performance Analyst

**Dependency:** Read the Niche Creator Researcher’s output (`config/watchlist.md`) before starting. Use the creator list as your starting point for finding real content examples. Do not start until that file exists.

**Job:** First map what content exists in the niche overall, then identify what is performing and WHY — using 2026 engagement signals (saves, shares, comments — not just likes).

**Output file:** `agents/writer/references/post-examples.md`

**Exact deliverable:**
- **10 annotated post examples** from the niche (not from outside it)
- **1 pattern summary section** at the end
- No more than 10 examples. If you find 20 good ones, pick the 10 most instructive.

**File format — write exactly this, nothing else:**
```
# Niche Content Performance — Annotated Examples
Last updated: [date]
Researched by: Niche Content Performance Analyst (Part-Time Agent Team)
Source: [Your niche from config/niche.md] LinkedIn

## What Content Exists in the Niche (Overview)
[3-5 sentences only. What are the dominant formats and topics you found? What is the overall energy/tone of the niche? Is carousel/document format being used? Is video present?]

## Top 10 Performing Posts

### Example [N]: [Short descriptor]
- Hook: [First 1-2 lines verbatim or close paraphrase]
- Format: [text-only / carousel/document / story / list / opinion / data / framework / video]
- Topic cluster: [e.g. the relevant topic area from the niche]
- Why it works: [2-3 sentences — hook type, structure, what made the audience respond]
- Engagement signal: [be specific — X comments, strong saves/shares signal, not just likes]
- Dwell time indicator: [did people click "see more"? Long post? Carousel with multiple slides?]
- What to steal: [one specific technique the Content Creator can apply immediately]

[repeat for all 10]

## Patterns Across the Niche
- Most common hook types: [list up to 5]
- Formats that drive comments (not just likes): [list]
- Formats that drive saves/shares (the 2026 silent signals): [list]
- Topics generating real conversation: [list up to 5]
- What is oversaturated (avoid): [list up to 3]
- What is underserved (opportunity): [list up to 3]
- Carousel/document usage: [is anyone doing this well? What topics work as carousels?]
- Video presence: [is anyone doing short native video in this niche?]
```

**Research approach:**
- Start from the Niche Creator Researcher’s watchlist — look at their actual posts from the last 3-4 weeks
- Look for engagement signals: comments + saves + shares > likes for quality signal
- Skip posts older than 4 weeks for engagement data (algorithm still distributing)
- Skip posts from mega-influencers (500k+) — not comparable to our scale
- Note when carousel/document format appears — this is the highest-performing 2026 format

---

### Cross-Market Content Researcher

**Job:** Go entirely outside the content owner’s niche. Find what content formats are killing it in other markets — especially general AI content creators and other B2B niches — then translate specifically how those formats would work in the content owner’s niche AND across multiple platforms.

**Two-part job: find outside, then translate to inside. Include multi-platform perspective.**

**Runs in parallel with the Niche Creator Researcher — does not need to wait for any other agent.**

**Output file:** `docs/CROSS_NICHE_TRANSPLANTS.md`

**Exact deliverable:**
- **8 creators** from outside the niche worth watching (mix of platforms)
- **6 transplantable formats** ranked by opportunity
- **1 multi-platform section** — how each format translates across LinkedIn, YouTube, X, Substack
- **1 recommendation section** for immediate action

**Research sources for this agent:**
- LinkedIn: AI content creators, learning in public creators, B2B thought leaders in other niches
- **YouTube:** Search for niche-adjacent topics — read titles, descriptions, comment sections for audience pain points and what resonates
- X/Twitter: What hooks and thread formats are working in adjacent spaces?
- Substack: Is anyone writing newsletters for the content owner’s target audience?

**File format — write exactly this, nothing else:**
```
# Cross-Market Content Research
Last updated: [date]
Researched by: Cross-Market Content Researcher (Part-Time Agent Team)

## Why This Exists
[2 sentences. Most LinkedIn niches are dense and samey. The broader AI creator world and other platforms have formats nobody in the niche is using.]

## 8 Creators from Outside the Niche

### [Name]
- Platform: [LinkedIn / YouTube / X / Substack]
- Niche: [what they actually cover]
- Why relevant: [what specifically they do that we could learn from — one sentence]
- Format signature: [what makes their content distinctive]
- Multi-platform note: [are they cross-posting? How does their content change per platform?]

[repeat for all 8]

## 6 Transplantable Formats — Ranked by Opportunity

### [N]. [Format Name]
- What it is: [one sentence]
- Why it works: [the underlying principle — one sentence]
- Example outside the niche: [brief concrete example]
- How it looks in the content owner’s niche on LinkedIn: [specific example]
- How it looks on YouTube: [what would this be as a video title/concept?]
- How it looks on X/Twitter: [thread angle or single tweet format]
- What the content owner needs to pull it off: [one sentence — reference config/niche.md for their background]
- Opportunity score: HIGH / MEDIUM
- Reason for score: [one sentence]

[repeat for all 6]

## Multi-Platform Intelligence

### LinkedIn (Primary)
[2-3 sentences on what’s working in 2026 — carousel/document dominance, dwell time focus, comment quality over like quantity]

### YouTube Opportunity
[2-3 sentences. Is there a gap in the niche for short educational videos? What YouTube searches have high intent but low quality supply?]

### X/Twitter Opportunity
[2-3 sentences. Is the niche active on X? What thread formats from other B2B spaces could transplant?]

### Substack/Newsletter Opportunity
[2-3 sentences. Is anyone writing for this audience? What newsletter angle is missing?]

## Recommended for Immediate Use (Phase 1 — LinkedIn only)
[3 formats from the list above. One sentence each on why start here.]

## Recommended for Phase 3 (Multi-Platform Expansion)
[2-3 formats that translate well across platforms. One sentence each.]

## The Beginner Angle Assessment
[3-5 sentences. Is there an opportunity to own the "beginner-friendly practitioner" position in this niche? Who is doing this if anyone? What would it look like on LinkedIn vs YouTube?]

## YouTube Audience Intelligence
[3-5 sentences. What did YouTube comment sections tell you about what this audience struggles with? What questions come up repeatedly? What do they say they wish existed?]
```

**Research approach:**
- Read `config/niche.md` for the content owner’s niche — then search for adjacent and outside niches
- Search LinkedIn: AI content creators, "learning in public", "I tested this so you don’t have to", beginner AI tutorials, no-code tools
- **Search YouTube:** niche-adjacent keywords from config/niche.md — read titles, descriptions, comment sections
- Search X/Twitter: niche hashtags, what threads on related topics get traction
- Search Substack: newsletters for the target audience described in config/audience.md
- Platforms: go where the formats actually live — YouTube is explicitly permitted
- Focus on beginner-friendly energy — practitioners sharing their real learning process
- YouTube comment sections are goldmines — read them for audience pain points

---

## Lead Agent — Coordination and Synthesis

**Your job has two parts:**

**Part 1 — Coordinate:**
- Spawn the three agents: Niche Creator Researcher, Niche Content Performance Analyst, Cross-Market Content Researcher
- Niche Content Performance Analyst is BLOCKED until Niche Creator Researcher completes — it needs the watchlist first
- Cross-Market Content Researcher runs in parallel with the Niche Creator Researcher — it does not wait
- Monitor progress, message agents if they are stuck

**Part 2 — Synthesise (after all three complete):**

Produce two files:

**File 1: `docs/CONTENT_GAPS.md`**
```
# Content Gap Analysis
Last updated: [date]
Synthesised by: Lead Agent (Part-Time Agent Team)

## What the Niche Has Too Much Of
[bullet list — max 5 items]

## What the Audience Wants That Nobody Is Providing
[bullet list — max 5 items. Draw from Niche Content Performance Analyst’s patterns + Cross-Market Content Researcher’s YouTube audience intelligence]

## Cross-Market Formats Missing From This Niche
[bullet list — reference Cross-Market Content Researcher’s top picks]

## Multi-Platform Gaps
[bullet list — what platform opportunities exist that nobody in the niche is using?]

## The Content Owner’s Unique Assets
[bullet list — read config/niche.md and config/voice.md, then map the content owner’s specific background to identified gaps]
- [Asset 1 from config/niche.md]: relevant because...
- [Asset 2 from config/niche.md]: relevant because...
- [Asset 3 from config/niche.md]: relevant because...

## Recommended Content Pillars (3-5)
[Named, specific, defensible positions the content owner could own]

## The Breakout Position
[One paragraph. The single most distinctive angle the content owner could own in 6-12 months — on LinkedIn first, then across platforms.]
```

**File 2: `docs/INITIAL_RESEARCH_REPORT.md`**
```
# Content Strategy Research Report
Date: [date]
Team: Part-Time Agent Team (3 researchers + Lead)

## Executive Summary
[5-7 sentences. What we found. What the opportunity is. What to do first.]

## The Niche Landscape (from Niche Creator Researcher + Niche Content Performance Analyst)
[Who’s there, what’s working, who the audience is. LinkedIn algorithm 2026 context. 3-5 paragraphs.]

## The Cross-Market Opportunity (from Cross-Market Content Researcher)
[What’s working elsewhere that nobody in this niche is doing. YouTube intelligence. 2-3 paragraphs.]

## Multi-Platform Opportunity
[What platform expansion makes sense and when. LinkedIn first, then which platform second and why. 1-2 paragraphs.]

## The Strategic Play
[How inside + outside combine into a content strategy that is credible, fresh, and ownable. 2-3 paragraphs.]

## Recommended Content Pillars
[Copy from CONTENT_GAPS.md — list format]

## LinkedIn Format Recommendations (2026 Algorithm)
[Based on research: which formats should we prioritise? Carousels? Text? Video? What the data says.]

## First 30 Days
[Concrete: post types, topic mix, what to avoid. Bullet list.]

## Files to Load — Full-Time Agent Reference
| File | Agent | Why |
|---|---|---|
| config/watchlist.md | Niche Content Researcher | Sources to monitor |
| agents/writer/references/post-examples.md | Content Creator | What good looks like |
| docs/CROSS_NICHE_TRANSPLANTS.md | Content Strategist | Fresh format ideas |
| docs/CONTENT_GAPS.md | Content Strategist, Marketing Director | Where the white space is |
```

**After both files are written:** Push all output files to your repo via the GitHub MCP tool.

---

## Research Protocol (All Agents)

**Quality over quantity:** Write precisely to the template. Do not add extra sections. Do not add commentary outside the format. The templates are designed to be read by other AI agents — structure matters.

**Search approach:**
- Start broad, narrow progressively
- Read `config/niche.md` for exact keywords, topics, and tools to search
- Use multiple angles: Google `site:linkedin.com`, Reddit, YouTube search, trade publications
- **YouTube is explicitly permitted** — search, read titles/descriptions/comments/transcripts
- Cross-reference: if multiple sources confirm the same creator or pattern, weight it higher
- Flag uncertainty explicitly rather than assert confidence you don’t have

**2026 engagement signals to look for:**
- Comments with substance (not "great post!") — the real signal
- Saves and shares — harder to find but look for mentions of "saved this" in comments
- Carousel/document format with multiple slides — high dwell time by design
- Posts where people reply with personal stories — deep resonance signal
- Posts where people tag colleagues — viral within organisations signal

**Lookback window:**
- Engagement data: last 3-4 weeks only — older posts have incomplete signals
- Creator style/approach: can go back 6-12 months to understand their content DNA
- YouTube: no strict window — view counts and comment depth are the signals regardless of age

**What to skip:**
- Mega-influencers 500k+ followers
- Generic business content that mentions the niche once
- Non-English content unless directly relevant
- Posts with only likes but no comments or saves — algorithm hasn’t validated them
- Anything obviously AI-generated without real practitioner perspective

**Save progressively:** Write to output files as you complete sections — don’t hold everything in memory until the end.

---

## File Handoff Map

| Agent | Writes | Reads first |
|---|---|---|
| Niche Creator Researcher | `config/watchlist.md` | `config/niche.md` — runs first |
| Niche Content Performance Analyst | `agents/writer/references/post-examples.md` | `config/watchlist.md` — waits for Niche Creator Researcher |
| Cross-Market Content Researcher | `docs/CROSS_NICHE_TRANSPLANTS.md` | `config/niche.md` — runs parallel to Niche Creator Researcher |
| Lead Agent | `docs/CONTENT_GAPS.md`, `docs/INITIAL_RESEARCH_REPORT.md` | All three agent outputs + `config/niche.md` + `config/voice.md` |

---

## How to Run This Session

See `agents/part-time/HOW_TO_RUN.md` for step-by-step instructions.

---

## When to Run Again

- **Initial run:** Now — before Full-Time agents go live
- **Quarterly refresh:** Every 3 months — niche evolves, new creators emerge, algorithm changes
- **Trigger for early refresh:** If engagement drops significantly after 6-8 weeks of running, run the Niche Content Performance Analyst standalone to update post-examples.md
- **Do NOT run daily or weekly** — Agent Teams cost ~15x normal tokens. The Full-Time Niche Content Researcher handles ongoing weekly scanning.
