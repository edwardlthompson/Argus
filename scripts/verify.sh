#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pytest
python -c "from argus.config_loader import load_fixes, load_rubric; load_fixes(); load_rubric(); print('config ok')"
ruff check argus tests
echo "verify ok"
