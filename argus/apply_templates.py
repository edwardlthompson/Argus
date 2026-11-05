"""File body templates for auto_safe content PRs."""

from __future__ import annotations

TEMPLATES: dict[str, tuple[str, str]] = {
    "HYGIENE-SECURITY-MD": (
        "SECURITY.md",
        "# Security Policy\n\nReport vulnerabilities privately via GitHub Security Advisories.\n",
    ),
    "HYGIENE-CONTRIBUTING": (
        "CONTRIBUTING.md",
        "# Contributing\n\n1. Open an issue or PR.\n2. Keep changes focused.\n3. Run tests before review.\n",
    ),
    "HYGIENE-COC": (
        "CODE_OF_CONDUCT.md",
        "# Code of Conduct\n\nBe respectful. Harassment is not tolerated.\n",
    ),
    "HYGIENE-GITATTRIBUTES": (
        ".gitattributes",
        "* text=auto eol=lf\n*.py text eol=lf\n*.md linguist-documentation=true\n",
    ),
    "HYGIENE-LICENSE": (
        "LICENSE",
        "MIT License\n\nCopyright (c) contributors\n\nPermission is hereby granted...\n",
    ),
    "HYGIENE-CI": (
        ".github/workflows/ci.yml",
        (
            "name: ci\non:\n  push:\n    branches: [main, master]\n  pull_request:\n"
            "jobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - uses: actions/checkout@v4\n      - run: echo ok\n"
        ),
    ),
    "HYGIENE-CODEOWNERS": (
        ".github/CODEOWNERS",
        "# Default owners — edit after merge\n* @OWNER\n",
    ),
    "HYGIENE-GITIGNORE": (
        ".gitignore",
        (
            ".venv/\n__pycache__/\n*.py[cod]\n.pytest_cache/\n.mypy_cache/\n"
            "dist/\nbuild/\n.env\n.DS_Store\nThumbs.db\n"
        ),
    ),
    "SEC-CODEQL-WORKFLOW": (
        ".github/workflows/codeql.yml",
        (
            "name: CodeQL\non:\n  push:\n    branches: [main, master]\n  pull_request:\n"
            "  schedule:\n    - cron: '0 6 * * 1'\n"
            "jobs:\n  analyze:\n    runs-on: ubuntu-latest\n"
            "    permissions:\n      security-events: write\n      contents: read\n"
            "    steps:\n      - uses: actions/checkout@v4\n"
            "      - uses: github/codeql-action/init@v3\n        with:\n          languages: python\n"
            "      - uses: github/codeql-action/analyze@v3\n"
        ),
    ),
}


def file_from_template(fix_id: str) -> tuple[str, str] | None:
    return TEMPLATES.get(fix_id)
