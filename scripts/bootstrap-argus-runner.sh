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

echo "Triggering dry-run scan ..."
gh workflow run argus-scan --repo "$FULL" -f apply=false -f notify=false

echo "OK runner: https://github.com/${FULL}"
echo "Next: watch Actions; later re-run with apply=true when ready."
