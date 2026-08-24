#!/usr/bin/env bash
# Bootstrap a fresh server: install Docker + Compose plugin, create app dir.
# Run ON the target server (as a sudo-capable user), or via:
#   ssh user@server 'bash -s' < scripts/setup_server.sh
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/app}"

if command -v docker >/dev/null 2>&1; then
  echo "docker already installed, skipping engine install"
else
  echo "installing docker engine"
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER"
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose plugin missing after install, check distro support" >&2
  exit 1
fi

sudo systemctl enable --now docker

mkdir -p "$APP_DIR"

echo "server ready. app dir: $APP_DIR"
echo "if this is the first login as docker group member, log out/in (or run 'newgrp docker') before running docker without sudo"
