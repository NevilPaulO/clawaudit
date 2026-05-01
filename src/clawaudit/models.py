from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Literal

Severity = Literal["info", "warn", "high", "critical"]

SEVERITY_WEIGHTS: dict[Severity, int] = {
    "info": 1,
    "warn": 4,
    "high": 9,
    "critical": 16,
}


@dataclass
class Finding:
    id: str
    title: str
    severity: Severity
    area: str
    detail: str
    recommendation: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditItem:
    kind: str
    name: str
    path: str | None = None
    summary: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditReport:
    workspace: str
    gateway_home: str
    findings: list[Finding]
    items: list[AuditItem]
    stats: dict[str, Any]

    @property
    def safety_score(self) -> int:
        penalty = sum(SEVERITY_WEIGHTS[f.severity] for f in self.findings)
        return max(0, min(100, 100 - penalty))

    @property
    def reliability_score(self) -> int:
        penalty = 0
        for f in self.findings:
            if f.area in {"cron", "heartbeat", "hooks", "taskflow"}:
                penalty += SEVERITY_WEIGHTS[f.severity]
            else:
                penalty += max(1, SEVERITY_WEIGHTS[f.severity] // 2)
        return max(0, min(100, 100 - penalty))

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace": self.workspace,
            "gateway_home": self.gateway_home,
            "safety_score": self.safety_score,
            "reliability_score": self.reliability_score,
            "stats": self.stats,
            "items": [i.to_dict() for i in self.items],
            "findings": [f.to_dict() for f in self.findings],
        }


def default_workspace() -> Path:
    return Path.home() / ".openclaw" / "workspace"


def default_gateway_home() -> Path:
    return Path.home() / ".openclaw"
