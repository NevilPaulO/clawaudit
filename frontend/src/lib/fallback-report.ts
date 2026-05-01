import type { AuditReport } from "./types";

export function fallbackReport(errorMessage: string): AuditReport {
  return {
    workspace: "~/.openclaw/workspace",
    gateway_home: "~/.openclaw",
    safety_score: 0,
    reliability_score: 0,
    stats: {
      findings_by_severity: { critical: 1 },
      findings_by_area: { api: 1 },
      items_by_kind: {},
    },
    items: [],
    findings: [
      {
        id: "api-unavailable",
        title: "ClawAudit API is unavailable",
        severity: "critical",
        area: "api",
        detail: errorMessage,
        recommendation: "Start the Python API with: uvicorn clawaudit.api:app --reload --port 8765, then run the audit again.",
        evidence: ["Expected API: http://127.0.0.1:8765"],
      },
    ],
  };
}
