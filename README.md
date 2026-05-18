# ClawAudit

**ClawAudit** is a local-first autonomy auditor for OpenClaw workspaces.

It scans the parts of OpenClaw that can make an assistant act on its own — workspace instructions, heartbeat, cron jobs, hooks, skills, and config — then produces a safety/reliability report for unattended automations.

## Why this exists

OpenClaw can run background jobs, heartbeat checks, hooks, standing orders, and skills. That is powerful, but once automations pile up it becomes hard to answer simple questions:

- What can my agent do without me asking again?
- Which jobs may fail silently?
- Are there external/destructive actions without approval gates?
- Is heartbeat doing work that should be cron?
- Which skills expand the agent's tool/action surface?

ClawAudit gives a readable first-pass answer without executing anything.

## Current MVP features

- Read-only local scan
- Safety score and reliability score
- Markdown and JSON reports
- Local SQLite audit history
- Searchable previous runs with before/after diffs
- Streamlit dashboard
- Checks for:
  - missing key workspace files
  - vague standing orders
  - missing approval/escalation language
  - noisy heartbeat instructions
  - possible secrets in workspace files
  - cron jobs without failure alerts
  - duplicate cron schedules
  - silent agent-turn cron jobs
  - hooks with weak guardrail language
  - local skills that mention risky capability keywords
  - config signals such as permissive exec approval wording

## Project location

```bash
~/[projects]/clawaudit
```

## Setup

```bash
cd ~/[projects]/clawaudit
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run the CLI audit

```bash
clawaudit audit --workspace ~/.openclaw/workspace --gateway-home ~/.openclaw --out reports
```

Outputs:

- `reports/AUTONOMY_AUDIT.md`
- `reports/autonomy_audit.json`

## Run the dashboard

```bash
streamlit run streamlit_app.py --server.port 8502
```

Then open:

```text
http://127.0.0.1:8502
```

## Run the API bridge

```bash
uvicorn clawaudit.api:app --reload --port 8765
```

Endpoints:

- `GET /health`
- `POST /api/audit/run`
- `GET /api/audit/latest`
- `GET /api/audit/report/markdown`
- `GET /api/audit/report/json`
- `GET /api/history/runs`
- `GET /api/history/runs/{run_id}`
- `GET /api/history/runs/{run_id}/diff`
- `POST /api/history/search`

History is stored locally at:

```text
~/.openclaw/clawaudit/history.sqlite
```

## Run the frontend

The polished frontend lives in `frontend/` and consumes the local API bridge.

```bash
cd frontend
npm install
npm run dev
```

Then open:

```text
http://127.0.0.1:3000
```

Optional API override:

```bash
NEXT_PUBLIC_CLAWAUDIT_API=http://127.0.0.1:8765 npm run dev
```

## Documentation

- [How it works](docs/HOW_IT_WORKS.md)
- [Audit rules](docs/AUDIT_RULES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Frontend plan](docs/FRONTEND_PLAN.md)

## Important limitations

ClawAudit is a static analyzer. It does not execute OpenClaw jobs, inspect live task state, or replace OpenClaw's built-in config/status tools. It is meant as a fast local safety review before trusting automations unattended.
