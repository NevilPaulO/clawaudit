from __future__ import annotations

import json
from pathlib import Path

from .models import AuditReport, Finding

SEVERITY_ORDER = ["critical", "high", "warn", "info"]


def write_reports(report: AuditReport, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "autonomy_audit.json"
    md_path = out_dir / "AUTONOMY_AUDIT.md"
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return md_path, json_path


def render_markdown(report: AuditReport) -> str:
    lines: list[str] = []
    lines.append("# OpenClaw Autonomy Audit")
    lines.append("")
    lines.append(f"Workspace: `{report.workspace}`")
    lines.append(f"Gateway home: `{report.gateway_home}`")
    lines.append("")
    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"- Safety score: **{report.safety_score}/100**")
    lines.append(f"- Reliability score: **{report.reliability_score}/100**")
    lines.append(f"- Findings: **{len(report.findings)}**")
    lines.append(f"- Inventory items: **{len(report.items)}**")
    lines.append("")
    lines.extend(render_recommendation_summary(report))
    lines.append("")
    lines.append("## Inventory")
    lines.append("")
    for kind, count in sorted(report.stats.get("items_by_kind", {}).items()):
        lines.append(f"- {kind}: {count}")
    lines.append("")
    lines.append("## Risk distribution")
    lines.append("")
    for severity in SEVERITY_ORDER:
        count = report.stats.get("findings_by_severity", {}).get(severity, 0)
        lines.append(f"- {severity}: {count}")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    if not report.findings:
        lines.append("No findings. Nice and suspiciously clean.")
    else:
        for severity in SEVERITY_ORDER:
            group = [f for f in report.findings if f.severity == severity]
            if not group:
                continue
            lines.append(f"### {severity.upper()}")
            lines.append("")
            for finding in group:
                lines.extend(render_finding(finding))
    lines.append("")
    lines.append("## Automation inventory")
    lines.append("")
    for item in report.items:
        path = f" — `{item.path}`" if item.path else ""
        summary = f": {item.summary}" if item.summary else ""
        lines.append(f"- **{item.kind}** `{item.name}`{summary}{path}")
    lines.append("")
    lines.append("## How to read this report")
    lines.append("")
    lines.append("ClawAudit is a static local audit. It reads known OpenClaw workspace/config files and flags patterns that commonly cause noisy, unsafe, or unreliable unattended automations. It does not replace OpenClaw's built-in status/config validation, and it does not execute automations.")
    lines.append("")
    return "\n".join(lines)


def render_recommendation_summary(report: AuditReport) -> list[str]:
    high_priority = [f for f in report.findings if f.severity in {"critical", "high"}]
    warn_priority = [f for f in report.findings if f.severity == "warn"]
    lines = ["## Recommended next actions", ""]
    if high_priority:
        lines.append("Handle these first:")
        for finding in high_priority[:5]:
            lines.append(f"- **{finding.title}** — {finding.recommendation}")
    elif warn_priority:
        lines.append("No high/critical issues found. Best next cleanup:")
        for finding in warn_priority[:5]:
            lines.append(f"- **{finding.title}** — {finding.recommendation}")
    else:
        lines.append("No urgent action. Review info findings for optional hardening.")
    return lines


def render_finding(finding: Finding) -> list[str]:
    lines = [f"#### {finding.title}", ""]
    lines.append(f"- Severity: `{finding.severity}`")
    lines.append(f"- Area: `{finding.area}`")
    lines.append(f"- ID: `{finding.id}`")
    lines.append(f"- Detail: {finding.detail}")
    lines.append(f"- Recommendation: {finding.recommendation}")
    if finding.evidence:
        lines.append("- Evidence:")
        for evidence in finding.evidence:
            lines.append(f"  - `{evidence}`")
    lines.append("")
    return lines
