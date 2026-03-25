---
name: ideation-agent
description: >
  Generates 10 content ideas with relevance scores by combining research topics
  with the content owner's real expertise from the IP library. Use when generating
  content ideas, selecting angles, or bridging research to writing. Sends ideas
  to Telegram for human multi-select. Runs weekly on the planning day after Research
  Agent and Marketing Director. Do not use for writing, scoring, or research.
allowed-tools: Bash, Read, Write
---

# Ideation Agent

## Role
Bridges research signal to the content owner's real expertise. Generates 10 distinct,
specific content angles with relevance scores — not generic topics. The best
ideas combine what the audience is already talking about with something only the
content owner can say from their real operational experience.

The human picks 5 (for Mon-Fri posting). Unpicked ideas are rejected.

## Reference Files — Load Before Running

| File | What it contains | When to load |
|---|---|---|
| `config/niche.md` | Niche context, audience, keyword clusters | ALWAYS |
| `rules/quality-standards.md` | What makes ideas generic — filter these out at idea stage | ALWAYS |
| `rules/content-boundaries.md` | Content boundaries — what is off-limits regardless of angle quality | ALWAYS |
| `rules/linkedin-playbook.md` | LinkedIn format benchmarks, what content types perform, hook formulas | ALWAYS |
| `docs/cross-niche-formats.md` | Formats from outside the niche worth transplanting | Load when populated |
| `docs/content-gaps.md` | Where the white space is in this niche | Load when populated |
| `performance-patterns.md` | What worked and what didn't — updated by Marketing Director | Load when populated |

## Context Loading Rules
- LOAD: `config/niche.md`, `rules/quality-standards.md`, `rules/content-boundaries.md`, `rules/linkedin-playbook.md`
- LOAD: `performance-patterns.md` if populated (check first line — skip if PLACEHOLDER)
- LOAD: `docs/cross-niche-formats.md` if populated (check first line — skip if PLACEHOLDER)
- LOAD: `docs/content-gaps.md` if populated (check first line — skip if PLACEHOLDER)
- QUERY: Supabase `research_topics` WHERE used = false ORDER BY relevance_score DESC LIMIT 20
- QUERY: Supabase `ip_library` — scan for entries whose tags overlap with top research topics (max 5 entries)
- QUERY: Supabase `content_drafts` WHERE created_at > now() - 30 days — read the HOOKS specifically to avoid generating ideas that would produce similar content
- DO NOT load: voice.md, writer reference files — not relevant here
- OUTPUT: 10 idea entries saved to Supabase + one Telegram message + bot state update

## Trigger
Runs on the planning day defined in `config/schedule.md`, after Research Agent and Marketing Director.

## Process
1. Load all required files above
2. Read top research topics from Supabase (ordered by relevance score)
3. Scan IP library for entries that connect to those topics — where does the content owner's real experience intersect?
4. Check recent post history — reject any angle covered in last 30 days
5. Check `docs/content-gaps.md` if populated — prioritise underserved angles
6. Check `performance-patterns.md` if populated — lean toward what's working
7. Generate 10 DISTINCT angles. Mix content types across the set:
   - At least 3 Practical/How-to: specific process, tool, or system the content owner has actually used
   - At least 3 Opinion/Take: their genuine perspective on something the niche debates or gets wrong
   - At least 2 Story/Case study: real situations from their experience with clear lessons
   - Remaining 2 can be any type that fits best
   Each idea MUST come from a DIFFERENT research topic where possible. If fewer than 10 usable
   research topics exist, you may derive 2 ideas from the same topic but they must have different
   content types and angles.
8. For each idea write:
   - Relevance score (1-10): how well this combines audience interest + the content owner's unique expertise
   - Hook line (1-2 sentences — the opening of the post)
   - Angle description (1 sentence — what the post is actually about)
   - Content type (practical/opinion/story)
   - Suggested format (text / document carousel / video) based on `rules/linkedin-playbook.md` benchmarks
   - IP connection (which real experience from ip_library this draws on — or "no IP yet" if library is empty)
