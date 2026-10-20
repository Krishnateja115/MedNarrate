#!/usr/bin/env bash
# Packs only what the SERVER needs (backend, admin portal, compose files, proxy config).
# Run on your Mac from the repository root:   bash deploy/make_bundle.sh
# Result: mednarrate-server.tar.gz  (no secrets, no databases, no uploads, no node_modules)
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="mednarrate-server.tar.gz"
COPYFILE_DISABLE=1 tar -czf "$OUT" \
  --exclude='._*' \
  --exclude='.git' --exclude='node_modules' --exclude='.next' \
  --exclude='.venv' --exclude='venv' --exclude='__pycache__' --exclude='.pytest_cache' \
  --exclude='.env' --exclude='.env.local' --exclude='.env.production' --exclude='.env.development' \
  --exclude='*.db' --exclude='*.sqlite*' --exclude='*.log' --exclude='*.tsbuildinfo' \
  --exclude='mednarrate-backend/uploads' --exclude='mednarrate-backend/storage' \
  --exclude='mednarrate-backend/logs' --exclude='mednarrate-backend/data/kb_index' \
  --exclude='mednarrate-backend/data/mrad_full' --exclude='.DS_Store' \
  --exclude='mednarrate-admin/coverage' --exclude='mednarrate-admin/e2e' \
  --exclude='mednarrate-backend/models' --exclude='*.bak' --exclude='*.gguf' \
  docker-compose.yml docker-compose.deploy.yml .env.deploy.example deploy website \
  mednarrate-backend mednarrate-admin
echo "Created $OUT ($(du -h "$OUT" | cut -f1))"
tar -tzf "$OUT" | grep -E '(^|/)\.env$' && { echo "ERROR: a .env file is inside the bundle"; exit 1; } || true
