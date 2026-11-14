#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 -c 'import sys; assert (3,11) <= sys.version_info[:2] <= (3,12), "Gunakan Python 3.11/3.12"'
python3 -m venv .venv
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python scripts/seed_demo.py
