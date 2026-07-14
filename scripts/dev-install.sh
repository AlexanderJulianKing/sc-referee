#!/usr/bin/env bash
# Reproduce the development environment from the committed lockfile.
set -euo pipefail
cd "$(dirname "$0")/.."

uv sync --locked --extra engine --extra dev --extra llm
uv run python -c "import sc_referee; print('dev install OK:', sc_referee.__version__)"
