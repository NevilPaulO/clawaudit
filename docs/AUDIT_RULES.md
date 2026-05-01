# Audit Rules

This document explains the current ClawAudit MVP rules.

Rules are intentionally conservative. A finding means "review this", not always "this is broken".

## Severity levels

| Severity | Meaning |
| --- | --- |
| `critical` | Strong evidence of unsafe/unreliable autonomy. Not used yet in MVP rules. |
| `high` | Review before trusting unattended automation. |
| `warn` | Likely cleanup or reliability issue. |
| `info` | Useful context or optional hardening. |

## Workspace rules

### Missing AGENTS.md / HEARTBEAT.md

Flags missing key workspace files.

Why: these files define long-lived behavior and proactive checks.

### Possible secret-like value

Looks for inline `api_key`, `token`, `secret`, or `password` assignments with long values in workspace files.

Why: workspace files are frequently loaded into prompts. Secrets should not live there.

### Standing orders are not explicit

Checks whether `AGENTS.md` contains obvious authority/trigger/program markers.

Why: autonomous programs should define scope, trigger, approval gate, and escalation rules.

### Actions without approval language

Looks for action verbs such as send, delete, post, trade, transfer, restart, deploy, commit, push, etc. without approval/confirmation wording.

Why: external, destructive, public, financial, or infrastructure actions need human gates unless intentionally pre-authorized.

### Standing orders lack escalation language

If authority-like language exists but escalation/failure language is missing, ClawAudit flags it.

Why: autonomy needs stop conditions.

## Heartbeat rules

### Heartbeat may be noisy

Flags active-looking heartbeat content without silence wording such as `HEARTBEAT_OK`, `NO_REPLY`, `stay quiet`, or `only alert`.

Why: heartbeat should not spam the user when nothing changed.

### Heartbeat may contain precise scheduling work

Looks for exact timing language in HEARTBEAT.md.

Why: exact schedules usually belong in cron, while heartbeat is better for flexible periodic awareness.

### Heartbeat too large

Flags heartbeat files with many active lines.

Why: large heartbeat prompts waste tokens and become unfocused.

## Config rules

### Config unreadable

Flags missing/unreadable strict JSON config.

Why: MVP parser currently reads strict JSON only. OpenClaw may support richer config formats, so this is informational.

### Exec approval may be permissive

Looks for config text implying exec approvals with `ask=off`.

Why: unattended command execution should be reviewed carefully.

## Cron rules

### Cron jobs file missing or unreadable

Flags absent/unparseable `~/.openclaw/cron/jobs.json`.

Why: useful context. If cron is not used, this is harmless.

### Cron job has no failure alert

Flags enabled cron jobs without `failureAlert` or `delivery.failureDestination`.

Why: background jobs should not fail silently.

### Agent-turn cron job is fully silent

Flags agent-turn cron jobs with `delivery.mode=none`.

Why: silent jobs can be fine, but should have logs/failure alerts.

### Cron job is coupled to chat context

Flags shared/current-session agent-turn jobs.

Why: isolated jobs are more repeatable unless continuity is intentionally needed.

### Many enabled cron jobs

Flags more than eight enabled jobs.

Why: many jobs can create cost, noise, and overlap.

### Duplicate cron schedule

Flags multiple jobs with identical schedule objects.

Why: jobs may burst together or duplicate work.

## Hooks rules

### Message hook lacks approval language

Flags hooks that listen to inbound messages without obvious guardrail wording.

Why: message-triggered automation should clearly define what it can do and when it escalates.

### Hook action behavior lacks escalation language

Flags hooks that mention action verbs without failure/escalation wording.

Why: lifecycle/message hooks need retry/failure/user notification behavior.

## Skills rules

### Skill may expand autonomous capability

Flags local skills that mention risky capability keywords such as shell, command, browser, send, delete, publish, trade, wallet, or transfer.

Why: skills teach the agent how to use tools. Third-party/local skills should be reviewed before broad use.

## Future rule ideas

- Parse OpenClaw JSONC/includes more accurately.
- Read live `openclaw cron list` output as optional evidence.
- Detect channel allowlists and mention/no-mention behavior.
- Add cost/rate-limit risk checks.
- Add proposed patch generation with explicit approval.
- Add rule suppression comments for accepted risks.
