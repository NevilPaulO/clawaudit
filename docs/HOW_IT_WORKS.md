# How ClawAudit Works

ClawAudit is a read-only scanner for OpenClaw autonomy surfaces.

It answers three practical questions:

1. **Inventory:** What automation-related files and objects exist?
2. **Risk:** Which patterns look noisy, unsafe, brittle, or under-specified?
3. **Action:** What should the operator fix first?

## Inputs

By default ClawAudit scans:

```text
Workspace:    ~/.openclaw/workspace
Gateway home: ~/.openclaw
```

It currently checks these locations:

```text
~/.openclaw/workspace/AGENTS.md
~/.openclaw/workspace/HEARTBEAT.md
~/.openclaw/workspace/MEMORY.md
~/.openclaw/workspace/TOOLS.md
~/.openclaw/workspace/USER.md
~/.openclaw/workspace/IDENTITY.md
~/.openclaw/openclaw.json
~/.openclaw/cron/jobs.json
~/.openclaw/hooks/*/HOOK.md
~/.openclaw/workspace/hooks/*/HOOK.md
~/.openclaw/workspace/skills/**/SKILL.md
~/.openclaw/workspace/.agents/skills/**/SKILL.md
~/.agents/skills/**/SKILL.md
~/.openclaw/skills/**/SKILL.md
```

## Processing flow

1. Resolve workspace and gateway paths.
2. Read known files if present.
3. Parse strict JSON files where possible.
4. Build an inventory of workspace files, config, cron jobs, hooks, and skills.
5. Run rule checks against text/JSON patterns.
6. Produce findings with severity, area, detail, recommendation, and evidence.
7. Calculate safety and reliability scores.
8. Write Markdown and JSON reports.
9. Optionally render the same data in Streamlit.

## Scores

ClawAudit uses simple weighted penalties:

```text
info     = 1 point
warn     = 4 points
high     = 9 points
critical = 16 points
```

Safety score starts at 100 and subtracts all finding penalties.

Reliability score gives full penalty to operational areas like cron, heartbeat, hooks, and taskflow, and lighter penalty to less operational findings.

The scoring is intentionally simple for MVP. The important part is not the exact number — it is the prioritized finding list.

## Outputs

### Markdown report

`reports/AUTONOMY_AUDIT.md` is designed for humans. It includes:

- executive summary
- scores
- recommended next actions
- inventory counts
- findings grouped by severity
- automation inventory

### JSON report

`reports/autonomy_audit.json` is designed for automation. It includes all report data in structured form.

### Dashboard

The Streamlit dashboard shows:

- score cards
- autonomy score gauge
- severity distribution
- risk by area
- recommended next actions
- filterable findings
- filterable inventory
- downloadable Markdown/JSON reports

## Safety model

ClawAudit is read-only. It does not:

- run cron jobs
- execute hooks
- send messages
- modify workspace files
- patch config
- install skills

Future versions may offer suggested patches, but applying them should remain an explicit operator action.
