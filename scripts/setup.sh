#!/bin/bash
# OverBudget – Erstinstallation im LXC-Container
# Aufruf: bash setup.sh
set -e

REPO="https://github.com/drstrangelove52/overbudget.git"
INSTALL_DIR="/opt/overbudget"

# ── Pakete ────────────────────────────────────────────────────────────────────
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg git nano

# ── Docker installieren ───────────────────────────────────────────────────────
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

systemctl enable --now docker

# ── Repo klonen ───────────────────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Verzeichnis $INSTALL_DIR existiert bereits, überspringe Clone."
else
  git clone "$REPO" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# ── .env anlegen ─────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  JWT=$(openssl rand -hex 32)
  GPG=$(openssl rand -hex 16)
  sed -i "s|change-this-to-a-long-random-string|$JWT|" .env
  sed -i "s|change-this-backup-passphrase|$GPG|" .env
fi

# ── Caddyfile: Hostname setzen ────────────────────────────────────────────────
read -rp "Hostname für HTTPS (z.B. overbudget.lan) [Enter = überspringen]: " HOSTNAME
if [ -n "$HOSTNAME" ]; then
  sed -i "s|your-hostname.local|$HOSTNAME|g" Caddyfile
fi

# ── .env anzeigen und zur Anpassung auffordern ────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════"
echo " Aktuelle Konfiguration ($INSTALL_DIR/.env):"
echo "════════════════════════════════════════════════════"
cat .env
echo "════════════════════════════════════════════════════"
echo ""
echo " Mindestens APP_USERNAME und APP_PASSWORD anpassen!"
echo " JWT_SECRET und GPG_PASSPHRASE wurden automatisch generiert."
echo ""
read -rp "Jetzt .env bearbeiten? [J/n]: " EDIT
if [[ "$EDIT" != "n" && "$EDIT" != "N" ]]; then
  nano .env
fi

# ── Starten ───────────────────────────────────────────────────────────────────
echo ""
echo "Starte OverBudget (Images werden heruntergeladen, dauert einige Minuten)..."
docker compose up -d --build

echo ""
echo "════════════════════════════════════════════════════"
echo " OverBudget läuft."
echo " Frontend:  http://$(hostname -I | awk '{print $1}'):3000"
echo " API:       http://$(hostname -I | awk '{print $1}'):8000/docs"
echo ""
echo " Update:    $INSTALL_DIR/scripts/update.sh"
echo "════════════════════════════════════════════════════"
