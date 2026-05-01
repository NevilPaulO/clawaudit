export type Severity = "info" | "warn" | "high" | "critical";

export interface Finding {
  id: string;
  title: string;
  severity: Severity;
  area: string;
  detail: string;
  recommendation: string;
  evidence: string[];
}

export interface AuditItem {
  kind: string;
  name: string;
  path?: string | null;
  summary?: string | null;
  metadata: Record<string, unknown>;
}

export interface AuditReport {
  workspace: string;
  gateway_home: string;
  history_run_id?: number;
  safety_score: number;
  reliability_score: number;
  stats: {
    findings_by_severity?: Record<string, number>;
    findings_by_area?: Record<string, number>;
    items_by_kind?: Record<string, number>;
  };
  items: AuditItem[];
  findings: Finding[];
}

export interface HistoryRun {
  id: number;
  created_at: string;
  workspace: string;
  gateway_home: string;
  safety_score: number;
  reliability_score: number;
  finding_count: number;
  item_count: number;
  summary: string;
  score?: number;
}

export interface HistoryDiff {
  run_id: number;
  previous_run_id?: number | null;
  added_findings: Finding[];
  resolved_findings: Finding[];
  changed_findings: Array<{ id: string; before: Finding; after: Finding }>;
}
