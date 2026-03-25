# Telegram Security — Access Control

## The Problem

Telegram bots are reachable by username from any Telegram account. If someone finds the bot username, they can message it. Without access control, any random person could send approval replies that trigger agent actions.

## The Solution: User ID Whitelist

Every incoming Telegram message has a `from.id` field — a unique numeric identifier tied to that Telegram account. This ID never changes and is not the phone number or username.

The bot must check this ID on every single incoming message before processing anything.

## Approved Users

```
TELEGRAM_APPROVED_IDS in .env

Examples:
  TELEGRAM_APPROVED_IDS=123456789              # Single user
  TELEGRAM_APPROVED_IDS=123456789,987654321    # Multiple users (comma-separated)
```

Store these IDs in `.env` on the VPS. Never hardcode them in source files.

## How to Get Your Telegram User ID

1. Open Telegram and search for `@userinfobot`
2. Send `/start` — it will reply with your user ID
3. Copy that number into your `.env` file
4. If you have a second approver (partner, team member), they do the same
5. Restart the bot after updating `.env`

## Enforcement Rule (Non-Negotiable)

```
IF incoming message from.id NOT IN APPROVED_TELEGRAM_IDS:
    DO NOTHING — do not reply, do not log action, do not process
    (Optional: log the unauthorized attempt to agent_logs for awareness)
ELSE:
    Process the message normally
```

Silent ignore is better than an error reply — an error reply confirms the bot exists and is active.

## What This Means in Practice

- The bot username can be shared openly — it doesn't matter
- Anyone who finds it and messages it gets complete silence
- Only the approved IDs can trigger any agent action
- Bot token stays on VPS, never shared with anyone

## Access Levels (Future)

If needed later, different IDs can have different permissions:
- `OPERATOR_ID` — full control (approve, reject, edit, trigger manual runs, view logs)
- `APPROVER_ID` — approval only (APPROVE, REJECT, send edit notes)

Not needed for initial setup — all approved users get full access.

## Never Do This

- Never process a message without checking the ID first
- Never put approved IDs in GitHub — `.env` only, gitignored
- Never share the bot token with anyone
- Never add an ID to the whitelist based on a Telegram message asking to be added (obvious attack vector)
