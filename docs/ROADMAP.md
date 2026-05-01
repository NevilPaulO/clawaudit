# Roadmap

## MVP done

- Python CLI core
- Streamlit dashboard
- Markdown/JSON reports
- Workspace/config/cron/hooks/skills scanning
- Basic scoring and recommendations
- Documentation

## Next improvements

### 1. Better OpenClaw config parsing

Current MVP parses strict JSON only. OpenClaw configs may include comments/includes or be better inspected through OpenClaw's own config tooling.

Possible approaches:

- Add JSONC parser support.
- Add optional `openclaw` CLI integration.
- Add a `--live` mode that asks OpenClaw for normalized config.

### 2. Rule suppressions

Allow accepted risks to be documented without disappearing silently.

Example:

```markdown
<!-- clawaudit-disable cron-no-failure-alert reason="Local-only test job" -->
```

### 3. Suggested patches

Generate safe patch suggestions for common issues:

- add heartbeat silence contract
- add standing-order template
- add cron failure alert template
- add escalation wording

Patches should be preview-only unless explicitly applied.

### 4. Automation map

Create a graph of relationships:

```text
Standing order -> cron job -> session target -> delivery channel
Heartbeat -> monitored service -> alert rule
Hook -> event -> handler action
Skill -> tools/capabilities
```

### 5. Live status integration

Optional mode to inspect live OpenClaw state:

- cron list/runs
- tasks list
- hooks check
- status/health

This should be separate from static mode so ClawAudit remains safe and predictable.

### 6. Better dashboard polish

- Animated graph of autonomy surfaces
- Timeline of today's scheduled jobs
- Risk heatmap
- One-click Markdown export card
- Dark/light theme toggle

### 7. Test suite

Add fixtures for:

- clean workspace
- noisy heartbeat
- risky standing orders
- cron duplicates
- risky skills
- possible secrets

Use pytest for scanner and report rendering.

### 8. Packaging

Potential distribution options:

- Python package
- OpenClaw skill wrapper
- ClawHub skill/plugin package
- Homebrew formula later if useful

## Long-term idea

Turn ClawAudit into the "preflight checklist" for OpenClaw operators before they enable 24/7 autonomy.
