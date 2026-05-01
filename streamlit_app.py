from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from clawaudit.reporting import render_markdown
from clawaudit.scanner import scan

st.set_page_config(page_title="ClawAudit", page_icon="🦞", layout="wide")

st.markdown(
    """
<style>
.stApp {
  background: radial-gradient(circle at 5% 0%, #1e2a4a 0, #0b1020 34%, #050609 100%);
  color: #f8fafc;
}
.block-container { padding-top: 2rem; }
[data-testid="stMetricValue"] { font-size: 2.35rem; }
.claw-hero {
  border: 1px solid rgba(125,211,252,.22);
  background: linear-gradient(135deg, rgba(15,23,42,.92), rgba(30,41,59,.60));
  border-radius: 28px;
  padding: 1.4rem 1.6rem;
  box-shadow: 0 24px 80px rgba(0,0,0,.38);
}
.claw-card {
  border: 1px solid rgba(148,163,184,.20);
  background: linear-gradient(135deg, rgba(15,23,42,.88), rgba(30,41,59,.50));
  border-radius: 20px;
  padding: 1.05rem 1.15rem;
  box-shadow: 0 16px 46px rgba(0,0,0,.28);
}
.finding-critical { border-left: 6px solid #ef4444; }
.finding-high { border-left: 6px solid #fb7185; }
.finding-warn { border-left: 6px solid #fbbf24; }
.finding-info { border-left: 6px solid #38bdf8; }
.small-muted { color: #94a3b8; font-size: .9rem; }
.score-good { color: #22c55e; font-weight: 800; }
.score-mid { color: #fbbf24; font-weight: 800; }
.score-bad { color: #fb7185; font-weight: 800; }
</style>
""",
    unsafe_allow_html=True,
)


def score_label(score: int) -> str:
    if score >= 85:
        return "Strong"
    if score >= 65:
        return "Needs review"
    return "Risky"


def score_class(score: int) -> str:
    if score >= 85:
        return "score-good"
    if score >= 65:
        return "score-mid"
    return "score-bad"


with st.sidebar:
    st.header("Scan target")
    workspace = st.text_input("Workspace", str(Path.home() / ".openclaw" / "workspace"))
    gateway_home = st.text_input("Gateway home", str(Path.home() / ".openclaw"))
    run = st.button("Run audit", type="primary", use_container_width=True)
    st.divider()
    st.caption("ClawAudit is read-only. It scans local files and does not execute automations.")

if "report" not in st.session_state or run:
    with st.spinner("Scanning OpenClaw autonomy surface..."):
        st.session_state.report = scan(Path(workspace), Path(gateway_home))

report = st.session_state.report
markdown_report = render_markdown(report)
json_report = report.to_dict()

