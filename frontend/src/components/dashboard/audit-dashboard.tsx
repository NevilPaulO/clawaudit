"use client";

import Link from "next/link";
import type React from "react";
import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Activity, AlertTriangle, CheckCircle2, Download, FileJson, GitCompare, HeartHandshake, History, Layers3, RefreshCw, Search, ShieldCheck, Sparkles } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { getHistoryDiff, getHistoryRuns, getMarkdownReport, runAudit, searchHistory } from "@/lib/api";
import type { AuditReport, HistoryDiff, HistoryRun, Severity } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScoreRing } from "./score-ring";

const severityColors: Record<Severity, string> = {
  critical: "#ef4444",
  high: "#fb7185",
  warn: "#fbbf24",
  info: "#38bdf8",
};

const severityOrder: Severity[] = ["critical", "high", "warn", "info"];

interface AuditDashboardProps {
  initialReport: AuditReport;
}

export function AuditDashboard({ initialReport }: AuditDashboardProps) {
  const [report, setReport] = useState(initialReport);
  const [workspace, setWorkspace] = useState(initialReport.workspace);
  const [gatewayHome, setGatewayHome] = useState(initialReport.gateway_home);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyQuery, setHistoryQuery] = useState("");
  const [historyDateFrom, setHistoryDateFrom] = useState("");
  const [historyDateTo, setHistoryDateTo] = useState("");
  const [historyRuns, setHistoryRuns] = useState<HistoryRun[]>([]);
  const [historyDiff, setHistoryDiff] = useState<HistoryDiff | null>(null);
  const [completeDialogOpen, setCompleteDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const severityData = useMemo(
    () => severityOrder
      .map((severity) => ({ name: severity, value: report.stats.findings_by_severity?.[severity] ?? 0 }))
      .filter((item) => item.value > 0),
    [report]
  );

  const areaData = useMemo(
    () => Object.entries(report.stats.findings_by_area ?? {}).map(([name, value]) => ({ name, value })),
    [report]
  );

  const topFindings = report.findings.filter((finding) => finding.severity === "critical" || finding.severity === "high");
  const priorityFindings = topFindings.length ? topFindings : report.findings.filter((finding) => finding.severity === "warn").slice(0, 5);

  async function handleRunAudit() {
    setLoading(true);
    setCompleteDialogOpen(false);
    setError(null);
    try {
      const [next] = await Promise.all([runAudit(workspace, gatewayHome), delay(900)]);
      setReport(next);
      setCompleteDialogOpen(true);
      void loadHistory(next.history_run_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run audit");
    } finally {
      setLoading(false);
    }
  }

  async function downloadMarkdown() {
    const markdown = await getMarkdownReport();
    downloadFile("AUTONOMY_AUDIT.md", markdown, "text/markdown");
  }

  function downloadJson() {
    downloadFile("autonomy_audit.json", JSON.stringify(report, null, 2), "application/json");
  }

  async function loadHistory(runId = report.history_run_id) {
    await fetchHistory(runId, historyQuery, historyDateFrom, historyDateTo);
  }

  async function clearHistoryFilters() {
    setHistoryQuery("");
    setHistoryDateFrom("");
    setHistoryDateTo("");
    await fetchHistory(report.history_run_id, "", "", "");
  }

  async function fetchHistory(runId: number | undefined, query: string, dateFrom: string, dateTo: string) {
    setHistoryLoading(true);
    setError(null);
    try {
      const runs = query.trim()
        ? await searchHistory(query.trim(), 12, dateFrom || undefined, dateTo || undefined)
        : await getHistoryRuns(12, dateFrom || undefined, dateTo || undefined);
      setHistoryRuns(runs);
      const selectedRunId = runId ?? runs[0]?.id;
      if (selectedRunId) {
        setHistoryDiff(await getHistoryDiff(selectedRunId));
      } else {
        setHistoryDiff(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load history");
    } finally {
      setHistoryLoading(false);
    }
  }

  return (
    <main className="glass-grid relative min-h-screen overflow-hidden px-4 py-5 text-slate-100 lg:px-8">
      <div className="pointer-events-none absolute left-[-10rem] top-[-10rem] h-96 w-96 rounded-full bg-cyan-400/20 blur-3xl" />
      <div className="pointer-events-none absolute right-[-8rem] top-40 h-[28rem] w-[28rem] rounded-full bg-fuchsia-500/15 blur-3xl" />
      <ScanOverlay open={loading} />
      <CompleteDialog
        open={completeDialogOpen}
        safetyScore={report.safety_score}
        reliabilityScore={report.reliability_score}
        findingCount={report.findings.length}
        onClose={() => setCompleteDialogOpen(false)}
      />
      <div className="mx-auto max-w-6xl space-y-6">
        <nav className="flex items-center justify-between rounded-full border border-white/10 bg-white/[.04] px-5 py-3 backdrop-blur-xl">
          <Link href="/" className="flex items-center gap-2 font-black tracking-tight text-white">
            <span className="grid h-9 w-9 place-items-center rounded-full bg-cyan-300 text-slate-950">🦞</span>
            ClawAudit
          </Link>
          <div className="flex items-center gap-2">
            <Button asChild variant="outline" size="sm">
              <Link href="/support"><HeartHandshake className="h-4 w-4" /> Support</Link>
            </Button>
          </div>
        </nav>
        <motion.section
          className="relative overflow-hidden rounded-[1.75rem] border border-white/10 bg-slate-950/70 p-6 shadow-2xl shadow-black/30 backdrop-blur-xl md:p-7"
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
        >
          <div className="absolute right-10 top-8 hidden text-cyan-300/20 lg:block">
            <Sparkles size={118} />
          </div>
          <div className="absolute bottom-[-7rem] right-24 hidden h-56 w-56 rounded-full border border-cyan-300/20 bg-cyan-300/10 blur-sm lg:block" />
          <Badge variant="default" className="mb-4">OpenClaw autonomy command center</Badge>
          <div className="grid gap-6 lg:grid-cols-[1.15fr_.85fr] lg:items-end">
            <div>
              <h1 className="max-w-3xl text-4xl font-black tracking-tight text-white md:text-6xl">
                Audit your agent before it acts alone<span className="text-cyan-300">.</span>
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
                A cinematic control-room for OpenClaw autonomy. See risks, checks, skills, schedules, and safety signals before trusting unattended automation.
              </p>
            </div>
            <Card className="bg-white/[.06]">
              <CardHeader>
                <CardTitle>Scan target</CardTitle>
                <CardDescription>Choose what to inspect, then run a fresh preflight.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <input className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-slate-100 outline-none ring-cyan-400/40 focus:ring-2" value={workspace} onChange={(event) => setWorkspace(event.target.value)} />
                <input className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-slate-100 outline-none ring-cyan-400/40 focus:ring-2" value={gatewayHome} onChange={(event) => setGatewayHome(event.target.value)} />
                <Button onClick={handleRunAudit} disabled={loading} className="w-full">
                  <RefreshCw className={loading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
                  {loading ? "Running audit..." : "Run audit"}
                </Button>
                {error && <p className="text-sm text-rose-300">{error}</p>}
              </CardContent>
            </Card>
          </div>
        </motion.section>

        <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard icon={<ShieldCheck />} label="Safety" value={`${report.safety_score}/100`} tone={scoreTone(report.safety_score)} />
          <MetricCard icon={<Activity />} label="Reliability" value={`${report.reliability_score}/100`} tone={scoreTone(report.reliability_score)} />
          <MetricCard icon={<AlertTriangle />} label="Findings" value={String(report.findings.length)} tone={topFindings.length ? "danger" : "calm"} />
          <MetricCard icon={<Layers3 />} label="Inventory" value={String(report.items.length)} tone="violet" />
        </section>

        <Tabs defaultValue="overview" className="space-y-5">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="findings">Findings</TabsTrigger>
            <TabsTrigger value="inventory">Inventory</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
            <TabsTrigger value="export">Export</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <div className="grid gap-6 lg:grid-cols-[.85fr_1.15fr]">
              <Card>
                <CardHeader>
                  <CardTitle>Autonomy score</CardTitle>
                  <CardDescription>Live readiness signal for unattended automation.</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col items-center gap-5">
                  <ScoreRing score={report.safety_score} label="safety" />
                  <div className="w-full space-y-2">
                    <div className="flex justify-between text-sm text-slate-400"><span>Reliability</span><span>{report.reliability_score}%</span></div>
                    <Progress value={report.reliability_score} />
                  </div>
                </CardContent>
              </Card>

              <div className="grid gap-6 xl:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Severity mix</CardTitle>
                    <CardDescription>How findings are distributed.</CardDescription>
                  </CardHeader>
                  <CardContent className="h-72 min-w-0">
                    {severityData.length ? (
                      <ResponsiveContainer width="100%" height={260} minWidth={220}>
                        <PieChart>
                          <Pie data={severityData} dataKey="value" nameKey="name" innerRadius={58} outerRadius={90} paddingAngle={4}>
                            {severityData.map((entry) => <Cell key={entry.name} fill={severityColors[entry.name as Severity]} />)}
                          </Pie>
                          <Tooltip contentStyle={{ background: "#020617", border: "1px solid rgba(255,255,255,.12)", borderRadius: 12 }} />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : <EmptyState label="No findings" />}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Risk by area</CardTitle>
                    <CardDescription>Where the audit is focusing.</CardDescription>
                  </CardHeader>
                  <CardContent className="h-72 min-w-0">
                    {areaData.length ? (
                      <ResponsiveContainer width="100%" height={260} minWidth={220}>
                        <BarChart data={areaData} margin={{ left: -25 }}>
                          <CartesianGrid stroke="rgba(255,255,255,.08)" vertical={false} />
                          <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                          <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                          <Tooltip contentStyle={{ background: "#020617", border: "1px solid rgba(255,255,255,.12)", borderRadius: 12 }} />
                          <Bar dataKey="value" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : <EmptyState label="No area risks" />}
                  </CardContent>
                </Card>
              </div>
            </div>

            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Recommended next actions</CardTitle>
                <CardDescription>The highest-value cleanup items first.</CardDescription>
              </CardHeader>
              <CardContent>
                {priorityFindings.length ? (
                  <div className="grid gap-3 md:grid-cols-2">
                    {priorityFindings.map((finding) => <FindingMini key={finding.id} finding={finding} />)}
                  </div>
                ) : (
                  <div className="flex items-center gap-3 rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-emerald-100">
                    <CheckCircle2 className="h-5 w-5" />
                    No urgent action. Review info findings for optional hardening.
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="findings">
            <div className="grid gap-4">
              {report.findings.map((finding, index) => (
                <motion.div key={finding.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.035 }}>
                  <Card className="overflow-hidden">
                    <div className="flex flex-col gap-4 p-5 md:flex-row md:items-start md:justify-between">
                      <div>
                        <div className="mb-2 flex flex-wrap items-center gap-2">
                          <Badge variant={finding.severity}>{finding.severity.toUpperCase()}</Badge>
                          <Badge variant="muted">{finding.area}</Badge>
                        </div>
                        <h3 className="text-xl font-bold text-white">{finding.title}</h3>
                        <p className="mt-2 text-slate-300">{finding.detail}</p>
                        <p className="mt-3 text-sm text-cyan-100"><strong>Fix:</strong> {finding.recommendation}</p>
                      </div>
                      <div className="min-w-0 rounded-2xl border border-white/10 bg-black/20 p-3 text-xs text-slate-400 md:w-80">
                        <div className="mb-2 font-semibold text-slate-200">Evidence</div>
                        {finding.evidence.length ? finding.evidence.map((item) => <div key={item} className="truncate font-mono">{item}</div>) : "None"}
                      </div>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="inventory">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {report.items.map((item, index) => (
                <motion.div key={`${item.kind}-${item.name}-${index}`} initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: index * 0.02 }}>
                  <Card className="h-full">
                    <CardHeader>
                      <div className="flex items-center justify-between gap-3">
                        <Badge variant="muted">{item.kind}</Badge>
                        <Activity className="h-4 w-4 text-cyan-300" />
                      </div>
                      <CardTitle className="break-words">{item.name}</CardTitle>
                      <CardDescription>{item.summary}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="break-all font-mono text-xs text-slate-500">{item.path}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="history">
            <div className="grid gap-6 lg:grid-cols-[1.05fr_.95fr]">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><History className="h-5 w-5 text-cyan-300" /> Audit timeline</CardTitle>
                  <CardDescription>Local saved runs so you can compare what happened before and after.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-3 xl:grid-cols-[1fr_auto]">
                    <input
                      className="min-w-0 rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-slate-100 outline-none ring-cyan-400/40 focus:ring-2"
                      placeholder="Search history, e.g. cron, approval, heartbeat"
                      value={historyQuery}
                      onChange={(event) => setHistoryQuery(event.target.value)}
                      onKeyDown={(event) => { if (event.key === "Enter") void loadHistory(); }}
                    />
                    <Button onClick={() => loadHistory()} disabled={historyLoading}>
                      <Search className={historyLoading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
                      {historyQuery.trim() ? "Search" : "Load history"}
                    </Button>
                  </div>
                  <div className="grid gap-3 rounded-2xl border border-white/10 bg-black/20 p-3 sm:grid-cols-[1fr_1fr_auto]">
                    <label className="space-y-1 text-xs font-semibold text-slate-400">
                      From date
                      <input
                        type="date"
                        className="w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none ring-cyan-400/40 focus:ring-2"
                        value={historyDateFrom}
                        onChange={(event) => setHistoryDateFrom(event.target.value)}
                      />
                    </label>
                    <label className="space-y-1 text-xs font-semibold text-slate-400">
                      To date
                      <input
                        type="date"
                        className="w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none ring-cyan-400/40 focus:ring-2"
                        value={historyDateTo}
                        onChange={(event) => setHistoryDateTo(event.target.value)}
                      />
                    </label>
                    <Button
                      variant="outline"
                      className="self-end"
                      onClick={() => { void clearHistoryFilters(); }}
                    >
                      Clear
                    </Button>
                  </div>
                  {historyRuns.length ? (
                    <div className="space-y-3">
                      {historyRuns.map((run) => (
                        <button
                          key={run.id}
                          type="button"
                          onClick={() => loadHistory(run.id)}
                          className="w-full rounded-2xl border border-white/10 bg-white/[.04] p-4 text-left transition hover:border-cyan-300/40 hover:bg-cyan-300/10"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="font-semibold text-white">Run #{run.id}</div>
                            <Badge variant="muted">{formatDate(run.created_at)}</Badge>
                          </div>
                          <div className="mt-2 grid gap-2 text-sm text-slate-300 sm:grid-cols-3">
                            <span>Safety {run.safety_score}/100</span>
                            <span>Reliability {run.reliability_score}/100</span>
                            <span>{run.finding_count} findings</span>
                          </div>
                          <p className="mt-2 line-clamp-2 text-sm text-slate-400">{run.summary}</p>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <EmptyState label="Load history to see saved audit runs" />
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><GitCompare className="h-5 w-5 text-violet-300" /> Before / after</CardTitle>
                  <CardDescription>What changed compared with the previous saved run.</CardDescription>
                </CardHeader>
                <CardContent>
                  {historyDiff ? (
                    <div className="space-y-4">
                      <DiffGroup title="New findings" findings={historyDiff.added_findings} tone="danger" />
                      <DiffGroup title="Resolved findings" findings={historyDiff.resolved_findings} tone="good" />
                      <div className="rounded-2xl border border-white/10 bg-white/[.04] p-4">
                        <div className="font-semibold text-white">Changed findings</div>
                        <div className="mt-1 text-3xl font-black text-white">{historyDiff.changed_findings.length}</div>
                      </div>
                    </div>
                  ) : (
                    <EmptyState label="Select a saved run to compare" />
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="export">
            <Card>
              <CardHeader>
                <CardTitle>Export report</CardTitle>
                <CardDescription>Download the current audit report.</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-3">
                <Button onClick={downloadMarkdown}><Download className="h-4 w-4" /> Markdown</Button>
                <Button variant="outline" onClick={downloadJson}><FileJson className="h-4 w-4" /> JSON</Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}

function ScanOverlay({ open }: { open: boolean }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 grid place-items-center bg-slate-950/75 px-4 backdrop-blur-md"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          role="status"
          aria-live="polite"
        >
          <motion.div
            className="relative w-full max-w-md overflow-hidden rounded-[2rem] border border-cyan-300/20 bg-slate-950/90 p-7 text-center shadow-2xl shadow-cyan-950/40"
            initial={{ opacity: 0, scale: 0.94, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 10 }}
          >
            <div className="pointer-events-none absolute inset-x-8 top-0 h-24 bg-cyan-300/20 blur-3xl" />
            <div className="relative mx-auto grid h-28 w-28 place-items-center">
              <motion.div
                className="absolute inset-0 rounded-full border border-cyan-300/25"
                animate={{ scale: [1, 1.18, 1], opacity: [0.65, 0.15, 0.65] }}
                transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
              />
              <motion.div
                className="absolute inset-3 rounded-full border-2 border-transparent border-t-cyan-300 border-r-fuchsia-300"
                animate={{ rotate: 360 }}
                transition={{ duration: 1.1, repeat: Infinity, ease: "linear" }}
              />
              <motion.div
                className="absolute inset-7 rounded-full border-2 border-transparent border-b-emerald-300 border-l-cyan-200"
                animate={{ rotate: -360 }}
                transition={{ duration: 1.6, repeat: Infinity, ease: "linear" }}
              />
              <ShieldCheck className="relative h-9 w-9 text-cyan-200" />
            </div>
            <h2 className="mt-5 text-2xl font-black text-white">Scanning your setup</h2>
            <p className="mt-2 text-sm leading-6 text-slate-300">Checking saved instructions, schedules, history, and risk signals. This usually takes a moment.</p>
            <div className="mt-6 h-2 overflow-hidden rounded-full bg-white/10">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-cyan-300 via-fuchsia-300 to-emerald-300"
                initial={{ x: "-100%" }}
                animate={{ x: "100%" }}
                transition={{ duration: 1.15, repeat: Infinity, ease: "easeInOut" }}
              />
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function CompleteDialog({ open, safetyScore, reliabilityScore, findingCount, onClose }: { open: boolean; safetyScore: number; reliabilityScore: number; findingCount: number; onClose: () => void }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 grid place-items-center bg-slate-950/70 px-4 backdrop-blur-md"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="audit-complete-title"
        >
          <motion.div
            className="relative w-full max-w-lg overflow-hidden rounded-[2rem] border border-emerald-300/25 bg-slate-950/95 p-7 text-center shadow-2xl shadow-emerald-950/30"
            initial={{ opacity: 0, scale: 0.9, y: 18 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 10 }}
            transition={{ type: "spring", stiffness: 220, damping: 22 }}
          >
            <div className="pointer-events-none absolute inset-x-10 top-0 h-28 bg-emerald-300/20 blur-3xl" />
            <div className="relative mx-auto grid h-24 w-24 place-items-center rounded-full bg-emerald-300/10">
              <motion.div
                className="absolute inset-0 rounded-full border border-emerald-300/35"
                initial={{ scale: 0.65, opacity: 0 }}
                animate={{ scale: 1.25, opacity: 0 }}
                transition={{ duration: 0.9, repeat: 1 }}
              />
              <motion.div
                className="grid h-16 w-16 place-items-center rounded-full bg-emerald-400 text-slate-950 shadow-lg shadow-emerald-400/25"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.1, type: "spring", stiffness: 260, damping: 16 }}
              >
                <motion.svg width="34" height="34" viewBox="0 0 34 34" fill="none" aria-hidden="true">
                  <motion.path
                    d="M8 17.5l6 6L26.5 10"
                    stroke="currentColor"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ delay: 0.28, duration: 0.45, ease: "easeOut" }}
                  />
                </motion.svg>
              </motion.div>
            </div>
            <h2 id="audit-complete-title" className="mt-5 text-3xl font-black text-white">Audit complete</h2>
            <p className="mt-2 text-sm leading-6 text-slate-300">Your latest scan is saved in history and ready to review.</p>
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              <ResultPill label="Safety" value={`${safetyScore}/100`} />
              <ResultPill label="Reliability" value={`${reliabilityScore}/100`} />
              <ResultPill label="Findings" value={String(findingCount)} />
            </div>
            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
              <Button onClick={onClose}>Review results</Button>
              <Button variant="outline" onClick={onClose}>Close</Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function ResultPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[.04] p-3">
      <div className="text-xs text-slate-400">{label}</div>
      <div className="mt-1 text-xl font-black text-white">{value}</div>
    </div>
  );
}

function MetricCard({ icon, label, value, tone }: { icon: React.ReactNode; label: string; value: string; tone: "good" | "mid" | "danger" | "calm" | "violet" }) {
  const toneClass = {
    good: "from-emerald-400/20 to-cyan-400/10 text-emerald-200",
    mid: "from-amber-400/20 to-cyan-400/10 text-amber-200",
    danger: "from-rose-500/20 to-red-400/10 text-rose-200",
    calm: "from-cyan-400/20 to-sky-400/10 text-cyan-200",
    violet: "from-violet-400/20 to-cyan-400/10 text-violet-100",
  }[tone];

  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
      <Card className={`bg-gradient-to-br ${toneClass}`}>
        <CardContent className="flex items-center justify-between p-4">
          <div>
            <p className="text-sm text-slate-400">{label}</p>
            <p className="mt-1 text-2xl font-black text-white">{value}</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/10 p-2.5">{icon}</div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function scoreTone(score: number): "good" | "mid" | "danger" {
  if (score >= 85) return "good";
  if (score >= 65) return "mid";
  return "danger";
}

function FindingMini({ finding }: { finding: { title: string; recommendation: string; severity: Severity } }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[.04] p-4">
      <Badge variant={finding.severity}>{finding.severity}</Badge>
      <div className="mt-2 font-semibold text-white">{finding.title}</div>
      <div className="mt-1 text-sm text-slate-400">{finding.recommendation}</div>
    </div>
  );
}

function DiffGroup({ title, findings, tone }: { title: string; findings: Array<{ title: string; severity: Severity }>; tone: "good" | "danger" }) {
  return (
    <div className={`rounded-2xl border p-4 ${tone === "good" ? "border-emerald-300/20 bg-emerald-300/10" : "border-rose-300/20 bg-rose-300/10"}`}>
      <div className="flex items-center justify-between gap-3">
        <div className="font-semibold text-white">{title}</div>
        <div className="text-3xl font-black text-white">{findings.length}</div>
      </div>
      {findings.length ? (
        <div className="mt-3 space-y-2">
          {findings.slice(0, 4).map((finding) => (
            <div key={`${title}-${finding.title}`} className="flex items-center justify-between gap-3 rounded-xl bg-black/20 px-3 py-2 text-sm text-slate-200">
              <span className="truncate">{finding.title}</span>
              <Badge variant={finding.severity}>{finding.severity}</Badge>
            </div>
          ))}
        </div>
      ) : <p className="mt-2 text-sm text-slate-400">Nothing in this bucket.</p>}
    </div>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function EmptyState({ label }: { label: string }) {
  return <div className="flex min-h-48 items-center justify-center rounded-2xl border border-white/10 bg-white/[.03] p-6 text-center text-slate-400">{label}</div>;
}

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function downloadFile(filename: string, body: string, type: string) {
  const blob = new Blob([body], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
