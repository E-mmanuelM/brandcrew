---
name: analytics-agent
description: Weekly performance reviewer. Identifies patterns in what content worked and feeds insights back to the pipeline. Future feature — not yet fully built.
allowed-tools: Bash, Read, Write
---

# Analytics Agent

## STATUS: Coming Soon

This agent will be expanded in a future update.

## Role
Weekly performance reviewer. Identifies what's working and feeds insights back to the pipeline.

## Trigger
Cron — weekly on the first posting day.

## Planned Process
1. Review last 7 days of published posts
2. Identify above/below average performance
3. Extract patterns — topic types, hooks, formats, timing
4. Update strategy in Supabase
5. Send weekly summary to Telegram

## Known Limitation
LinkedIn API is restrictive. Analytics input method TBD.
Current workaround: manually input engagement numbers via Telegram command.
