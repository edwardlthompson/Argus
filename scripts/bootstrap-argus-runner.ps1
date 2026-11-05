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

Write-Host "Triggering dry-run scan ..."
gh workflow run argus-scan --repo $full -f apply=false -f notify=false

Write-Host "OK runner: https://github.com/$full"
Write-Host "Next: merge/watch Actions; later re-run scan with apply=true when ready."
