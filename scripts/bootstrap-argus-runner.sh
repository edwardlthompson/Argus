#!/usr/bin/env bash
# Bootstrap a private Argus runner from the public product repo.
# Usage: bash scripts/bootstrap-argus-runner.sh [owner] [name]
set -euo pipefail
cd "$(dirname "$0")/.."
OWNER="${1:-$(gh api user --jq .login)}"
NAME="${2:-argus-runner}"
FULL="${OWNER}/${NAME}"

if ! gh repo view "$FULL" >/dev/null 2>&1; then
  echo "Creating private repo ${FULL} ..."
  gh repo create "$FULL" --private --description "Private Argus control-plane runner (scans, apply, inbox)."
fi

echo "Pushing current HEAD to ${FULL}:main ..."
git push "https://github.com/${FULL}.git" "HEAD:main"

echo "Setting ARGUS_GITHUB_TOKEN secret from gh auth token ..."
gh auth token | gh secret set ARGUS_GITHUB_TOKEN --repo "$FULL"

INBOX=$(cat <<EOF
# Private runner control plane.
enabled: true
controller_repo: ${FULL}
label_inbox: argus-inbox
label_security: argus-security
security_issues: true
max_issues_per_run: 20
EOF
)
B64=$(printf '%s' "$INBOX" | base64 | tr -d '\n')
SHA=$(gh api "repos/${FULL}/contents/config/inbox.yaml" --jq .sha 2>/dev/null || true)
ARGS=( -f message="chore(runner): inbox defaults for ${FULL}" -f content="$B64" -f branch=main )
if [[ -n "${SHA}" ]]; then ARGS+=( -f sha="$SHA" ); fi
gh api -X PUT "repos/${FULL}/contents/config/inbox.yaml" "${ARGS[@]}" >/dev/null

# Arm YOLO on the private runner only (public product stays apply_mode: normal).
YOLO_ON="Argus private runner — YOLO armed. Delete this file or write YOLO-OFF.md to kill.
"
YOLO_B64=$(printf '%s' "$YOLO_ON" | base64 | tr -d '\n')
YOLO_SHA=$(gh api "repos/${FULL}/contents/yolo.on" --jq .sha 2>/dev/null || true)
YARGS=( -f message="chore(runner): arm YOLO (yolo.on)" -f content="$YOLO_B64" -f branch=main )
if [[ -n "${YOLO_SHA}" ]]; then YARGS+=( -f sha="$YOLO_SHA" ); fi
gh api -X PUT "repos/${FULL}/contents/yolo.on" "${YARGS[@]}" >/dev/null

SAFETY=$(cat <<'EOF'
# Private runner — hands-off YOLO (public product template stays apply_mode: normal).
max_auto_prs_per_run: 25
max_auto_prs_per_owner: 25
max_concurrent_agent_sessions: 8
max_agent_prompt_chars: 12000
max_gate_failures_before_pause: 2
prefer_pull_requests: true
never_delete_repos: true
never_force_push: true
attention_threshold_for_agents: 60
apply_mode: yolo
yolo:
  skip_profile: true
  auto_merge_auto_safe: true
  auto_merge_dependabot: true
  auto_merge_dependabot_patch: true
  dependabot_auto_merge_levels: [patch, minor, major]
  auto_dispatch_agents: true
  auto_merge_agent_prs: true
  max_auto_merges_per_day: 80
  max_yolo_actions_per_run: 100
  close_stale_bot_prs_days: 14
  second_pass_if_budget: true
  stale_pr_idle_days: 30
github_api:
  core_limit_hint: 5000
  reserve: 250
  min_interval_ms: 80
  max_interval_ms: 2000
  calls_per_repo_estimate: 50
  max_repos_per_batch: 6
  max_wait_seconds: 3700
EOF
)
SAFETY_B64=$(printf '%s' "$SAFETY" | base64 | tr -d '\n')
SAFETY_SHA=$(gh api "repos/${FULL}/contents/config/safety.yaml" --jq .sha 2>/dev/null || true)
SARGS=( -f message="chore(runner): apply_mode yolo for private controller" -f content="$SAFETY_B64" -f branch=main )
if [[ -n "${SAFETY_SHA}" ]]; then SARGS+=( -f sha="$SAFETY_SHA" ); fi
gh api -X PUT "repos/${FULL}/contents/config/safety.yaml" "${SARGS[@]}" >/dev/null

echo "Triggering first YOLO scan (unset apply → safety.yaml implies apply) ..."
gh workflow run argus-scan --repo "$FULL" -f notify=true

echo "OK runner (YOLO armed): https://github.com/${FULL}"
echo "Kill switch: delete yolo.on or add YOLO-OFF.md on the runner."
