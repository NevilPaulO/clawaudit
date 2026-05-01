from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .history import AuditHistoryStore
from .models import default_gateway_home, default_workspace
from .reporting import render_markdown
from .scanner import scan


class AuditRequest(BaseModel):
    workspace: str | None = Field(default=None, description="OpenClaw workspace path")
    gateway_home: str | None = Field(default=None, description="OpenClaw gateway home path")


class HistorySearchRequest(BaseModel):
    query: str = Field(min_length=1, description="Text to search across saved audit history")
    limit: int = Field(default=10, ge=1, le=50)
    date_from: str | None = Field(default=None, description="Inclusive start date as YYYY-MM-DD")
    date_to: str | None = Field(default=None, description="Inclusive end date as YYYY-MM-DD")


app = FastAPI(
    title="ClawAudit API",
    version="0.1.0",
    description="Read-only API bridge for the ClawAudit Python audit engine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_latest_report: dict[str, Any] | None = None
_latest_markdown: str | None = None
_history = AuditHistoryStore()


def run_scan(request: AuditRequest | None = None):
    workspace = Path(request.workspace).expanduser() if request and request.workspace else default_workspace()
    gateway_home = Path(request.gateway_home).expanduser() if request and request.gateway_home else default_gateway_home()
    return scan(workspace, gateway_home)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": "clawaudit-api"}


@app.post("/api/audit/run")
def audit_run(request: AuditRequest | None = None) -> dict[str, Any]:
    global _latest_report, _latest_markdown
    report = run_scan(request)
    run_id = _history.save_report(report)
    _latest_report = report.to_dict()
    _latest_report["history_run_id"] = run_id
    _latest_markdown = render_markdown(report)
    return _latest_report


@app.get("/api/audit/latest")
def audit_latest() -> dict[str, Any]:
    global _latest_report, _latest_markdown
    if _latest_report is None:
        stored = _history.latest_run()
        if stored:
            _latest_report = stored["report"]
            _latest_report["history_run_id"] = stored["id"]
        else:
            report = run_scan()
            run_id = _history.save_report(report)
            _latest_report = report.to_dict()
            _latest_report["history_run_id"] = run_id
        _latest_markdown = render_markdown(run_scan())
    return _latest_report


@app.get("/api/audit/report/markdown", response_model=None)
def audit_report_markdown() -> dict[str, str]:
    global _latest_report, _latest_markdown
    if _latest_markdown is None:
        report = run_scan()
        _latest_report = report.to_dict()
        _latest_markdown = render_markdown(report)
    return {"markdown": _latest_markdown}


@app.get("/api/audit/report/json")
def audit_report_json() -> dict[str, Any]:
    return audit_latest()


@app.get("/api/history/runs")
def history_runs(limit: int = 20, date_from: str | None = None, date_to: str | None = None) -> dict[str, Any]:
    return {"runs": _history.list_runs(limit=limit, date_from=date_from, date_to=date_to)}


@app.get("/api/history/runs/{run_id}")
def history_run(run_id: int) -> dict[str, Any]:
    stored = _history.get_run(run_id)
    if not stored:
        return {"error": "Run not found"}
    return stored


@app.get("/api/history/runs/{run_id}/diff")
def history_diff(run_id: int) -> dict[str, Any]:
    diff = _history.get_diff(run_id)
    if not diff:
        return {"error": "Diff not found"}
    return diff


@app.post("/api/history/search")
def history_search(request: HistorySearchRequest) -> dict[str, Any]:
    return {"results": _history.search(request.query, limit=request.limit, date_from=request.date_from, date_to=request.date_to)}
