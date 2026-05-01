from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import AuditReport, default_gateway_home

TOKEN_RE = re.compile(r"[a-zA-Z0-9_./:-]{2,}")
VECTOR_SIZE = 384


@dataclass(frozen=True)
class StoredRun:
    id: int
    created_at: str
    workspace: str
    gateway_home: str
    safety_score: int
    reliability_score: int
    finding_count: int
    item_count: int
    summary: str


def default_history_path() -> Path:
    return default_gateway_home() / "clawaudit" / "history.sqlite"


class AuditHistoryStore:
    """Local SQLite audit history with lightweight vector-style similarity search.

    The store intentionally avoids external services. Each run keeps the full report JSON,
    a human-readable summary, and a compact hashed token vector used for cosine similarity.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = (db_path or default_history_path()).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    workspace TEXT NOT NULL,
                    gateway_home TEXT NOT NULL,
                    safety_score INTEGER NOT NULL,
                    reliability_score INTEGER NOT NULL,
                    finding_count INTEGER NOT NULL,
                    item_count INTEGER NOT NULL,
                    summary TEXT NOT NULL,
                    report_json TEXT NOT NULL,
                    vector_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_diffs (
                    run_id INTEGER PRIMARY KEY,
                    previous_run_id INTEGER,
                    added_findings TEXT NOT NULL,
                    resolved_findings TEXT NOT NULL,
                    changed_findings TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES audit_runs(id),
                    FOREIGN KEY(previous_run_id) REFERENCES audit_runs(id)
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_audit_runs_created_at ON audit_runs(created_at DESC)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_audit_runs_workspace ON audit_runs(workspace)")

    def save_report(self, report: AuditReport) -> int:
        report_dict = report.to_dict()
        summary = build_summary(report_dict)
        vector = vectorize(summary + "\n" + report_text(report_dict))
        created_at = datetime.now(UTC).isoformat()
        previous = self.latest_run(workspace=report.workspace)

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO audit_runs (
                    created_at, workspace, gateway_home, safety_score, reliability_score,
                    finding_count, item_count, summary, report_json, vector_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    report.workspace,
                    report.gateway_home,
                    report.safety_score,
                    report.reliability_score,
                    len(report.findings),
                    len(report.items),
                    summary,
                    json.dumps(report_dict, sort_keys=True),
                    json.dumps(vector, sort_keys=True),
                ),
            )
            run_id = int(cursor.lastrowid)
            diff = diff_reports(previous["report"] if previous else None, report_dict)
            connection.execute(
                """
                INSERT INTO audit_diffs (run_id, previous_run_id, added_findings, resolved_findings, changed_findings)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    previous["id"] if previous else None,
                    json.dumps(diff["added_findings"], sort_keys=True),
                    json.dumps(diff["resolved_findings"], sort_keys=True),
                    json.dumps(diff["changed_findings"], sort_keys=True),
                ),
            )
            return run_id

    def list_runs(self, limit: int = 20, date_from: str | None = None, date_to: str | None = None) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 100))
        where, params = date_filters(date_from, date_to)
        params.append(limit)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT id, created_at, workspace, gateway_home, safety_score, reliability_score,
                       finding_count, item_count, summary
                FROM audit_runs
                {where}
                ORDER BY datetime(created_at) DESC, id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [dict(row) for row in rows]

    def latest_run(self, workspace: str | None = None) -> dict[str, Any] | None:
        query = "SELECT * FROM audit_runs"
        params: tuple[Any, ...] = ()
        if workspace:
            query += " WHERE workspace = ?"
            params = (workspace,)
        query += " ORDER BY datetime(created_at) DESC, id DESC LIMIT 1"
        with self._connect() as connection:
            row = connection.execute(query, params).fetchone()
        return self._row_with_report(row) if row else None

    def get_run(self, run_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM audit_runs WHERE id = ?", (run_id,)).fetchone()
        return self._row_with_report(row) if row else None

    def get_diff(self, run_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM audit_diffs WHERE run_id = ?", (run_id,)).fetchone()
        if not row:
            return None
        return {
            "run_id": row["run_id"],
            "previous_run_id": row["previous_run_id"],
            "added_findings": json.loads(row["added_findings"]),
            "resolved_findings": json.loads(row["resolved_findings"]),
            "changed_findings": json.loads(row["changed_findings"]),
        }

    def search(self, query: str, limit: int = 10, date_from: str | None = None, date_to: str | None = None) -> list[dict[str, Any]]:
        query_vector = vectorize(query)
        query_terms = set(tokenize(query))
        limit = max(1, min(limit, 50))
        where, params = date_filters(date_from, date_to)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT id, created_at, workspace, gateway_home, safety_score, reliability_score,
                       finding_count, item_count, summary, vector_json
                FROM audit_runs
                {where}
                ORDER BY datetime(created_at) DESC, id DESC
                LIMIT 250
                """,
                tuple(params),
            ).fetchall()

        scored: list[dict[str, Any]] = []
        for row in rows:
            row_dict = dict(row)
            vector = {int(k): float(v) for k, v in json.loads(row_dict.pop("vector_json")).items()}
            score = cosine_similarity(query_vector, vector)
            summary_terms = set(tokenize(row_dict["summary"]))
            if query_terms:
                score += 0.08 * len(query_terms & summary_terms)
            if score > 0:
                row_dict["score"] = round(score, 4)
                scored.append(row_dict)
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:limit]

    def _row_with_report(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["report"] = json.loads(data.pop("report_json"))
        data.pop("vector_json", None)
        return data


def date_filters(date_from: str | None, date_to: str | None) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if date_from:
        clauses.append("date(created_at) >= date(?)")
        params.append(date_from)
    if date_to:
        clauses.append("date(created_at) <= date(?)")
        params.append(date_to)
    return ("WHERE " + " AND ".join(clauses), params) if clauses else ("", params)


def build_summary(report: dict[str, Any]) -> str:
    severity = report.get("stats", {}).get("findings_by_severity", {}) or {}
    area = report.get("stats", {}).get("findings_by_area", {}) or {}
    top_areas = ", ".join(f"{name}: {count}" for name, count in sorted(area.items(), key=lambda item: item[1], reverse=True)[:4])
    top_findings = "; ".join(finding.get("title", "Untitled") for finding in report.get("findings", [])[:4])
    return (
        f"Safety {report.get('safety_score')}/100, reliability {report.get('reliability_score')}/100. "
        f"Findings by severity: {severity}. Areas: {top_areas or 'none'}. "
        f"Top findings: {top_findings or 'none'}."
    )


def report_text(report: dict[str, Any]) -> str:
    parts: list[str] = [build_summary(report)]
    for finding in report.get("findings", []):
        parts.extend([
            finding.get("id", ""),
            finding.get("title", ""),
            finding.get("severity", ""),
            finding.get("area", ""),
            finding.get("detail", ""),
            finding.get("recommendation", ""),
            " ".join(finding.get("evidence", [])),
        ])
    for item in report.get("items", []):
        parts.extend([item.get("kind", ""), item.get("name", ""), item.get("summary", "") or "", item.get("path", "") or ""])
    return "\n".join(parts)


def diff_reports(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    if not previous:
        return {"added_findings": current.get("findings", []), "resolved_findings": [], "changed_findings": []}

    previous_findings = {finding.get("id"): finding for finding in previous.get("findings", [])}
    current_findings = {finding.get("id"): finding for finding in current.get("findings", [])}
    previous_ids = set(previous_findings)
    current_ids = set(current_findings)

    changed = []
    for finding_id in sorted(previous_ids & current_ids):
        before = previous_findings[finding_id]
        after = current_findings[finding_id]
        if before.get("severity") != after.get("severity") or before.get("detail") != after.get("detail"):
            changed.append({"id": finding_id, "before": before, "after": after})

    return {
        "added_findings": [current_findings[finding_id] for finding_id in sorted(current_ids - previous_ids)],
        "resolved_findings": [previous_findings[finding_id] for finding_id in sorted(previous_ids - current_ids)],
        "changed_findings": changed,
    }


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def vectorize(text: str) -> dict[int, float]:
    counts: dict[int, float] = {}
    for token in tokenize(text):
        bucket = stable_hash(token) % VECTOR_SIZE
        counts[bucket] = counts.get(bucket, 0.0) + 1.0
    norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {bucket: round(value / norm, 6) for bucket, value in counts.items()}


def stable_hash(value: str) -> int:
    result = 2166136261
    for char in value:
        result ^= ord(char)
        result = (result * 16777619) & 0xFFFFFFFF
    return result


def cosine_similarity(left: dict[int, float], right: dict[int, float]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(bucket, 0.0) for bucket, value in left.items())
