import { AuditDashboard } from "@/components/dashboard/audit-dashboard";
import { getLatestAudit } from "@/lib/api";
import { fallbackReport } from "@/lib/fallback-report";

async function loadReport() {
  try {
    return await getLatestAudit();
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not reach the ClawAudit API.";
    return fallbackReport(message);
  }
}

export default async function Home() {
  const report = await loadReport();
  return <AuditDashboard initialReport={report} />;
}
