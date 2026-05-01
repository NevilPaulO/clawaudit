from __future__ import annotations

import argparse
from pathlib import Path

from .history import AuditHistoryStore
from .reporting import write_reports
from .scanner import scan


def main() -> None:
    parser = argparse.ArgumentParser(prog="clawaudit", description="Audit OpenClaw autonomy surfaces")
    sub = parser.add_subparsers(dest="command")

    audit = sub.add_parser("audit", help="Scan an OpenClaw workspace and generate reports")
    audit.add_argument("--workspace", default=str(Path.home() / ".openclaw" / "workspace"))
    audit.add_argument("--gateway-home", default=str(Path.home() / ".openclaw"))
    audit.add_argument("--out", default="reports")

    args = parser.parse_args()
    if args.command in {None, "audit"}:
        report = scan(Path(args.workspace), Path(args.gateway_home))
        run_id = AuditHistoryStore().save_report(report)
        md_path, json_path = write_reports(report, Path(args.out))
        print(f"ClawAudit complete")
        print(f"History run: #{run_id}")
        print(f"Safety score: {report.safety_score}/100")
        print(f"Reliability score: {report.reliability_score}/100")
        print(f"Findings: {len(report.findings)}")
        print(f"Markdown: {md_path}")
        print(f"JSON: {json_path}")


if __name__ == "__main__":
    main()
