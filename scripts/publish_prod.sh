#!/usr/bin/env bash
# Sync local repo to server and rebuild containers.
# Usage: scripts/publish_prod.sh [user@host]
set -euo pipefail

REMOTE="${1:-deploy@203.0.113.10}"   # placeholder IP, override via arg or env
APP_DIR="${APP_DIR:-app}"            # relative to remote $HOME -> ~/app

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "syncing $REPO_ROOT -> $REMOTE:~/$APP_DIR"

rsync -az --delete \
  --exclude '.git/' \
  --exclude '.env' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.venv/' \
  --exclude '.pytest_cache/' \
  --exclude '.ruff_cache/' \
  --exclude 'node_modules/' \
  --exclude 'dist/' \
  "$REPO_ROOT"/ "$REMOTE:~/$APP_DIR/"

echo "rebuilding containers on $REMOTE"

ssh "$REMOTE" bash -s <<EOF
set -euo pipefail
cd ~/$APP_DIR
if [ ! -f .env ]; then
  echo ".env missing on server, copy one before first deploy" >&2
  exit 1
fi
docker compose build
docker compose up -d --remove-orphans
docker image prune -f
EOF

echo "deploy done"
