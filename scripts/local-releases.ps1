# Local release-freshness scan (REST only). Do not run from GitHub Actions.
param(
    [switch]$OpenPrs,
    [string]$Owner = "",
    [string]$Repo = "",
    [int]$MaxPrs = 0,
    [switch]$PublicOnly,
    [switch]$Notify
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not ($env:GITHUB_TOKEN -or $env:ARGUS_GITHUB_TOKEN)) {
    throw "Set GITHUB_TOKEN or ARGUS_GITHUB_TOKEN before local-releases"
}
$py = "python"
if (Test-Path .\.venv\Scripts\python.exe) { $py = ".\.venv\Scripts\python.exe" }
$cli = @("releases")
if ($OpenPrs) { $cli += "--open-prs" } else { $cli += "--dry-run" }
if ($Owner) { $cli += @("--owner", $Owner) }
if ($Repo) { $cli += @("--repo", $Repo) }
if ($MaxPrs -gt 0) { $cli += @("--max-prs", "$MaxPrs") }
if ($PublicOnly) { $cli += "--public-only" }
if ($Notify) { $cli += "--notify" }
Write-Host "local-releases (not Actions)…"
& $py -m argus @cli
Write-Host "local-releases ok — see dist/releases-report.md"
