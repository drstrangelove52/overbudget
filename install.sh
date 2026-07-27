#!/bin/bash
# OverBudget — fully automated install script.
#
# Run on a fresh Ubuntu/Debian VM as a normal user with sudo rights, from
# inside the repo directory (e.g. ~/overbudget). Installs Docker and
# Tailscale, generates .env with random secrets, builds and starts the
# stack, and wires up Tailscale HTTPS. Safe to re-run — every step is
# skipped or updated in place if it was already done, so `git pull &&
# ./install.sh` is also the update workflow.
#
# Fully automated if these are set beforehand (as environment variables);
# otherwise falls back to a prompt only where truly unavoidable
# (Tailscale login, if no auth key is given):
#
#   TAILSCALE_AUTHKEY    Reusable/ephemeral key from
#                         https://login.tailscale.com/admin/settings/keys
#                         (optional — without it, `tailscale up` prints a
#                         login URL to open once, manually)
#   TAILSCALE_HOSTNAME   Overrides the default "overbudget01"
#   ADMIN_USERNAME       Login username (default: admin)
#   ADMIN_PASSWORD       Login password (default: random, printed at the
#                         end — change it under "Einstellungen" after
#                         first login)
#   LAN_IP                Overrides the auto-detected primary LAN IP
#
# Usage:
#   TAILSCALE_AUTHKEY=tskey-... ./install.sh

set -euo pipefail

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }
warn() { printf '\033[1;33m!!  %s\033[0m\n' "$1"; }

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

if [ "$(id -u)" -eq 0 ]; then
  warn "Bitte nicht als root ausführen — als normaler User mit sudo-Rechten starten."
  exit 1
fi
log "sudo-Berechtigung wird geprüft…"
sudo -v

TAILSCALE_HOSTNAME="${TAILSCALE_HOSTNAME:-overbudget01}"

# 1. Docker ------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  log "Docker wird installiert…"
  curl -fsSL https://get.docker.com | sudo sh
else
  log "Docker bereits installiert, übersprungen."
fi

# 2. Tailscale -----------------------------------------------------------
if ! command -v tailscale >/dev/null 2>&1; then
  log "Tailscale wird installiert…"
  curl -fsSL https://tailscale.com/install.sh | sudo sh
else
  log "Tailscale bereits installiert, übersprungen."
fi

if ! sudo tailscale status >/dev/null 2>&1; then
  log "Tailscale wird verbunden…"
  if [ -n "${TAILSCALE_AUTHKEY:-}" ]; then
    sudo tailscale up --authkey="$TAILSCALE_AUTHKEY" --hostname="$TAILSCALE_HOSTNAME"
  else
    warn "Kein TAILSCALE_AUTHKEY gesetzt — bitte den gleich ausgegebenen Link öffnen und mit deinem Tailscale-Konto bestätigen."
    sudo tailscale up --hostname="$TAILSCALE_HOSTNAME"
  fi
else
  log "Tailscale bereits verbunden, übersprungen."
fi

TAILSCALE_DNS="$(sudo tailscale status --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))')"

# 3. .env -----------------------------------------------------------------
GENERATED_ADMIN_PASSWORD=false
if [ ! -f .env ]; then
  log ".env wird generiert…"
  DETECTED_IP="$(ip -4 route get 1.1.1.1 2>/dev/null | grep -oP 'src \K[\d.]+' || true)"
  RESOLVED_LAN_IP="${LAN_IP:-$DETECTED_IP}"
  if [ -z "$RESOLVED_LAN_IP" ]; then
    warn "Konnte die LAN-IP nicht automatisch erkennen — bitte mit LAN_IP=<ip> ./install.sh erneut starten."
    exit 1
  fi

  RESOLVED_ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
  if [ -n "${ADMIN_PASSWORD:-}" ]; then
    RESOLVED_ADMIN_PASSWORD="$ADMIN_PASSWORD"
  else
    RESOLVED_ADMIN_PASSWORD="$(openssl rand -base64 18)"
    GENERATED_ADMIN_PASSWORD=true
  fi

  cp .env.example .env
  sed -i \
    -e "s|^LAN_IP=.*|LAN_IP=${RESOLVED_LAN_IP}|" \
    -e "s|^DB_ROOT_PASSWORD=.*|DB_ROOT_PASSWORD=$(openssl rand -base64 24)|" \
    -e "s|^DB_PASSWORD=.*|DB_PASSWORD=$(openssl rand -base64 24)|" \
    -e "s|^APP_USERNAME=.*|APP_USERNAME=${RESOLVED_ADMIN_USERNAME}|" \
    -e "s|^APP_PASSWORD=.*|APP_PASSWORD=${RESOLVED_ADMIN_PASSWORD}|" \
    -e "s|^GPG_PASSPHRASE=.*|GPG_PASSPHRASE=$(openssl rand -hex 16)|" \
    .env
else
  log ".env existiert bereits, übersprungen (bestehende Secrets bleiben unangetastet)."
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

# 4. Build & start ------------------------------------------------------
log "Container werden gebaut und gestartet…"
sudo docker compose up --build -d

log "Warte auf das Backend…"
BACKEND_UP=false
for _ in $(seq 1 30); do
  if curl -skf -o /dev/null "https://${LAN_IP}/api/health"; then
    BACKEND_UP=true
    break
  fi
  sleep 2
done
if [ "$BACKEND_UP" != true ]; then
  warn "Backend antwortet nach 60s nicht — 'sudo docker compose logs api' zur Fehlersuche prüfen."
  exit 1
fi

# 5. Tailscale HTTPS --------------------------------------------------------
log "Tailscale HTTPS wird eingerichtet…"
sudo tailscale serve --bg "https+insecure://${LAN_IP}:443"

# 6. Summary ----------------------------------------------------------------
log "Fertig!"
echo "LAN (Zertifikatswarnung nötig):  https://${LAN_IP}"
echo "Tailscale (echtes Zertifikat):  https://${TAILSCALE_DNS}"
echo
echo "Login:    ${APP_USERNAME}"
if [ "$GENERATED_ADMIN_PASSWORD" = true ]; then
  echo "Passwort: ${APP_PASSWORD}   (automatisch generiert — nach dem ersten Login unter Einstellungen ändern!)"
fi
echo
echo "Update:   git pull && ./install.sh"
