# Frontend Plan: ClawAudit Pro UI

## Decision

Keep the current **Streamlit dashboard** working as the fast Python-native MVP/admin UI, and add a separate polished **Next.js frontend** for the modern product UI.

Nevil mentioned Nuxt, but the linked MCP documentation is for **Next.js**. This plan assumes **Next.js App Router**. If Nuxt is required later, the same backend/API contract can be reused with a Vue/Nuxt frontend.

## Goals

1. Keep the Python app working exactly as it is.
2. Keep Streamlit available at `streamlit_app.py` for quick local use.
3. Add a modern frontend with:
   - Next.js App Router
   - Tailwind CSS
   - shadcn/ui components
   - Motion.dev animations
   - Next.js MCP support for agent-assisted development
   - shadcn MCP support for component discovery/install
4. Use the existing Python audit engine as the source of truth.
5. Avoid duplicating audit logic in JavaScript.

## Documentation checked

### Next.js MCP

Source: `https://nextjs.org/docs/app/guides/mcp`

Key points:

- Requires Next.js 16+.
- Add `next-devtools-mcp` to project `.mcp.json`.
- MCP lets coding agents inspect routes, page metadata, runtime errors, logs, and dev server state.
- Useful tools include `get_errors`, `get_logs`, `get_routes`, `get_page_metadata`, and `get_project_metadata`.

Planned config:

```json
{
  "mcpServers": {
    "next-devtools": {
      "command": "npx",
      "args": ["-y", "next-devtools-mcp@latest"]
    }
  }
}
```

### shadcn/ui MCP

Source: `https://ui.shadcn.com/docs/mcp`

Key points:

- MCP server lets agents browse/search/install shadcn registry components.
- Configure in `.mcp.json` with `npx shadcn@latest mcp`.
- Uses `components.json` registries.
- Standard shadcn/ui registry works without extra registry config.

Planned combined `.mcp.json`:

```json
{
  "mcpServers": {
    "next-devtools": {
      "command": "npx",
      "args": ["-y", "next-devtools-mcp@latest"]
    },
    "shadcn": {
      "command": "npx",
      "args": ["shadcn@latest", "mcp"]
    }
  }
}
```

### Tailwind CSS with Next.js

Source: `https://tailwindcss.com/docs/installation/framework-guides/nextjs`

Key points:

- Create Next.js project with TypeScript/App Router.
- Install Tailwind/PostCSS packages.
- Import Tailwind in `app/globals.css`.

### Motion.dev

Source: `https://motion.dev/docs`

Key points:

- Motion supports React, JavaScript, and Vue.
- Good fit for layout animations, scroll animations, SVG animation, and timeline effects.
- For Next.js, use React Motion APIs in client components.

## Proposed architecture

```text
clawaudit/
├── src/clawaudit/             # existing Python audit engine
├── streamlit_app.py           # existing MVP/admin dashboard, keep working
├── frontend/                  # new Next.js polished UI
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   ├── .mcp.json
│   ├── components.json
│   └── package.json
└── api/ or src/clawaudit/api.py # FastAPI bridge, optional but recommended
```

## Backend/API approach

Add a thin **FastAPI** API around the existing scanner.

Why:

- Streamlit can continue importing Python directly.
- Next.js can call HTTP endpoints.
- Audit logic remains in one place.
- Future desktop/cloud deployment becomes easier.

Recommended endpoints:

```text
GET  /health
POST /api/audit/run
GET  /api/audit/latest
GET  /api/audit/report/markdown
GET  /api/audit/report/json
```

Example response shape:

```json
{
  "workspace": "/Users/user/.openclaw/workspace",
  "gateway_home": "/Users/user/.openclaw",
  "safety_score": 96,
  "reliability_score": 96,
  "stats": {},
  "items": [],
  "findings": []
}
```

## Frontend screens

### 1. Dashboard overview

Hero section:

- App name: ClawAudit
- Subtitle: "Preflight checks for OpenClaw autonomy"
- Current workspace path
- Run audit button

Cards:

- Safety score
- Reliability score
- Findings count
- Inventory count

Visuals:

- Animated score ring
- Severity donut chart
- Risk by area bar chart
- "What needs attention" panel

### 2. Findings page

Filterable table/cards:

- severity
- area
- title
- recommendation
- evidence

Interactions:

- expand finding details
- copy recommendation
- export selected findings

### 3. Inventory page

Shows discovered autonomy surfaces:

- workspace files
- config
- cron jobs
- hooks
- skills

Future visual:

- graph view of relationships between automations

### 4. Reports page

- Markdown preview
- JSON preview
- download buttons
- copy-to-clipboard

### 5. Settings page

