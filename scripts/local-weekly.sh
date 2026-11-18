#!/usr/bin/env bash
# PC fallback when GitHub Actions cannot run argus-weekly (billing / spending limit).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -z "${GITHUB_TOKEN:-}${ARGUS_GITHUB_TOKEN:-}" ]]; then
  echo "Set GITHUB_TOKEN or ARGUS_GITHUB_TOKEN before local-weekly" >&2
  exit 1
fi
PY=python3
[[ -x .venv/bin/python ]] && PY=.venv/bin/python
DRY=()
SKIP=()
LOOP=6
SLEEP=60
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY=(--dry-run); shift ;;
    --apply) DRY=(--apply); shift ;;
    --skip-merge) SKIP=(--skip-merge); shift ;;
    --loop) LOOP="$2"; shift 2 ;;
    --sleep) SLEEP="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ ${#DRY[@]} -eq 0 ]] && DRY=(--apply)
echo "local-weekly fallback (Actions-out)…"
"$PY" -m argus local-weekly "${DRY[@]}" "${SKIP[@]}" --loop "$LOOP" --sleep "$SLEEP"
echo "local-weekly ok"
