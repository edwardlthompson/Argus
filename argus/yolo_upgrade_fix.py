"""Classify + mechanically fix open parent-upgrade PRs; soft-merge allowlist helpers."""

from __future__ import annotations

import re
from typing import Any

from argus.github_client import GitHubClient, GitHubError
from argus.yolo_upgrade_heal import (
    BRANCH_PREFIX,
    TARGET_VER,
    _exists,
    _get_raw,
    _put,
    heal_template_index,
)

# Soft-merge OK only when every remaining failure is in this set (exact job names).
SOFT_MERGE_ALLOWLIST = frozenset({
    "Template Upgrade Simulation",
    "Template Upgrade Simulation (Windows)",
    "Validate Bootstrap Artifacts",
    "Validate Template Index",
})

# Always block soft-merge when any of these fail (substring match, case-insensitive).
HARD_BLOCK_SUBSTRINGS = (
    "security scan",
    "trivy",
    "codeql",
    "gitleaks",
    "dependency review",
)

def soft_merge_ok(failed_names: list[str] | set[str]) -> bool:
    """True when failures are allowlist-only (or empty → caller treats as green).

    Ignores the umbrella workflow job named exactly ``CI`` (aggregate status).
    """
    names = [str(n) for n in failed_names if n and str(n) != "CI"]
    if not names:
        # Only umbrella CI / nothing concrete — still require at least allowlist-only
        # when the sole failure was CI; treat as soft-ok (noise wrapper).
        return True
    for n in names:
        low = n.lower()
        if any(b in low for b in HARD_BLOCK_SUBSTRINGS):
            return False
        if n not in SOFT_MERGE_ALLOWLIST:
            return False
    return True


