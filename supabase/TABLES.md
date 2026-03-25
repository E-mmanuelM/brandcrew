# Database Guide — BrandCrew

---

## What This File Is
Plain-English explanation of every table in the database.
Who writes to it, who reads from it, and why it exists.

Run `supabase/schema.sql` in your Supabase SQL Editor to create all tables.

---

## HOW DATA FLOWS THROUGH THE SYSTEM

```
Research Agent
    → writes to: research_topics

Content Strategist (Ideation Agent)
    → reads from: research_topics
    → writes to: content_ideas

Writer Agent
    → reads from: content_ideas (picks oldest approved idea)
    → writes to: content_drafts (status: draft)

Quality Agent
    → reads from: content_drafts
    → writes to: content_drafts (updates status: passed or failed)

You (via Telegram)
    → approves/rejects → content_drafts (status: approved or rejected)

Social Media Designer
    → reads from: content_drafts (approved)
    → renders template → updates image_url
    → writes to: content_drafts (status: finalized)

You (manual LinkedIn post)
    → /get_post → content_drafts (posted: true)
```

---

## TABLES

---

### research_topics
**Written by:** Research Agent (runs weekly on Sunday)
**Read by:** Content Strategist

What it stores: Trending topics the Research Agent finds each week.
Each row is one topic candidate — the agent finds 5-10 per run.

| Column | What it means |
|---|---|
| id | Unique ID for this topic |
| topic | The topic in plain text |
| source_url | Where it was found (LinkedIn post, article, etc) |
| relevance_score | 1-10 — how relevant to your niche |
| engagement_signal | Why this is trending right now |
| created_at | When it was found |
| used | Has this topic been turned into a post yet? |

---

### content_ideas
**Written by:** Content Strategist (Ideation Agent)
**Read by:** Writer Agent

What it stores: The 10 content ideas generated each Sunday.
Each row is one idea — tied back to the research topic that inspired it.

| Column | What it means |
|---|---|
| id | Unique ID for this idea |
| research_topic_id | Which research topic inspired this idea |
| hook | The potential first line of the post |
| angle_description | One sentence explaining the angle |
| relevance_score | 1-10 — how strong this idea is |
| selected | Was this idea approved by you via Telegram? |
| created_at | When it was generated |

---

### content_drafts
**Written by:** Writer Agent, Quality Agent, Social Media Designer, you (via Telegram)
**Read by:** Quality Agent, Social Media Designer, Dashboard, Analytics Agent

What it stores: Every post draft and its full journey through the pipeline.
This is the most important table — it tracks every post from idea to published.

| Column | What it means |
|---|---|
| id | Unique ID for this draft |
| content_idea_id | Which idea this draft came from |
| draft_text | The full post text |
| quality_score | Total score out of 50 from Quality Agent |
| quality_breakdown | JSON — individual scores for each category |
| status | Where the post is in the pipeline (see below) |
| rejection_reason | Why it failed quality check (if it did) |
| retry_count | How many times Writer Agent has retried |
| image_prompt | Legacy — text prompt for image generation |
| image_url | Path to the rendered image file |
| template_name | Which HTML template was used for the image |
| template_vars | JSON — the variables passed to the template |
| posted | Has this finalized post been retrieved via /get_post? |
| created_at | When first drafted |
| updated_at | Last time anything changed |

**Status values explained:**
- `draft` — just written by Writer Agent, not yet scored
- `passed` — passed Quality Agent, sent to Telegram for your review
- `failed` — failed Quality Agent, sent back to Writer to retry
- `approved` — you approved the text in Telegram, image being generated
- `rejected` — you rejected it in Telegram, discarded
- `finalized` — both text and image approved, ready to post
- `published` — you posted it on LinkedIn

---

### agent_logs
**Written by:** Every agent, every time it runs
**Read by:** Dashboard, Marketing Director, you (for debugging)

What it stores: A record of everything every agent does.
If something breaks, this is where you look first.

| Column | What it means |
|---|---|
| id | Unique ID for this log entry |
| agent_name | Which agent ran (research, writer, quality, etc) |
| action | What it did ("searched for topics", "draft saved", etc) |
| status | success or error |
| details | JSON — any extra info (how many topics found, scores, errors) |
| output_summary | Path to output file if applicable |
| started_at | When the agent started |
| completed_at | When the agent finished |
| created_at | When the log row was created |

---

## PHASE 2+ TABLES

These are created by the schema but only used when the system matures:

| Table | Purpose |
|---|---|
| ip_library | Your real expertise — case studies, frameworks, opinions |
| published_posts | Tracks performance of published posts (impressions, engagements) |
| repurposed_content | X/Twitter threads, Substack versions, video scripts |
| analytics_insights | Weekly performance summaries from Analytics Agent |

---

## QUICK REFERENCE

| I want to know... | Look in... |
|---|---|
| What topics were researched this week | research_topics — filter by created_at |
| What ideas were generated | content_ideas — filter by created_at |
| What posts are waiting for my approval | content_drafts — filter status = 'passed' |
| What posts are ready to publish | content_drafts — filter status = 'finalized' AND posted = false |
| What posts have been published | content_drafts — filter posted = true |
| Why an agent failed | agent_logs — filter by agent_name + status = 'error' |
| What a post scored in quality | content_drafts — quality_score + quality_breakdown |
