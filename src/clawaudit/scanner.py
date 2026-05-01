from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .models import AuditItem, AuditReport, Finding, default_gateway_home, default_workspace

WORKSPACE_FILES = ["AGENTS.md", "HEARTBEAT.md", "MEMORY.md", "TOOLS.md", "USER.md", "IDENTITY.md"]
ACTION_WORDS = re.compile(r"\b(send|post|tweet|email|delete|remove|buy|sell|trade|transfer|approve|publish|restart|stop|start|deploy|commit|push)\b", re.I)
APPROVAL_WORDS = re.compile(r"\b(ask|approval|approve|confirm|permission|human|review|sign[- ]?off|before acting)\b", re.I)
ESCALATION_WORDS = re.compile(r"\b(escalat|alert|notify|interrupt|failure|blocked|risk|urgent)\b", re.I)
SILENCE_WORDS = re.compile(r"\b(HEARTBEAT_OK|NO_REPLY|stay quiet|silent|do not notify|only alert|nothing new)\b", re.I)
SECRET_PATTERNS = re.compile(r"\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*['\"]?[^\s'\"]{12,}", re.I)
RISKY_SKILL_WORDS = re.compile(r"\b(exec|shell|command|subprocess|browser|send|delete|publish|tweet|email|trade|wallet|transfer)\b", re.I)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")
    except FileNotFoundError:
        return ""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def scan(workspace: Path | None = None, gateway_home: Path | None = None) -> AuditReport:
    workspace = (workspace or default_workspace()).expanduser().resolve()
    gateway_home = (gateway_home or default_gateway_home()).expanduser().resolve()
    findings: list[Finding] = []
    items: list[AuditItem] = []

    scan_workspace_files(workspace, findings, items)
    scan_config(gateway_home, findings, items)
    scan_cron(gateway_home, findings, items)
    scan_hooks(gateway_home, workspace, findings, items)
    scan_skills(workspace, findings, items)

    stats = build_stats(findings, items)
    return AuditReport(
        workspace=str(workspace),
        gateway_home=str(gateway_home),
        findings=findings,
        items=items,
        stats=stats,
    )


def add_finding(findings: list[Finding], finding: Finding) -> None:
    # Keep IDs stable but avoid duplicates from multiple sources.
    if not any(existing.id == finding.id for existing in findings):
        findings.append(finding)