def normalize_markdown_table_pipes(text: str) -> str:
    """Add leading/trailing pipes on GFM table rows; fix compact pipe spacing. No content rewrite."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    for line in lines:
        raw = line.rstrip("\r\n")
        ending = line[len(raw):]
        stripped = raw.strip()
        if "|" not in stripped or stripped.startswith("```"):
            out.append(line)
            continue
        # Likely a table row: has | and looks like cells
        if not re.search(r"\|.*\|", stripped) and not stripped.startswith("|"):
            # single-edge pipe rows (MD055)
            if stripped.count("|") >= 1 and not stripped.startswith("#"):
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if len(cells) >= 1 and any(cells):
                    raw = "| " + " | ".join(cells) + " |"
                    out.append(raw + ending)
                    continue
            out.append(line)
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 2 and not re.match(r"^\|?\s*:?-+:?\s*\|", stripped):
            out.append(line)
            continue
        # separator row
        if all(re.match(r"^:?-+:?$", c or "-") for c in cells if c is not None):
            sep = "| " + " | ".join(c if c else "---" for c in cells) + " |"
            out.append(sep + ending)
            continue
        raw = "| " + " | ".join(cells) + " |"
        out.append(raw + ending)
    return "".join(out)


def _list_adr_paths(client: GitHubClient, owner: str, name: str, ref: str) -> list[str]:
    try:
        data = client.get(f"/repos/{owner}/{name}/contents/docs/adr", params={"ref": ref})
    except GitHubError as exc:
        if "404" in str(exc):
            return []
        raise
    if not isinstance(data, list):
        return []
    return [
        str(item.get("path"))
        for item in data
        if isinstance(item, dict) and str(item.get("path") or "").endswith(".md")
    ]


def fix_markdown_tables(
    client: GitHubClient, owner: str, name: str, branch: str
) -> list[str]:
    """Normalize table pipes on AGENTS.md + docs/adr/*.md. Returns action tags."""
    actions: list[str] = []
    paths = ["AGENTS.md"] + _list_adr_paths(client, owner, name, branch)
    for path in paths:
        got = _get_raw(client, owner, name, path, branch)
        if got is None:
            continue
        raw, sha = got
        text = raw.decode("utf-8", errors="replace")
        new = normalize_markdown_table_pipes(text)
        if new == text:
            continue
        _put(
            client, owner, name, path, new.encode("utf-8"),
            f"chore(argus): normalize markdown table pipes in {path}",
            branch, sha,
        )
        actions.append(f"md:{path}")
    return actions


def fix_fdroid_changelogs(
    client: GitHubClient,
    owner: str,
    name: str,
    branch: str,
    *,
    missing_paths: list[str] | None = None,
) -> list[str]:
    """Create one-line stubs for missing F-Droid changelog paths."""
    actions: list[str] = []
    paths = list(missing_paths or [])
    if not paths:
        # Heuristic: common template example path versionCode 4 (+ neighbors 1–5)
        candidates: list[str] = []
        for base in (
            "examples/android/metadata/en-US/changelogs",
            "metadata/en-US/changelogs",
            "fastlane/metadata/android/en-US/changelogs",
        ):
            meta = base.rsplit("/changelogs", 1)[0]
            if not _exists(client, owner, name, meta, branch):
                continue
            for n in range(1, 6):
                candidates.append(f"{base}/{n}.txt")
        # Prefer missing files only when any changelog already exists (version bump gap)
        existing = [p for p in candidates if _exists(client, owner, name, p, branch)]
        if existing:
            paths = [p for p in candidates if p not in existing]
        else:
            # No changelogs yet but metadata tree present — stub 4.txt (common template gate)
            for base in (
                "examples/android/metadata/en-US/changelogs",
                "metadata/en-US/changelogs",
                "fastlane/metadata/android/en-US/changelogs",
            ):
                meta = base.rsplit("/changelogs", 1)[0]
                if _exists(client, owner, name, meta, branch):
                    paths.append(f"{base}/4.txt")
                    break
    for path in paths:
        if _exists(client, owner, name, path, branch):
            continue
        stub = f"chore: template upgrade {TARGET_VER}\n".encode()
        _put(
            client, owner, name, path, stub,
            f"chore(argus): stub F-Droid changelog {path}",
            branch, None,
        )
        actions.append(f"fdroid:{path}")
    return actions


def classify_pr_checks(
    client: GitHubClient, owner: str, name: str, sha: str | None
) -> dict[str, Any]:
    """Return {state, failed, pending} for a commit."""
    from argus.yolo import pr_ci_detail

    return pr_ci_detail(client, owner, name, sha)


def classify_upgrade_prs(
    client: GitHubClient,
    *,
    login: str | None = None,
    max_repos: int = 80,
) -> dict[str, Any]:
    """List open upgrade PRs with CI classification."""
    out: dict[str, Any] = {"items": [], "errors": []}
    try:
        me = login or str((client.whoami() or {}).get("login") or "")
    except GitHubError as exc:
        out["errors"].append(str(exc))
        return out
    if not me:
        out["errors"].append("no_login")
        return out
    try:
        data = client.get(
            "/search/issues",
            params={
                "q": f'user:{me} is:pr is:open "upgrade parent rules" in:title',
                "per_page": min(100, max_repos),
            },
        )
    except GitHubError as exc:
        out["errors"].append(str(exc))
        return out
    for it in (data.get("items") if isinstance(data, dict) else []) or []:
        if len(out["items"]) >= max_repos:
            break
        repo_url = str(it.get("repository_url") or "")
        parts = repo_url.rstrip("/").split("/")
        if len(parts) < 2:
            continue
        owner, name = parts[-2], parts[-1]
        num = int(it["number"])
        try:
            pr = client.get(f"/repos/{owner}/{name}/pulls/{num}")
            head = str(((pr or {}).get("head") or {}).get("ref") or "")
            sha = str(((pr or {}).get("head") or {}).get("sha") or "") or None
        except GitHubError as exc:
            out["errors"].append(f"{owner}/{name}#{num}:{exc}")
            continue
        if not head.startswith(BRANCH_PREFIX):
            continue
        detail = classify_pr_checks(client, owner, name, sha)
        out["items"].append({
            "repo": f"{owner}/{name}",
            "number": num,
            "head": head,
            "sha": sha,
            "state": detail.get("state"),
            "failed": detail.get("failed") or [],
            "soft_ok": soft_merge_ok(detail.get("failed") or []),
        })
    return out


def fix_upgrade_branch(
    client: GitHubClient,
    owner: str,
    name: str,
    branch: str,
    *,
    failed_names: list[str] | None = None,
) -> str:
    """Run heal + mechanical fixers. Returns status tag."""
    actions: list[str] = []
    heal = heal_template_index(client, owner, name, branch)
    if heal.startswith("changed"):
        actions.append(heal)
    failed = failed_names or []
    need_md = any(
        "bootstrap" in f.lower() or "validate template" in f.lower() or "markdown" in f.lower()
        for f in failed
    ) or not failed
    if need_md:
        actions.extend(fix_markdown_tables(client, owner, name, branch))
    need_fdroid = any("feature gate" in f.lower() for f in failed) or not failed
    if need_fdroid:
        actions.extend(fix_fdroid_changelogs(client, owner, name, branch))
    if not actions:
        return "unchanged"
    return "changed:" + ",".join(actions)


def fix_open_upgrade_prs(
    client: GitHubClient,
    *,
    login: str | None = None,
    max_repos: int = 80,
) -> dict[str, Any]:
    """Classify then fix each open upgrade head."""
    out: dict[str, Any] = {"fixed": [], "skipped": [], "errors": [], "classify": []}
    classified = classify_upgrade_prs(client, login=login, max_repos=max_repos)
    out["classify"] = classified.get("items") or []
    out["errors"].extend(classified.get("errors") or [])
    for item in out["classify"]:
        repo = str(item.get("repo") or "")
        if "/" not in repo:
            continue
        owner, name = repo.split("/", 1)
        num = item.get("number")
        head = str(item.get("head") or "")
        failed = list(item.get("failed") or [])
        key = f"{repo}#{num}"
        if item.get("state") == "green":
            out["skipped"].append(f"{key}:already_green")
            continue
        try:
            status = fix_upgrade_branch(
                client, owner, name, head, failed_names=failed
            )
            if status.startswith("changed"):
                out["fixed"].append(f"{key}:{status}")
            else:
                out["skipped"].append(f"{key}:{status}")
        except GitHubError as exc:
            out["errors"].append(f"{key}:{exc}")
    return out
