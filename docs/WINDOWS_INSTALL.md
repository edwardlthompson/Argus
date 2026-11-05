# Windows install — PATH

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Ensure `python` and `argus` resolve:

```powershell
where.exe python
where.exe argus
# If argus missing: python -m argus --help
# Or add Scripts to PATH for the active venv:
$env:Path = "$(Resolve-Path .\.venv\Scripts);$env:Path"
```

Verify: `python scripts/agent-run.py verify`
