"""Issue title/body/marker helpers for the Argus inbox."""

from __future__ import annotations

from argus.models import MatchedFix

MARKER_TMPL = "<!-- argus:{fix_id}:{repo} -->"
DONE_COMMENT = "argus done"


def issue_marker(fix_id: str, repo: str) -> str:
    return MARKER_TMPL.format(fix_id=fix_id, repo=repo)


def parse_marker(text: str) -> tuple[str, str] | None:
    """Return (fix_id, repo) from body if marker present."""
    if "<!-- argus:" not in text:
        return None
    start = text.find("<!-- argus:")
    end = text.find("-->", start)
    if end < 0:
        return None
    inner = text[start + len("<!-- argus:") : end].strip()
    if ":" not in inner:
        return None
    fix_id, _, rest = inner.partition(":")
    if "/" not in rest:
        return None
    return fix_id.strip(), rest.strip()


def build_issue_body(matched: MatchedFix, repo_full: str) -> str:
    fix = matched.fix
    settings = f"https://github.com/{repo_full}/settings"
    steps = (fix.human_steps or "").strip()
    gate = fix.gate or "The steps above are complete."
    marker = issue_marker(fix.id, repo_full)
    return (
        f"{marker}\n\n"
        f"**Repo:** [{repo_full}](https://github.com/{repo_full})\n\n"
        f"**Why:** {fix.why}\n\n"
        f"### Steps\n\n{steps}\n\n"
        f"**Done when:** {gate}\n\n"
        f"Settings: {settings}\n\n"
        f"_Close this issue or comment `{DONE_COMMENT}` when finished._\n"
    )


def build_issue_title(matched: MatchedFix, repo_full: str) -> str:
    return f"[Argus] {matched.fix.title} — {repo_full}"
