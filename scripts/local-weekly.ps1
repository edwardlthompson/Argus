# PC fallback when GitHub Actions cannot run argus-weekly (billing / spending limit).
# Requires GITHUB_TOKEN or ARGUS_GITHUB_TOKEN in the environment.
param(
    [switch]$DryRun,
    [switch]$SkipMerge,
    [int]$Loop = 6,
    [int]$Sleep = 60
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not ($env:GITHUB_TOKEN -or $env:ARGUS_GITHUB_TOKEN)) {
    throw "Set GITHUB_TOKEN or ARGUS_GITHUB_TOKEN before local-weekly"
}

$py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
$argv = @("-m", "argus", "local-weekly", "--loop", "$Loop", "--sleep", "$Sleep")
if ($DryRun) { $argv += "--dry-run" } else { $argv += "--apply" }
if ($SkipMerge) { $argv += "--skip-merge" }

Write-Host "local-weekly fallback (Actions-out)…"
& $py @argv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "local-weekly ok"
