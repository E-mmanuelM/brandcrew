# Posting Schedule

> **This file is ready to go.** Default schedule is set for US Eastern time, Monday–Friday posting.
> Adjust the timezone and times to match yours when you're ready.

---

## Your Timezone

timezone: America/New_York

<!-- Change to your timezone. Examples: America/Los_Angeles, Europe/London, Asia/Tokyo, Australia/Sydney -->

## Posting Days

posting_days: Monday, Tuesday, Wednesday, Thursday, Friday

## Weekly Planning Day

planning_day: Sunday

## Planning Time (your local time)

planning_time: 4:00 PM

<!-- When the Sunday research + ideation cycle starts -->

## Daily Posting Time (your local time)

posting_time: 12:00 PM

<!-- When the Writer Agent fires each posting day -->
<!-- Recommendation: Mid-morning in your audience's timezone for LinkedIn visibility -->

## Number of Ideas Per Week

ideas_per_week: 10

<!-- How many content ideas the Strategist generates on Sunday. You pick your favorites. -->

## Posts Per Week

posts_per_week: 5

---

## How the Schedule Works

1. **Sunday** — Research Agent scans your niche → Strategist generates 10 ideas → sends to Telegram
2. **Sunday evening** — You pick 5 ideas via Telegram (or however many you want)
3. **Monday–Friday** — Writer Agent picks one approved idea per day, drafts a post, sends for approval
4. **After you approve** — Designer Agent creates the image → you approve → ready to post on LinkedIn

The system converts these times to UTC for cron jobs based on your timezone setting above.
