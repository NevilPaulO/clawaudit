# ClawAudit Frontend

Modern Next.js dashboard for the ClawAudit Python audit engine.

## Stack

- Next.js 16 App Router
- TypeScript
- Tailwind CSS
- shadcn/ui-style local components
- Motion.dev animations
- Recharts visualizations
- Next.js MCP + shadcn MCP config in `.mcp.json`

## Run

Start the Python API first:

```bash
cd ~/projects/python_projects/clawaudit
source .venv/bin/activate
uvicorn clawaudit.api:app --reload --port 8765
```

Then start the frontend:

```bash
cd ~/projects/python_projects/clawaudit/frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

## API

Default API base:

```text
http://127.0.0.1:8765
```

Override with:

```bash
NEXT_PUBLIC_CLAWAUDIT_API=http://127.0.0.1:8765 npm run dev
```

## Support page

Set your PayPal donation link with:

```bash
NEXT_PUBLIC_PAYPAL_DONATE_URL=https://www.paypal.com/donate/?hosted_button_id=YOUR_BUTTON_ID
```

Then visit:

```text
http://127.0.0.1:3000/support
```

## Verification

```bash
npm run lint
npm run build
npm run test:web
```