def scan_workspace_files(workspace: Path, findings: list[Finding], items: list[AuditItem]) -> None:
    for name in WORKSPACE_FILES:
        path = workspace / name
        if path.exists():
            text = read_text(path)
            items.append(AuditItem(kind="workspace_file", name=name, path=str(path), summary=f"{len(text.splitlines())} lines"))
            if SECRET_PATTERNS.search(text):
                add_finding(findings, Finding(
                    id=f"possible-secret-{name.lower()}",
                    title=f"Possible secret-like value in {name}",
                    severity="high",
                    area="workspace",
                    detail=f"{name} contains text that looks like an inline token, password, API key, or secret.",
                    recommendation="Move secrets to OpenClaw SecretRefs, environment variables, or a password manager. Keep workspace instructions secret-free.",
                    evidence=[str(path)],
                ))
        elif name in {"AGENTS.md", "HEARTBEAT.md"}:
            add_finding(findings, Finding(
                id=f"missing-{name.lower()}",
                title=f"Missing {name}",
                severity="warn",
                area="workspace",
                detail=f"{name} was not found in the workspace.",
                recommendation=f"Create {name} so autonomous behavior and boundaries are explicit.",
                evidence=[str(path)],
            ))

    agents = read_text(workspace / "AGENTS.md")
    heartbeat = read_text(workspace / "HEARTBEAT.md")

    if agents:
        has_program_markers = all(marker.lower() in agents.lower() for marker in ["authority", "trigger"]) or "Program:" in agents
        if not has_program_markers:
            add_finding(findings, Finding(
                id="standing-orders-not-explicit",
                title="Standing orders are not explicit",
                severity="info",
                area="standing_orders",
                detail="AGENTS.md exists, but no obvious standing-order sections with authority and triggers were found.",
                recommendation="For recurring autonomous programs, add sections with Authority, Trigger, Approval gate, and Escalation rules.",
                evidence=["AGENTS.md lacks clear Authority/Trigger markers"],
            ))

        if ACTION_WORDS.search(agents) and not APPROVAL_WORDS.search(agents):
            add_finding(findings, Finding(
                id="actions-without-approval-language",
                title="Potential external/destructive actions lack approval language",
                severity="high",
                area="standing_orders",
                detail="AGENTS.md mentions action verbs such as send/delete/post/restart but does not clearly mention approvals or confirmation.",
                recommendation="Add explicit approval gates for external, destructive, financial, or public actions.",
                evidence=["AGENTS.md action words found without approval words"],
            ))

        if "authority" in agents.lower() and not ESCALATION_WORDS.search(agents):
            add_finding(findings, Finding(
                id="standing-orders-no-escalation",
                title="Standing orders may lack escalation rules",
                severity="warn",
                area="standing_orders",
                detail="Authority-like language exists, but escalation/failure wording is not obvious.",
                recommendation="Document when the agent must stop, alert, ask, or hand the decision back to the human.",
                evidence=["Authority wording found without escalation/failure wording"],
            ))

    meaningful_heartbeat = active_lines(heartbeat)
    if heartbeat and meaningful_heartbeat and not SILENCE_WORDS.search(heartbeat):
        add_finding(findings, Finding(
            id="heartbeat-no-silence-contract",
            title="Heartbeat tasks may be noisy",
            severity="warn",
            area="heartbeat",
            detail="HEARTBEAT.md has active-looking content but no obvious silence/alert discipline.",
            recommendation="Tell the agent when to stay quiet and when to interrupt the user.",
            evidence=["No HEARTBEAT_OK/NO_REPLY/stay quiet wording found"],
        ))

    precise_words = ("every day", "daily at", " at ", "sharp", "exact", "cron")
    if heartbeat and any(any(word in line.lower() for word in precise_words) for line in meaningful_heartbeat):
        add_finding(findings, Finding(
            id="heartbeat-possible-cron-work",
            title="Heartbeat may contain precise scheduling work",
            severity="info",
            area="heartbeat",
            detail="Heartbeat appears to mention exact timing. Exact schedules usually belong in cron.",
            recommendation="Move exact-time reminders/reports to OpenClaw cron and keep heartbeat for flexible awareness checks.",
            evidence=meaningful_heartbeat[:3],
        ))

    if len(meaningful_heartbeat) > 20:
        add_finding(findings, Finding(
            id="heartbeat-too-large",
            title="Heartbeat file may be too large",
            severity="warn",
            area="heartbeat",
            detail=f"HEARTBEAT.md has {len(meaningful_heartbeat)} active lines. Large heartbeat prompts can waste tokens and become unfocused.",
            recommendation="Keep HEARTBEAT.md short: current checks, last-check state path, and interruption rules. Move durable programs to standing orders or cron.",
            evidence=[f"{len(meaningful_heartbeat)} active lines"],
        ))


def scan_config(gateway_home: Path, findings: list[Finding], items: list[AuditItem]) -> None:
    config_path = gateway_home / "openclaw.json"
    data = load_json(config_path)
    if data is None:
        add_finding(findings, Finding(
            id="config-unreadable",
            title="OpenClaw config missing or not strict JSON",
            severity="info",
            area="config",
            detail="ClawAudit could not parse ~/.openclaw/openclaw.json as JSON. OpenClaw may support JSONC/includes, but this MVP reads strict JSON only.",
            recommendation="Use the Control UI/OpenClaw config tools for authoritative config validation. Future ClawAudit versions can add JSONC support.",
            evidence=[str(config_path)],
        ))
        return

    items.append(AuditItem(kind="config", name="openclaw.json", path=str(config_path), summary="Gateway config parsed"))
    text = json.dumps(data).lower()
    if '"ask"' in text and '"off"' in text and "exec" in text:
        add_finding(findings, Finding(
            id="exec-approval-may-be-off",
            title="Exec approval policy may be permissive",
            severity="high",
            area="config",
            detail="Config appears to mention exec approval settings with ask=off.",
            recommendation="Keep host/gateway/node exec approvals on unless this is a trusted local-only setup with clear standing authority.",
            evidence=[str(config_path)],
        ))

    if "heartbeat" in text and '"0m"' not in text:
        items.append(AuditItem(kind="automation_surface", name="heartbeat", path=str(config_path), summary="Heartbeat configuration referenced"))


