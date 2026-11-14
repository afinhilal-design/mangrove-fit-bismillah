#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
exec .venv/bin/python -m streamlit run app.py --server.address localhost
