#!/usr/bin/env bash
# Bootstrap a fresh server: install Docker + Compose plugin, create app dir.
# Called automatically by scripts/deploy.sh when docker is missing, and safe
# to run standalone:
#   ssh user@server 'bash -s' < scripts/setup_server.sh
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/app}"

# Root has no need for sudo, and minimal images often do not ship it.
if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
elif command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
else
  echo "not running as root and sudo is unavailable; cannot install docker" >&2
  exit 1
fi

if command -v docker >/dev/null 2>&1; then
  echo "docker already installed, skipping engine install"
else
  echo "installing docker engine"
  curl -fsSL https://get.docker.com | sh
  if [ -n "$SUDO" ]; then
    $SUDO usermod -aG docker "$USER"
  fi
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose plugin missing after install, check distro support" >&2
  exit 1
fi


# Docker's default json-file driver never rotates, so container logs grow until
# they fill the disk. Set an engine-wide ceiling as a backstop for containers
# started outside docker-compose.yml (which sets its own per-service limits).
DAEMON_JSON=/etc/docker/daemon.json
if [ -f "$DAEMON_JSON" ]; then
  echo "$DAEMON_JSON already exists, leaving it alone"
  echo "  ensure it sets log-driver json-file with max-size/max-file, or logs stay unbounded"
else
  echo "writing default log rotation to $DAEMON_JSON"
  $SUDO mkdir -p /etc/docker
  printf '%s\n' \
    '{' \
    '  "log-driver": "json-file",' \
    '  "log-opts": { "max-size": "66m", "max-file": "3" }' \
    '}' | $SUDO tee "$DAEMON_JSON" >/dev/null
  RESTART_DOCKER=1
fi

if command -v systemctl >/dev/null 2>&1; then
  $SUDO systemctl enable --now docker
  # Log options are read at daemon start; a fresh daemon.json needs a restart.
  if [ -n "${RESTART_DOCKER:-}" ]; then
    $SUDO systemctl restart docker
  fi
fi

mkdir -p "$APP_DIR"

echo "server ready. app dir: $APP_DIR"
if [ -n "$SUDO" ]; then
  echo "if this is the first login as docker group member, log out/in (or run 'newgrp docker') before running docker without sudo"
fi