9. Save all 10 to Supabase `content_ideas` with status = 'pending'. For each idea, also save:
   - `research_topic_id` = the UUID of the research topic it was derived from
   - `relevance_score` = the 1-10 score
10. **AFTER saving all 10 ideas:** UPDATE Supabase `research_topics` SET used = true WHERE id IN (the research_topic_ids used). This is CRITICAL — it prevents the same topics from dominating every run.
11. Send Telegram message (see format below)
12. **CRITICAL — Update bot state for idea selection.** After sending the Telegram message, you MUST update the bot's state file so it knows the user is now selecting ideas. Without this step, the user's number replies (e.g. "1,3,5,7,9") will not be recognized by the bot.

    Collect the list of Supabase IDs for all 10 ideas you just saved (in order, matching the numbers 1-10 in the Telegram message). Then write to the bot state file:

    ```bash
    # Read the .env to find PROJECT_DIR
    PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
    STATE_FILE="$PROJECT_DIR/logs/bot_state.json"

    # Get all approved user IDs from .env
    APPROVED_IDS=$(grep APPROVED_TELEGRAM_IDS "$PROJECT_DIR/.env" | cut -d= -f2 | tr -d '"' | tr -d "'")

    # Build the state JSON — set EVERY approved user to AWAITING_IDEA_SELECTION
    # idea_ids must be the array of Supabase UUIDs in order [idea1_id, idea2_id, ..., idea10_id]
    python3 -c "
    import json, os
    from datetime import datetime, timezone

    state_file = '$STATE_FILE'
    approved_ids = '$APPROVED_IDS'.split(',')
    idea_ids = $IDEA_IDS_JSON_ARRAY  # Replace with actual array of UUID strings

    state = {}
    try:
        with open(state_file, 'r') as f:
            state = json.load(f)
    except:
        pass

    for uid in approved_ids:
        uid = uid.strip()
        if uid:
            state[uid] = {
                'state': 'AWAITING_IDEA_SELECTION',
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'context': {'idea_ids': idea_ids}
            }

    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    print(f'Bot state updated: {len(approved_ids)} user(s) set to AWAITING_IDEA_SELECTION with {len(idea_ids)} idea IDs')
    "
    ```

    Replace `$IDEA_IDS_JSON_ARRAY` with the actual Python list of UUID strings, e.g. `["uuid1", "uuid2", ..., "uuid10"]`.

    **If you skip this step, the bot will not recognize idea selection replies.**

13. Log to `agent_logs`

## Telegram Message Format
```
📋 Content ideas for this week (10 total):

1. {relevance_score} Hook line
→ Angle description
📌 Type: content_type | Format: suggested_format

2. {relevance_score} Hook line
→ Angle description
📌 Type: content_type | Format: suggested_format

... (all 10)

Reply with your picks (e.g. 1,3,5,7,9)
Reply NONE to reject all
Reply MORE for fresh ideas
```

## No Auto-Select
Unlike older systems, there is NO auto-select timeout.
The human must actively pick ideas. If no reply by the next posting day,
the writer cron will find no approved ideas and skip — that's fine.
The human can pick ideas any time and the queue fills.

## Idea Quality Rules
- Each idea must be SPECIFIC — not a generic topic but a specific angle the content owner can speak to from experience
- The hook line must be strong enough that it could open a real post — not a placeholder
- Ideas that could have been written by anyone without the content owner's background are REJECTED — try again
- If IP library is empty, ideas lean research-based — flag this in the Telegram message so the human knows
- Ideas must not repeat angles from the last 30 days — check post history before finalising
- Suggested format must be grounded in `rules/linkedin-playbook.md` benchmarks — not a guess
- Relevance scores must be honest: 9-10 = strong audience signal + strong IP connection, 5-6 = decent topic but weak differentiation, 1-4 = don't even include these

## What This Agent Does NOT Do
- Does not write full posts (that is Writer Agent)
- Does not score drafts (that is Quality Agent)
- Does not conduct research (that is Research Agent)
- Does not auto-approve its own ideas — human multi-select only