- workspace path
- gateway home path
- API URL
- scan mode: static / live later

## UI style direction

Theme: **dark, technical, premium, OpenClaw-native**.

Visual language:

- dark navy/black background
- glass cards
- cyan/blue highlights
- amber warning states
- red high-risk states
- subtle lobster/OpenClaw accent
- clean rounded shadcn components

Suggested color tokens:

```text
background: #050609
surface:    #0f172a
surface-2:  #111827
primary:    #38bdf8
accent:     #8b5cf6
success:    #22c55e
warning:    #fbbf24
danger:     #fb7185
text:       #f8fafc
muted:      #94a3b8
```

## shadcn/ui components to use

Core:

- `button`
- `card`
- `badge`
- `tabs`
- `table`
- `dialog`
- `sheet`
- `accordion`
- `alert`
- `progress`
- `separator`
- `scroll-area`
- `tooltip`
- `dropdown-menu`
- `command`

Optional later:

- chart components if using shadcn charts/Recharts
- sonner/toast for scan completion

## Animation plan with Motion.dev

Use animation tastefully, not gimmicky.

### Entry animations

- Hero fades/slides in.
- Score cards stagger in.
- Findings cards animate on filter changes.

### Score animation

- Safety score ring counts up from 0 to current score.
- Reliability score uses a softer delayed animation.

### Risk cards

- High-risk cards pulse once when audit finishes.
- Hover lift effect on all cards.

### Page transitions

- Use subtle opacity/y transitions between major tabs/pages.

### Future graph animation

- Automation map nodes gently appear with connecting lines.

## Recommended libraries

Frontend:

```text
next
react
react-dom
typescript
tailwindcss
@tailwindcss/postcss
shadcn/ui CLI components
motion
lucide-react
recharts or visx
zod
```

Backend:

```text
fastapi
uvicorn
```

Keep Plotly only for Streamlit unless we decide to reuse Plotly in frontend. For Next.js, Recharts or visx will feel more native with shadcn.

## Implementation phases

### Phase 1 — API bridge

- Add FastAPI dependency.
- Add `src/clawaudit/api.py`.
- Expose audit run/latest/report endpoints.
- Add CLI docs for running API:

```bash
uvicorn clawaudit.api:app --reload --port 8765
```

Acceptance criteria:

- Streamlit still works.
- CLI still works.
- `GET /health` returns OK.
- `POST /api/audit/run` returns current audit JSON.

### Phase 2 — Next.js frontend scaffold

Create `frontend/` without touching Streamlit.

- Next.js App Router + TypeScript.
- Tailwind installed.
- shadcn initialized.
- `.mcp.json` with Next.js and shadcn MCP servers.
- API client in `frontend/lib/api.ts`.

Acceptance criteria:

- `npm run dev` starts.
- Home page loads.
- App can fetch `/health` from Python API.

### Phase 3 — UI MVP

Build:

- Overview page
- Score cards
- Run audit button
- Findings list
- Inventory list
- Export buttons

Acceptance criteria:

- Uses real ClawAudit API data.
- Dashboard matches or exceeds current Streamlit functionality.
- Responsive at laptop and mobile widths.

### Phase 4 — Polish and animations

Add:

- Motion score animation
- card stagger animation
- tabs/page transitions
- risk severity visual system
- improved empty/loading/error states

Acceptance criteria:

- Animations feel smooth and restrained.
- No layout jank.
- Reduced-motion users get minimal animation.

### Phase 5 — Advanced visuals

Add:

- risk heatmap
- "today's automation timeline" when cron data exists
- autonomy surface graph
- suggested fix preview panel

Acceptance criteria:

- Users can understand automation risk in under 30 seconds.

## Development commands

Planned Python API:

```bash
cd ~/projects/python_projects/clawaudit
source .venv/bin/activate
uvicorn clawaudit.api:app --reload --port 8765
```

Current Streamlit UI:

```bash
cd ~/projects/python_projects/clawaudit
source .venv/bin/activate
streamlit run streamlit_app.py --server.port 8502
```

Future Next.js UI:

```bash
cd ~/projects/python_projects/clawaudit/frontend
npm run dev
```

## Important compatibility rule

The existing app must keep working:

- `clawaudit audit ...` must continue to generate reports.
- `streamlit run streamlit_app.py` must continue to work.
- The Next.js UI must consume the Python audit API instead of replacing the Python scanner.

## Recommendation

Build the frontend in this order:

1. FastAPI bridge
2. Next.js scaffold
3. shadcn layout/components
4. real audit API integration
5. Motion polish
6. advanced automation map

This gives us a professional UI without sacrificing the current working Python/Streamlit MVP.
