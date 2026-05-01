# Architecture

ClawAudit is intentionally small and local-first.

## High-level structure

```text
clawaudit/
├── pyproject.toml
├── requirements.txt
├── README.md
├── streamlit_app.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AUDIT_RULES.md
│   ├── HOW_IT_WORKS.md
│   └── ROADMAP.md
└── src/clawaudit/
    ├── __init__.py
    ├── cli.py
    ├── models.py
    ├── reporting.py
    └── scanner.py
```

## Modules

### `models.py`

Defines core dataclasses:

- `Finding` — one audit issue or observation.
- `AuditItem` — one inventory item discovered by the scan.
- `AuditReport` — complete report with scores, stats, findings, and inventory.

It also contains default path helpers for workspace and gateway home.

### `scanner.py`

The main audit engine.

Responsibilities:

- read workspace files
- parse strict JSON config/cron files
- discover hooks and local skills
- apply rule checks
- build inventory and stats

Scanner functions are split by area:

- `scan_workspace_files`
- `scan_config`
- `scan_cron`
- `scan_hooks`
- `scan_skills`

### `reporting.py`

Turns an `AuditReport` into:

- Markdown report
- JSON report

The Markdown output is meant to be readable in editors, GitHub, Discord snippets, or OpenClaw chats.

### `cli.py`

Defines the command line interface:

```bash
clawaudit audit --workspace ~/.openclaw/workspace --gateway-home ~/.openclaw --out reports
```

The CLI runs a scan and writes reports.

### `streamlit_app.py`

Visual dashboard layer.

It imports the same scanner/reporting code and renders:

- score metrics
- gauge chart
- severity chart
- risk by area
- findings
- inventory
- report downloads

The Streamlit app should stay thin. Business logic belongs in `src/clawaudit`.

## Data model

### Finding

```python
Finding(
    id="cron-no-failure-alert-example",
    title="Cron job has no obvious failure alert",
    severity="warn",
    area="cron",
    detail="...",
    recommendation="...",
    evidence=["..."]
)
```

### Audit item

```python
AuditItem(
    kind="cron_job",
    name="daily-report",
    path="~/.openclaw/cron/jobs.json",
    summary="cron 0 9 * * * · enabled=True · target=isolated",
    metadata={...}
)
```

### Audit report

```python
AuditReport(
    workspace="...",
    gateway_home="...",
    findings=[...],
    items=[...],
    stats={...}
)
```

## Design principles

1. **Read-only by default** — never mutate OpenClaw configuration during audit.
2. **Local-first** — no cloud service required.
3. **Evidence-based** — every finding should point to a file, job, or pattern.
4. **Actionable** — every finding should include a concrete recommendation.
5. **Composable** — CLI core first, UI second.
6. **Operator-controlled** — future auto-fixes should require explicit approval.

## Adding a new rule

1. Choose the correct scan function in `scanner.py`.
2. Add a `Finding` with stable `id`, severity, area, detail, recommendation, and evidence.
3. Prefer `add_finding` to avoid duplicates.
4. Update `docs/AUDIT_RULES.md`.
5. Run:

```bash
python -m compileall -q src streamlit_app.py
clawaudit audit --workspace ~/.openclaw/workspace --out reports
```

## Future architecture options

If ClawAudit grows, split rules into separate modules:

```text
src/clawaudit/rules/workspace.py
src/clawaudit/rules/cron.py
src/clawaudit/rules/hooks.py
src/clawaudit/rules/skills.py
src/clawaudit/rules/config.py
```

If we need a polished public UI, keep this Python package as the audit engine and expose it through FastAPI to a React/Next.js frontend.