def scan_cron(gateway_home: Path, findings: list[Finding], items: list[AuditItem]) -> None:
    jobs_path = gateway_home / "cron" / "jobs.json"
    jobs_data = load_json(jobs_path)
    if jobs_data is None:
        add_finding(findings, Finding(
            id="cron-jobs-unreadable",
            title="Cron jobs file missing or unreadable",
            severity="info",
            area="cron",
            detail="No readable ~/.openclaw/cron/jobs.json file was found.",
            recommendation="If this agent uses scheduled automations, verify cron is configured and jobs are visible.",
            evidence=[str(jobs_path)],
        ))
        return

    jobs = jobs_data if isinstance(jobs_data, list) else jobs_data.get("jobs", []) if isinstance(jobs_data, dict) else []
    seen_schedules: dict[str, list[str]] = {}
    enabled_count = 0
    for job in jobs:
        if not isinstance(job, dict):
            continue
        job_id = str(job.get("jobId") or job.get("id") or job.get("name") or "unknown")
        name = str(job.get("name") or job_id)
        enabled = job.get("enabled", True)
        if enabled is not False:
            enabled_count += 1
        schedule = job.get("schedule", {})
        payload = job.get("payload", {})
        delivery = job.get("delivery", {})
        session_target = job.get("sessionTarget") or job.get("session") or "default"
        schedule_key = json.dumps(schedule, sort_keys=True)
        seen_schedules.setdefault(schedule_key, []).append(name)
        items.append(AuditItem(
            kind="cron_job",
            name=name,
            path=str(jobs_path),
            summary=f"{schedule_label(schedule)} · enabled={enabled} · target={session_target}",
            metadata={"id": job_id, "enabled": enabled, "schedule": schedule, "delivery": delivery, "sessionTarget": session_target},
        ))

        if enabled is False:
            continue
        if not job.get("failureAlert") and not delivery.get("failureDestination"):
            add_finding(findings, Finding(
                id=f"cron-no-failure-alert-{job_id}",
                title="Cron job has no obvious failure alert",
                severity="warn",
                area="cron",
                detail=f"Enabled cron job '{name}' does not define failureAlert or delivery.failureDestination.",
                recommendation="Add a failure alert or failure destination so broken automations do not fail silently.",
                evidence=[name, str(schedule)],
            ))
        if delivery.get("mode") == "none" and payload.get("kind") == "agentTurn":
            add_finding(findings, Finding(
                id=f"cron-silent-agent-turn-{job_id}",
                title="Agent-turn cron job is fully silent",
                severity="info",
                area="cron",
                detail=f"Cron job '{name}' runs an agent turn with delivery.mode=none.",
                recommendation="Use silent delivery only for internal maintenance, and pair it with logs/failure alerts.",
                evidence=[name],
            ))
        if session_target in {"main", "current"} and payload.get("kind") == "agentTurn":
            add_finding(findings, Finding(
                id=f"cron-context-coupled-{job_id}",
                title="Cron job is coupled to chat context",
                severity="info",
                area="cron",
                detail=f"Cron job '{name}' appears to run against a shared/current session.",
                recommendation="Use isolated jobs for repeatable reports; use current/custom sessions only when deliberate context continuity is required.",
                evidence=[name, str(session_target)],
            ))

    if enabled_count > 8:
        add_finding(findings, Finding(
            id="many-enabled-cron-jobs",
            title="Many enabled cron jobs",
            severity="warn",
            area="cron",
            detail=f"{enabled_count} cron jobs are enabled. This can increase cost, noise, and overlapping runs.",
            recommendation="Group related checks, stagger schedules, and ensure each job has a failure destination.",
            evidence=[f"enabled jobs: {enabled_count}"],
        ))

    for schedule_key, names in seen_schedules.items():
        if schedule_key and len(names) > 1:
            add_finding(findings, Finding(
                id=f"duplicate-cron-schedule-{abs(hash(schedule_key))}",
                title="Multiple cron jobs share the same schedule",
                severity="info",
                area="cron",
                detail=f"{len(names)} cron jobs use the same schedule.",
                recommendation="Check whether these jobs should be staggered or combined to reduce bursts and duplicate notifications.",
                evidence=names[:6],
            ))


