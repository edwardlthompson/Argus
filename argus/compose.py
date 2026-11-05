"""Compose runbook.md and report.html from repo plans. Deterministic — no LLMs."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from argus.models import Confidence, MatchedFix, RepoPlan
from argus.paths import DIST_DIR, TEMPLATES_DIR, ensure_runtime_dirs
from argus.report_view import build_report_view
from argus.status_page import write_status_artifacts


def _topo_phases(fixes: list[MatchedFix]) -> dict[int, list[MatchedFix]]:
    """Group by phase, respecting depends_on order within phases."""
    by_id = {m.fix.id: m for m in fixes}
    remaining = set(by_id)
    ordered: list[MatchedFix] = []
    while remaining:
        progress = False
        for fid in sorted(remaining):
            deps = by_id[fid].fix.depends_on
            if all(d not in remaining for d in deps):
                ordered.append(by_id[fid])
                remaining.remove(fid)
                progress = True
        if not progress:
            ordered.extend(sorted((by_id[i] for i in remaining), key=lambda m: (m.fix.phase, m.fix.id)))
            break
    phases: dict[int, list[MatchedFix]] = defaultdict(list)
    for m in ordered:
        phases[m.fix.phase].append(m)
    return dict(sorted(phases.items()))


def _agent_prompt_block(
    repo_name: str,
    agent_fixes: list[MatchedFix],
    *,
    max_chars: int,
) -> tuple[str, list[MatchedFix]]:
    if not agent_fixes:
        return "", []

    phases = _topo_phases(agent_fixes)
    included: list[MatchedFix] = []
    deferred: list[MatchedFix] = []
    parts: list[str] = [
        f"### Agent prompt for `{repo_name}`",
        "",
        "Paste this entire block into your coding agent. Stop if any GATE fails twice.",
        "",
        "```text",
        f"Repository: {repo_name}",
        "You are performing gated Argus hygiene/correctness work.",
        "Prefer opening a PR over committing to the default branch.",
        "",
    ]

    for phase, items in phases.items():
        header = f"## Phase {phase}"
        body_lines = [header, ""]
        for m in items:
            if m.fix.confidence == Confidence.LOW:
                body_lines.append("> unverified — check before pasting")
                body_lines.append("")
            body_lines.append(f"### {m.fix.id}: {m.fix.title}")
            body_lines.append(m.fix.why)
            if m.fix.agent_prompt:
                body_lines.append(m.fix.agent_prompt.strip())
            body_lines.append("")

        gate = items[-1].fix.gate or "true"
        body_lines.append(f"GATE: {gate}")
        body_lines.append("")

        candidate = "\n".join(parts + body_lines)
        if len(candidate) > max_chars and included:
            deferred.extend(items)
            continue
        parts.extend(body_lines)
        included.extend(items)

    parts.extend(
        [
            "## Phase final — verify & PR",
            "",
            "1. Run project tests / verify script if present.",
            "2. Add a hand-written CHANGELOG note under [Unreleased] listing fix IDs: "
            + ", ".join(m.fix.id for m in included),
            "3. Push branch `chore/argus-agent` (or continue the existing Argus branch).",
            "4. Open a Pull Request whose body lists the fix IDs above.",
            "",
            "GATE: gh pr view --json url,title || test -f .git/ARGUS_PR_OPENED",
            "```",
            "",
        ]
    )
    return "\n".join(parts), deferred


def compose_runbook(
    plans: list[RepoPlan],
    *,
    max_prompt_chars: int = 12000,
    report_banner: str | None = None,
) -> str:
    lines: list[str] = [
        "# Argus Runbook",
        "",
        f"Generated for {len(plans)} repositories.",
        "",
    ]
    if report_banner:
        lines.extend([f"> {report_banner}", ""])

    for plan in plans:
        repo = plan.repo.full_name
        lines.append(f"## {repo}")
        lines.append("")
        conf = plan.score.confidence.value
        if plan.score.confidence == Confidence.LOW:
            lines.append(f"**Attention:** needs human read (low confidence) — raw score {plan.score.attention}/100")
        else:
            lines.append(f"**Attention:** {plan.score.attention}/100 ({conf} confidence)")
        if plan.score.notes:
            lines.append(f"_Notes:_ {'; '.join(plan.score.notes)}")
        lines.append("")

        if plan.human_fixes:
            lines.append("### Human tasks")
            lines.append("")
            for i, m in enumerate(plan.human_fixes, start=1):
                lines.append(f"#### H{i}. {m.fix.title}")
                lines.append("")
                lines.append(f"**Why:** {m.fix.why}")
                lines.append("")
                lines.append(m.fix.human_steps.strip())
                lines.append("")
                lines.append(f"**Done when:** {m.fix.gate or 'The steps above are complete.'}")
                lines.append("")

        if plan.agent_fixes:
            block, deferred = _agent_prompt_block(repo, plan.agent_fixes, max_chars=max_prompt_chars)
            lines.append(block)
            if deferred:
                lines.append("### Deferred (not in paste block)")
                lines.append("")
                for m in deferred:
                    lines.append(f"- `{m.fix.id}` — {m.fix.title}")
                lines.append("")

        if plan.auto_fixes and not plan.report_only:
            lines.append("### Auto-safe (controller may open PRs)")
            lines.append("")
            for m in plan.auto_fixes:
                lines.append(f"- `{m.fix.id}` — {m.fix.title} — GATE: `{m.fix.gate}`")
            lines.append("")

        if not plan.human_fixes and not plan.agent_fixes and not plan.auto_fixes:
            lines.append("_No open work._")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _jinja_env() -> Environment:
    ensure_runtime_dirs()
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def compose_html(
    plans: list[RepoPlan],
    *,
    report_banner: str | None = None,
    health_delta: dict | None = None,
    target_label: str = "portfolio",
    mode: str = "run",
    read_only: bool = False,
) -> str:
    view = build_report_view(
        plans,
        target_label=target_label,
        mode=mode,
        report_banner=report_banner,
        health_delta=health_delta,
        read_only=read_only,
    )
    return _jinja_env().get_template("report.html.j2").render(view=view)


def compose_portfolio_markdown(
    plans: list[RepoPlan],
    *,
    report_banner: str | None = None,
    health_delta: dict | None = None,
    target_label: str = "portfolio",
    mode: str = "run",
    read_only: bool = False,
) -> str:
    view = build_report_view(
        plans,
        target_label=target_label,
        mode=mode,
        report_banner=report_banner,
        health_delta=health_delta,
        read_only=read_only,
    )
    # Markdown template: disable HTML autoescape noise for MD
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)
    return env.get_template("portfolio_report.md.j2").render(view=view)


def compose_private_inbox_json(plans: list[RepoPlan]) -> dict:
    """Full task detail for Actions artifacts only — never publish to public Pages."""
    tasks = []
    for plan in plans:
        for m in plan.human_fixes:
            tasks.append(
                {
                    "repo": plan.repo.full_name,
                    "fix_id": m.fix.id,
                    "title": m.fix.title,
                    "why": m.fix.why,
                    "human_steps": m.fix.human_steps,
                    "gate": m.fix.gate,
                    "security": m.fix.id.upper().startswith("SEC-"),
                }
            )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "human_count": len(tasks),
        "tasks": tasks,
    }


def write_artifacts(
    plans: list[RepoPlan],
    *,
    max_prompt_chars: int = 12000,
    report_banner: str | None = None,
    health_delta: dict | None = None,
    dist_dir: Path | None = None,
    target_label: str = "portfolio",
    mode: str = "run",
    read_only: bool = False,
) -> dict[str, Path]:
    ensure_runtime_dirs()
    out = dist_dir or DIST_DIR
    out.mkdir(parents=True, exist_ok=True)
    runbook = compose_runbook(plans, max_prompt_chars=max_prompt_chars, report_banner=report_banner)
    html = compose_html(
        plans,
        report_banner=report_banner,
        health_delta=health_delta,
        target_label=target_label,
        mode=mode,
        read_only=read_only,
    )
    portfolio_md = compose_portfolio_markdown(
        plans,
        report_banner=report_banner,
        health_delta=health_delta,
        target_label=target_label,
        mode=mode,
        read_only=read_only,
    )
    md_path = out / "runbook.md"
    html_path = out / "report.html"
    portfolio_path = out / "portfolio-report.md"
    md_path.write_text(runbook, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    portfolio_path.write_text(portfolio_md, encoding="utf-8")
    (out / "inbox.json").write_text(
        json.dumps(compose_private_inbox_json(plans), indent=2) + "\n",
        encoding="utf-8",
    )
    write_status_artifacts(plans, dist_dir=out)
    return {
        "runbook": md_path,
        "report": html_path,
        "portfolio": portfolio_path,
    }
