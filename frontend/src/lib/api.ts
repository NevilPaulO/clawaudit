import type { AuditReport, HistoryDiff, HistoryRun } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_CLAWAUDIT_API ?? "http://127.0.0.1:8765";

export async function getLatestAudit(): Promise<AuditReport> {
  const response = await fetch(`${API_BASE}/api/audit/latest`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load latest audit: ${response.status}`);
  }
  return response.json();
}

export async function runAudit(workspace?: string, gatewayHome?: string): Promise<AuditReport> {
  const response = await fetch(`${API_BASE}/api/audit/run`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ workspace, gateway_home: gatewayHome }),
  });
  if (!response.ok) {
    throw new Error(`Failed to run audit: ${response.status}`);
  }
  return response.json();
}

export async function getMarkdownReport(): Promise<string> {
  const response = await fetch(`${API_BASE}/api/audit/report/markdown`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load markdown report: ${response.status}`);
  }
  const data = await response.json();
  return data.markdown;
}

export async function getHistoryRuns(limit = 20, dateFrom?: string, dateTo?: string): Promise<HistoryRun[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  const response = await fetch(`${API_BASE}/api/history/runs?${params.toString()}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load history: ${response.status}`);
  }
  const data = await response.json();
  return data.runs;
}

export async function searchHistory(query: string, limit = 10, dateFrom?: string, dateTo?: string): Promise<HistoryRun[]> {
  const response = await fetch(`${API_BASE}/api/history/search`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ query, limit, date_from: dateFrom || null, date_to: dateTo || null }),
  });
  if (!response.ok) {
    throw new Error(`Failed to search history: ${response.status}`);
  }
  const data = await response.json();
  return data.results;
}

export async function getHistoryDiff(runId: number): Promise<HistoryDiff> {
  const response = await fetch(`${API_BASE}/api/history/runs/${runId}/diff`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load history diff: ${response.status}`);
  }
  return response.json();
}
