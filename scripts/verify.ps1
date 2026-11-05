$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m pytest
python -c "from argus.config_loader import load_fixes, load_rubric; load_fixes(); load_rubric(); print('config ok')"
python -m ruff check argus tests
Write-Host "verify ok"
