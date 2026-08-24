#!/usr/bin/env bash
# Install or update delphi on a remote server over SSH + rsync.
#
# Same command does both: on a fresh box it installs Docker and brings the
# stack up, on an existing one it syncs changes and rebuilds. Safe to re-run.
#
# Target is read from DEPLOY_HOST (env or .env). Example:
#   DEPLOY_HOST=203.0.113.10 scripts/deploy.sh
#
# Flags:
#   --with-env   also copy local .env to the server (first deploy, or when
#                secrets change). Off by default so secrets are not resent.
#   --dry-run    show what rsync would transfer, change nothing
#   --no-health  skip the post-deploy health check
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

WITH_ENV=0
DRY_RUN=0
HEALTH=1
for arg in "$@"; do
  case "$arg" in
    --with-env)  WITH_ENV=1 ;;
    --dry-run)   DRY_RUN=1 ;;
    --no-health) HEALTH=0 ;;
    -h|--help)   sed -n '2,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

# Load .env without clobbering variables already set in the environment, so
# DEPLOY_HOST=... scripts/deploy.sh overrides the file.
if [ -f "$REPO_ROOT/.env" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in ''|'#'*) continue ;; esac
    key=${line%%=*}
    value=${line#*=}
    case "$key" in
      [A-Za-z_]*) ;;
      *) continue ;;
    esac
    value=${value%\"}; value=${value#\"}
    value=${value%\'}; value=${value#\'}
    if [ -z "${!key:-}" ]; then
      export "$key=$value"
    fi
  done < "$REPO_ROOT/.env"
fi

if [ -z "${DEPLOY_HOST:-}" ]; then
  cat >&2 <<'ERR'
DEPLOY_HOST is not set.

Set it in .env (see .env.example) or pass it inline:
  DEPLOY_HOST=203.0.113.10 scripts/deploy.sh
ERR
  exit 1
fi

DEPLOY_USER="${DEPLOY_USER:-root}"
DEPLOY_PATH="${DEPLOY_PATH:-app}"
DEPLOY_SSH_PORT="${DEPLOY_SSH_PORT:-22}"
APP_PORT="${APP_PORT:-12559}"

case "$DEPLOY_HOST" in
  *@*) REMOTE="$DEPLOY_HOST" ;;
  *)   REMOTE="$DEPLOY_USER@$DEPLOY_HOST" ;;
esac
HOST_ONLY="${REMOTE#*@}"

SSH_OPTS=(-p "$DEPLOY_SSH_PORT")
if [ -n "${DEPLOY_SSH_KEY:-}" ]; then
  SSH_OPTS+=(-i "$DEPLOY_SSH_KEY")
fi
SSH_CMD="ssh $(printf '%q ' "${SSH_OPTS[@]}")"

echo "==> target $REMOTE:~/$DEPLOY_PATH (port $DEPLOY_SSH_PORT)"

if ! ssh "${SSH_OPTS[@]}" -o BatchMode=yes -o ConnectTimeout=10 "$REMOTE" true 2>/dev/null; then
  echo "cannot reach $REMOTE over SSH." >&2
  echo "check DEPLOY_HOST/DEPLOY_USER/DEPLOY_SSH_PORT, and that your key is authorized." >&2
  exit 1
fi

RSYNC_OPTS=(-az --delete --exclude '.git/' --exclude '.env'
  --exclude '__pycache__/' --exclude '*.pyc' --exclude '.venv/'
  --exclude '.pytest_cache/' --exclude '.ruff_cache/'
  --exclude 'node_modules/' --exclude 'dist/')
if [ "$DRY_RUN" -eq 1 ]; then
  RSYNC_OPTS+=(-n -v)
  echo "==> dry run, nothing will change"
fi

echo "==> syncing files"
# DEPLOY_PATH is expanded here on purpose; $HOME is escaped so the server
# expands it. ssh flattens argv, so the remote command must be one string.
# shellcheck disable=SC2029
ssh "${SSH_OPTS[@]}" "$REMOTE" "mkdir -p \"\$HOME/$DEPLOY_PATH\""
rsync "${RSYNC_OPTS[@]}" -e "$SSH_CMD" "$REPO_ROOT"/ "$REMOTE:~/$DEPLOY_PATH/"

if [ "$WITH_ENV" -eq 1 ]; then
  if [ ! -f "$REPO_ROOT/.env" ]; then
    echo "--with-env given but no local .env exists" >&2
    exit 1
  fi
  echo "==> copying .env to server"
  if [ "$DRY_RUN" -eq 0 ]; then
    rsync -az -e "$SSH_CMD" "$REPO_ROOT/.env" "$REMOTE:~/$DEPLOY_PATH/.env"
  fi
fi

if [ "$DRY_RUN" -eq 1 ]; then
  echo "==> dry run complete"
  exit 0
fi

echo "==> installing prerequisites and starting stack"
ssh "${SSH_OPTS[@]}" "$REMOTE" APP_DIR="$DEPLOY_PATH" bash -s <<'REMOTE_SCRIPT'
set -euo pipefail
cd ~/"${APP_DIR:-app}"

if [ ! -f .env ]; then
  echo ".env missing on the server." >&2
  echo "re-run the deploy with --with-env, or create ~/${APP_DIR:-app}/.env by hand." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "-- docker not found, bootstrapping"
  # APP_DIR is relative to $HOME here, and we already cd'd into it, so pass the
  # absolute path or setup_server.sh creates a nested copy underneath it.
  APP_DIR="$PWD" bash scripts/setup_server.sh
fi

# A freshly added docker group is not active in this session yet, so fall
# back to sudo rather than failing the first deploy.
if docker info >/dev/null 2>&1; then
  DOCKER="docker"
elif sudo -n docker info >/dev/null 2>&1; then
  DOCKER="sudo docker"
else
  echo "docker is installed but not usable by $(whoami)." >&2
  echo "log out and back in (or run 'newgrp docker'), then re-run the deploy." >&2
  exit 1
fi

echo "-- building images"
$DOCKER compose build
echo "-- starting containers"
$DOCKER compose up -d --remove-orphans
$DOCKER compose ps
$DOCKER image prune -f >/dev/null
REMOTE_SCRIPT

if [ "$HEALTH" -eq 1 ]; then
  echo "==> waiting for the app to answer on port $APP_PORT"
  for _ in $(seq 1 30); do
    if curl -fsS -m 5 "http://$HOST_ONLY:$APP_PORT/healthz" >/dev/null 2>&1; then
      echo "==> healthy: http://$HOST_ONLY:$APP_PORT"
      exit 0
    fi
    sleep 2
  done
  echo "app did not answer on http://$HOST_ONLY:$APP_PORT/healthz after 60s." >&2
  echo "check logs with: ssh $REMOTE 'cd ~/$DEPLOY_PATH && docker compose logs --tail=50'" >&2
  exit 1
fi

echo "==> deploy done"
