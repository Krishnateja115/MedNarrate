#!/usr/bin/env bash
# Start the Docker stack using the values in mednarrate-backend/.env.
# (docker compose needs POSTGRES_PASSWORD, JWT_SECRET and CORS_ORIGINS at parse
# time; they live in that file, so it is passed with --env-file.)
set -euo pipefail
cd "$(dirname "$0")/.."
ENV_FILE=mednarrate-backend/.env
[ -f "$ENV_FILE" ] || { echo "$ENV_FILE not found" >&2; exit 1; }
docker compose --env-file "$ENV_FILE" -p mednarrate-audit up -d --build
echo "Waiting for the API..."
for _ in $(seq 1 60); do
  curl -fs http://127.0.0.1:8000/health >/dev/null 2>&1 && break
  sleep 2
done
docker compose --env-file "$ENV_FILE" -p mednarrate-audit exec backend python -m app.translation_check hi || true
