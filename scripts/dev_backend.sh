#!/usr/bin/env bash
# Start the MedNarrate API locally (no Docker) with the settings in
# mednarrate-backend/.env, replacing whatever is already listening on port 8000.
#
#   ./scripts/dev_backend.sh            check translation, then start the API
#   ./scripts/dev_backend.sh --no-check start the API only
set -euo pipefail
cd "$(dirname "$0")/../mednarrate-backend"

# The desktop app compares these with its own build values (see lib/main.dart)
# and refuses to open when the backend reports different ones ("Stale backend").
export MEDNARRATE_VERSION="${MEDNARRATE_VERSION:-1.0.0}"
export MEDNARRATE_COMMIT="${MEDNARRATE_COMMIT:-dev}"

PY=""
for candidate in .venv/bin/python venv/bin/python ../.venv/bin/python; do
  if [ -x "$candidate" ]; then PY="$candidate"; break; fi
done
if [ -z "$PY" ]; then echo "No virtualenv found in mednarrate-backend (.venv or venv)." >&2; exit 1; fi

if [ "${1:-}" != "--no-check" ]; then
  echo "== Checking translation with the real providers (about 20-60 seconds) =="
  "$PY" -m app.translation_check hi || echo "(translation check failed - the reason is printed above)"
  echo
fi

OLD=$(lsof -ti tcp:8000 || true)
if [ -n "$OLD" ]; then
  echo "Stopping the old process on port 8000 ($OLD)"
  kill $OLD || true
  sleep 1
fi

echo "== Starting API on http://127.0.0.1:8000 =="
exec "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
