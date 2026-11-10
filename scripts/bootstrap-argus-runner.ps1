# Bootstrap a private Argus runner from the public product repo.
# Usage (from a clone of public Argus):
#   pwsh -File scripts/bootstrap-argus-runner.ps1 [-Name argus-runner] [-Owner YOUR_LOGIN]
# Requires: gh auth with repo + workflow scopes.

param(
    [string]$Owner = "",
    [string]$Name = "argus-runner"
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

if (-not $Owner) {
    $Owner = (gh api user --jq .login)
}
$full = "$Owner/$Name"

$exists = $true
try { gh repo view $full | Out-Null } catch { $exists = $false }

if (-not $exists) {
    Write-Host "Creating private repo $full ..."
    gh repo create $full --private --description "Private Argus control-plane runner (scans, apply, inbox)."
}

Write-Host "Pushing current HEAD to ${full}:main ..."
git push "https://github.com/$full.git" "HEAD:main"

Write-Host "Setting ARGUS_GITHUB_TOKEN secret from gh auth token ..."
gh auth token | gh secret set ARGUS_GITHUB_TOKEN --repo $full

$inbox = @"
# Private runner control plane.
enabled: true
controller_repo: $full
label_inbox: argus-inbox
label_security: argus-security
security_issues: true
max_issues_per_run: 20
"@
$b64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($inbox))
$sha = $null
try {
    $sha = (gh api "repos/$full/contents/config/inbox.yaml" --jq .sha)
} catch { }
$payload = @{ message = "chore(runner): inbox defaults for $full"; content = $b64; branch = "main" }
if ($sha) { $payload.sha = $sha }
$payload | ConvertTo-Json | gh api -X PUT "repos/$full/contents/config/inbox.yaml" --input - | Out-Null

# Arm YOLO on the private runner only (public product stays apply_mode: normal).
$yoloOn = "Argus private runner — YOLO armed. Delete this file or write YOLO-OFF.md to kill.`n"
$yoloB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($yoloOn))
$yoloSha = $null
try { $yoloSha = (gh api "repos/$full/contents/yolo.on" --jq .sha) } catch { }
$yoloPayload = @{ message = "chore(runner): arm YOLO (yolo.on)"; content = $yoloB64; branch = "main" }
if ($yoloSha) { $yoloPayload.sha = $yoloSha }
$yoloPayload | ConvertTo-Json | gh api -X PUT "repos/$full/contents/yolo.on" --input - | Out-Null

$safety = @"
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
  auto_merge_dependabot_patch: true
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
"@
$safetyB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($safety))
$safetySha = $null
try { $safetySha = (gh api "repos/$full/contents/config/safety.yaml" --jq .sha) } catch { }
$safetyPayload = @{ message = "chore(runner): apply_mode yolo for private controller"; content = $safetyB64; branch = "main" }
if ($safetySha) { $safetyPayload.sha = $safetySha }
$safetyPayload | ConvertTo-Json | gh api -X PUT "repos/$full/contents/config/safety.yaml" --input - | Out-Null

Write-Host "Triggering first YOLO scan (unset apply → safety.yaml implies apply) ..."
gh workflow run argus-scan --repo $full -f notify=true

Write-Host "OK runner (YOLO armed): https://github.com/$full"
Write-Host "Kill switch: delete yolo.on or add YOLO-OFF.md on the runner."
