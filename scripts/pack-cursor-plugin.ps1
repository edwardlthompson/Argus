$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Out = Join-Path $Root "dist\cursor-plugin"
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$Plugin = Join-Path $Root ".cursor-plugin"
if (Test-Path $Plugin) {
  Copy-Item -Recurse -Force $Plugin (Join-Path $Out "plugin")
}
@(".cursor\commands", ".cursor\skills", ".cursor\agents", ".cursor\hooks") | ForEach-Object {
  $src = Join-Path $Root $_
  if (Test-Path $src) {
    $dest = Join-Path $Out ($_ -replace "^\.cursor\\", "")
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item -Recurse -Force "$src\*" $dest
  }
}
Write-Host "Packed argus-foss plugin stubs to $Out"