def scan_hooks(gateway_home: Path, workspace: Path, findings: list[Finding], items: list[AuditItem]) -> None:
    candidates = [gateway_home / "hooks", workspace / "hooks"]
    found = 0
    for root in candidates:
        if not root.exists():
            continue
        for hook_md in root.glob("*/HOOK.md"):
            found += 1
            text = read_text(hook_md)
            items.append(AuditItem(kind="hook", name=hook_md.parent.name, path=str(hook_md), summary=first_heading(text)))
            if "message:received" in text and not APPROVAL_WORDS.search(text):
                add_finding(findings, Finding(
                    id=f"message-hook-no-approval-{hook_md.parent.name}",
                    title="Message hook lacks obvious approval language",
                    severity="warn",
                    area="hooks",
                    detail=f"Hook '{hook_md.parent.name}' listens to inbound messages without obvious approval/guardrail wording.",
                    recommendation="Document what the hook may do and when it must escalate to the user.",
                    evidence=[str(hook_md)],
                ))
            if ACTION_WORDS.search(text) and not ESCALATION_WORDS.search(text):
                add_finding(findings, Finding(
                    id=f"hook-actions-no-escalation-{hook_md.parent.name}",
                    title="Hook action behavior lacks escalation language",
                    severity="warn",
                    area="hooks",
                    detail=f"Hook '{hook_md.parent.name}' appears to perform actions without clear failure/escalation wording.",
                    recommendation="Add handler docs that define success, failure, retry, and user notification behavior.",
                    evidence=[str(hook_md)],
                ))
    if found == 0:
        add_finding(findings, Finding(
            id="no-hooks-found",
            title="No standalone hooks found",
            severity="info",
            area="hooks",
            detail="No hooks were found in common hook directories.",
            recommendation="No action needed unless you expected lifecycle/message hooks to be installed.",
            evidence=[str(p) for p in candidates],
        ))


def scan_skills(workspace: Path, findings: list[Finding], items: list[AuditItem]) -> None:
    roots = [workspace / "skills", workspace / ".agents" / "skills", Path.home() / ".agents" / "skills", Path.home() / ".openclaw" / "skills"]
    skill_count = 0
    for root in roots:
        if not root.exists():
            continue
        for skill_md in root.glob("**/SKILL.md"):
            if len(skill_md.relative_to(root).parts) > 3:
                continue
            skill_count += 1
            text = read_text(skill_md)
            name = parse_frontmatter_name(text) or skill_md.parent.name
            items.append(AuditItem(kind="skill", name=name, path=str(skill_md), summary=first_description(text)))
            risky_matches = sorted(set(m.group(0).lower() for m in RISKY_SKILL_WORDS.finditer(text)))
            if risky_matches:
                severity = "warn" if any(word in risky_matches for word in ["delete", "publish", "tweet", "trade", "wallet", "transfer"]) else "info"
                add_finding(findings, Finding(
                    id=f"skill-risky-capability-{slug(name)}",
                    title="Skill may expand autonomous capability",
                    severity=severity,  # type: ignore[arg-type]
                    area="skills",
                    detail=f"Skill '{name}' mentions capability keywords: {', '.join(risky_matches[:8])}.",
                    recommendation="Review third-party/local skills before enabling broad tool access, especially if they include scripts or external actions.",
                    evidence=[str(skill_md)],
                ))
    if skill_count == 0:
        add_finding(findings, Finding(
            id="no-local-skills-found",
            title="No local skills found",
            severity="info",
            area="skills",
            detail="No workspace/personal/local skills were found in common directories.",
            recommendation="No action needed. Install skills only from trusted sources and review them first.",
            evidence=[str(r) for r in roots],
        ))


def build_stats(findings: list[Finding], items: list[AuditItem]) -> dict[str, Any]:
    by_severity: dict[str, int] = {}
    by_area: dict[str, int] = {}
    items_by_kind: dict[str, int] = {}
    for finding in findings:
        by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
        by_area[finding.area] = by_area.get(finding.area, 0) + 1
    for item in items:
        items_by_kind[item.kind] = items_by_kind.get(item.kind, 0) + 1
    return {"findings_by_severity": by_severity, "findings_by_area": by_area, "items_by_kind": items_by_kind}


def active_lines(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("```")
    ]


def schedule_label(schedule: Any) -> str:
    if not isinstance(schedule, dict):
        return "schedule=unknown"
    kind = schedule.get("kind", "unknown")
    if kind == "cron":
        return f"cron {schedule.get('expr', '?')} {schedule.get('tz', '')}".strip()
    if kind == "every":
        return f"every {schedule.get('everyMs', '?')}ms"
    if kind == "at":
        return f"at {schedule.get('at', '?')}"
    return str(schedule)


def first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.strip("# ").strip()
    return None


def first_description(text: str) -> str | None:
    in_frontmatter = False
    for line in text.splitlines()[:40]:
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter and line.startswith("description:"):
            return line.split(":", 1)[1].strip().strip('"')[:220]
    return first_heading(text)


def parse_frontmatter_name(text: str) -> str | None:
    for line in text.splitlines()[:20]:
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unknown"