st.markdown(
    f"""
<div class="claw-hero">
  <h1 style="margin:0">🦞 ClawAudit</h1>
  <p style="margin:.35rem 0 0;color:#cbd5e1">Local-first autonomy auditor for OpenClaw workspaces.</p>
  <p style="margin:.8rem 0 0" class="small-muted">Workspace: <code>{report.workspace}</code></p>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")
score_col, rel_col, findings_col, items_col = st.columns(4)
score_col.metric("Safety", f"{report.safety_score}/100", score_label(report.safety_score))
rel_col.metric("Reliability", f"{report.reliability_score}/100", score_label(report.reliability_score))
findings_col.metric("Findings", len(report.findings))
items_col.metric("Inventory", len(report.items))

critical_or_high = [f for f in report.findings if f.severity in {"critical", "high"}]
if critical_or_high:
    st.error(f"{len(critical_or_high)} high-priority finding(s) need review before trusting unattended automation.")
elif any(f.severity == "warn" for f in report.findings):
    st.warning("No high-risk findings, but there are warnings worth cleaning up.")
else:
    st.success("No high-risk warnings found. Review info findings for optional hardening.")

tab_overview, tab_findings, tab_inventory, tab_report = st.tabs(["Overview", "Findings", "Inventory", "Report export"])

with tab_overview:
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Autonomy score")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=report.safety_score,
            number={"suffix": "/100", "font": {"size": 48}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#38bdf8"},
                "steps": [
                    {"range": [0, 50], "color": "rgba(244,63,94,.35)"},
                    {"range": [50, 80], "color": "rgba(251,191,36,.30)"},
                    {"range": [80, 100], "color": "rgba(34,197,94,.30)"},
                ],
            },
        ))
        fig.update_layout(height=330, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Risk distribution")
        by_severity = report.stats.get("findings_by_severity", {})
        labels = [s for s in ["critical", "high", "warn", "info"] if by_severity.get(s, 0)]
        values = [by_severity[s] for s in labels]
        if values:
            colors = {"critical": "#ef4444", "high": "#fb7185", "warn": "#fbbf24", "info": "#38bdf8"}
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.58, marker_colors=[colors[l] for l in labels])])
            fig.update_layout(height=330, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("No findings.")

    st.subheader("Risk by area")
    by_area = report.stats.get("findings_by_area", {})
    if by_area:
        fig = go.Figure(data=[go.Bar(x=list(by_area.keys()), y=list(by_area.values()), marker_color="#8b5cf6")])
        fig.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=70), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,.35)", font_color="#f8fafc")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recommended next actions")
    priority = [f for f in report.findings if f.severity in {"critical", "high"}] or [f for f in report.findings if f.severity == "warn"] or report.findings[:5]
    for finding in priority[:5]:
        st.markdown(f"- **{finding.title}** — {finding.recommendation}")

with tab_findings:
    st.subheader("Findings")
    severity_filter = st.multiselect("Severity", ["critical", "high", "warn", "info"], default=["critical", "high", "warn", "info"])
    area_filter = st.multiselect("Area", sorted({f.area for f in report.findings}), default=sorted({f.area for f in report.findings}))
    severity_order = {"critical": 0, "high": 1, "warn": 2, "info": 3}
    for finding in sorted(report.findings, key=lambda f: (severity_order.get(f.severity, 9), f.area, f.title)):
        if finding.severity not in severity_filter or finding.area not in area_filter:
            continue
        badge = {"critical": "🔴", "high": "🟠", "warn": "🟡", "info": "🔵"}.get(finding.severity, "⚪")
        st.markdown(f"<div class='claw-card finding-{finding.severity}'>", unsafe_allow_html=True)
        st.markdown(f"### {badge} {finding.title}")
        st.caption(f"{finding.severity.upper()} · {finding.area} · {finding.id}")
        st.write(finding.detail)
        st.markdown(f"**Recommendation:** {finding.recommendation}")
        if finding.evidence:
            with st.expander("Evidence"):
                for evidence in finding.evidence:
                    st.code(evidence, language=None)
        st.markdown("</div><br>", unsafe_allow_html=True)

with tab_inventory:
    st.subheader("Automation inventory")
    kinds = sorted({item.kind for item in report.items})
    kind_filter = st.multiselect("Filter by kind", kinds, default=kinds)
    for item in report.items:
        if item.kind not in kind_filter:
            continue
        st.markdown(f"""
<div class="claw-card">
  <strong>{item.kind}</strong> · <code>{item.name}</code><br>
  <span class="small-muted">{item.summary or ''}</span><br>
  <span class="small-muted">{item.path or ''}</span>
</div>
<br>
""", unsafe_allow_html=True)

with tab_report:
    st.subheader("Export")
    st.download_button("Download Markdown report", markdown_report, file_name="AUTONOMY_AUDIT.md", mime="text/markdown")
    st.download_button("Download JSON report", data=__import__("json").dumps(json_report, indent=2), file_name="autonomy_audit.json", mime="application/json")
    st.markdown("### Preview")
    st.code(markdown_report[:6000], language="markdown")
