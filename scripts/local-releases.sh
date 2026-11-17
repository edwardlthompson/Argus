#!/usr/bin/env bash
# Local release-freshness scan (REST only). Do not run from GitHub Actions.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -z "${GITHUB_TOKEN:-}${ARGUS_GITHUB_TOKEN:-}" ]]; then
  echo "Set GITHUB_TOKEN or ARGUS_GITHUB_TOKEN before local-releases" >&2
  exit 1
fi
PY=python3
[[ -x .venv/bin/python ]] && PY=.venv/bin/python
MODE=(--dry-run)
EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) MODE=(--dry-run); shift ;;
    --open-prs) MODE=(--open-prs); shift ;;
    --owner|--repo|--max-prs) EXTRA+=("$1" "$2"); shift 2 ;;
    --public-only|--notify) EXTRA+=("$1"); shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
echo "local-releases (not Actions)…"
"$PY" -m argus releases "${MODE[@]}" "${EXTRA[@]}"
echo "local-releases ok — see dist/releases-report.md"
