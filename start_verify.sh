#!/usr/bin/env bash
# One command to open the verification queue. Creates a local virtualenv on first run
# (a bare `pip install` fails on modern macOS/Debian with "externally-managed-environment"),
# installs dependencies, starts the app, and opens it in a browser where possible.
#
#   ./start_verify.sh            # http://127.0.0.1:8765
#   ./start_verify.sh 8899       # a different port, if 8765 is taken
set -euo pipefail
cd "$(dirname "$0")"

PORT="${1:-8765}"
URL="http://127.0.0.1:${PORT}"

PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "Need Python 3.11 or newer on PATH (tried python3, python, py)." >&2
  echo "macOS: brew install python@3.12   Ubuntu/Debian: sudo apt install python3 python3-venv" >&2
  exit 1
fi

if [ ! -x .venv/bin/python ] && [ ! -x .venv/Scripts/python.exe ]; then
  echo "Creating .venv ..."
  "$PY" -m venv .venv || {
    echo "venv creation failed. On Debian/Ubuntu: sudo apt install python3-venv" >&2
    exit 1
  }
fi
VENV_PY=".venv/bin/python"
[ -x "$VENV_PY" ] || VENV_PY=".venv/Scripts/python.exe"

echo "Installing dependencies (first run only) ..."
"$VENV_PY" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
"$VENV_PY" -m pip install --quiet -r requirements.txt

echo
echo "Verification queue: $URL"
echo "Press Ctrl-C to stop. Promoted records land in records/verified/ — commit and push that folder."
echo

( sleep 2
  if command -v open >/dev/null 2>&1; then open "$URL" >/dev/null 2>&1 || true          # macOS
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 || true # Linux
  fi ) &

exec "$VENV_PY" tools/verify_ui.py --port "$PORT"
