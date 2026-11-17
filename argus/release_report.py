"""Markdown + HTML report for `argus releases` (private dist/ artifacts)."""

from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

from argus.paths import DIST_DIR, ensure_runtime_dirs


def grandma_lines(flagged: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for row in flagged:
        missing = "; ".join(row.get("missing") or []) or "release hygiene"
        pr = row.get("pr_url") or "(no PR — dry-run or irregular)"
        lines.append(f"{row.get('full_name')}: {missing} — {pr}")
    return lines


def compose_markdown(rows: list[dict[str, Any]], *, dry_run: bool, listing: str | None = None) -> str:
    flagged = [r for r in rows if r.get("needs_prep")]
    hot_repos = [r for r in rows if any((w.get("hot") or []) for w in (r.get("workflows") or []))]
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Argus release freshness",
        "",
        f"Generated {now}. Mode: `{'dry-run' if dry_run else 'open-prs'}`. Local CLI only — not GitHub Actions.",
        "",
        "## Grandma list",
        "",
    ]
    if not flagged:
        lines.append("_No repos flagged._")
    else:
        lines.append("| Repo | Platforms | Last release | What's missing | PR |")
        lines.append("|------|-----------|--------------|----------------|----|")
        for r in flagged:
            last = r.get("latest_tag") or "none"
            if r.get("latest_date"):
                last = f"{last} ({r['latest_date']})"
            pr = r.get("pr_url") or ("irregular — see runbook" if r.get("irregular") else "dry-run")
            lines.append(
                f"| {r.get('full_name')} | {', '.join(r.get('platforms') or []) or '—'} "
                f"| {last} | {'; '.join(r.get('missing') or [])} | {pr} |"
            )
    priv_n = sum(1 for r in hot_repos if r.get("private") or r.get("visibility") == "private")
    pub_n = len(hot_repos) - priv_n
    lines += [
        "",
        "## Actions minutes (existing workflows — not changed)",
        "",
        "Public repos get free standard GitHub-hosted minutes. Private repos do not. "
        "macOS is ~10× a Linux minute. This section only **lists** push/PR/schedule workflows; "
        "Argus does not edit them.",
        f"{priv_n} private repo(s) with push/PR/schedule workflows (billed). "
        f"{pub_n} public (standard minutes free).",
        *(
            [
                "",
                "_This scan listed **public** repos only (`/users/{user}/repos`). "
                "Re-run locally with a classic `repo` PAT so `/user/repos` includes private repos (billed minutes)._",
            ]
            if listing == "user_public"
            else []
        ),
        "",
        "| Repo | Visibility | Workflow | Triggers |",
        "|------|------------|----------|----------|",
    ]
    any_hot = False
    for r in hot_repos:
        vis = r.get("visibility") or ("private" if r.get("private") else "public")
        note = "private (billed)" if vis == "private" else "public (standard minutes free)"
        for w in r.get("workflows") or []:
            if not w.get("hot"):
                continue
            any_hot = True
            lines.append(f"| {r.get('full_name')} | {note} | `{w.get('path')}` | {', '.join(w.get('hot') or [])} |")
    if not any_hot:
        lines.append("| — | — | _none with push/PR/schedule_ | — |")
    lines += ["", "## Skipped", ""]
    skipped = [r for r in rows if r.get("skip")]
    if not skipped:
        lines.append("_None._")
    else:
        for r in skipped:
            lines.append(f"- `{r.get('full_name')}` — {r.get('skip')}")
    return "\n".join(lines).rstrip() + "\n"


def compose_html(md_rows: list[dict[str, Any]], *, dry_run: bool) -> str:
    flagged = [r for r in md_rows if r.get("needs_prep")]
    bits: list[str] = []
    for r in flagged:
        link = ""
        if r.get("pr_url"):
            href = escape(str(r.get("pr_url")))
            link = f' · <a href="{href}">PR</a>'
        miss = escape("; ".join(r.get("missing") or []) or "release hygiene")
        bits.append(f"<li><strong>{escape(str(r.get('full_name')))}</strong> — {miss}{link}</li>")
    items = "".join(bits) or "<li>No repos flagged.</li>"
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'/>"
        "<title>Argus release freshness</title></head><body>"
        f"<h1>Release freshness ({'dry-run' if dry_run else 'open-prs'})</h1>"
        "<p>Local CLI report. Not published to Pages. Argus never cuts tags.</p>"
        f"<h2>Needs you</h2><ol>{items}</ol>"
        "<p>See <code>dist/releases-report.md</code> for the Actions-minutes table.</p>"
        "</body></html>\n"
    )


def write_reports(
    rows: list[dict[str, Any]], *, dry_run: bool, dist_dir: Path | None = None, listing: str | None = None,
) -> dict[str, Path]:
    ensure_runtime_dirs()
    out = dist_dir or DIST_DIR
    out.mkdir(parents=True, exist_ok=True)
    md, html = compose_markdown(rows, dry_run=dry_run, listing=listing), compose_html(rows, dry_run=dry_run)
    md_path, html_path = out / "releases-report.md", out / "releases-report.html"
    md_path.write_text(md, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    return {"markdown": md_path, "html": html_path}
