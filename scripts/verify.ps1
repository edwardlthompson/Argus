$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m pytest
python -c "from argus.config_loader import load_fixes, load_rubric; load_fixes(); load_rubric(); print('config ok')"
python -m ruff check argus tests
python scripts/agent-run.py check-file-encoding
python scripts/agent-run.py update-deps -- --audit
Write-Host "verify ok"
