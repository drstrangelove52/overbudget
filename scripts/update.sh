#!/bin/bash
# OverBudget – Update auf neueste Version
set -e

INSTALL_DIR="/opt/overbudget"
cd "$INSTALL_DIR"

echo "Aktueller Stand:"
git log -1 --format="  %h  %s  (%cr)"

echo ""
echo "Hole Updates von GitHub..."
git pull

echo ""
echo "Baue geänderte Images neu und starte Container..."
docker compose up -d --build --remove-orphans

echo ""
echo "Räume alte Images auf..."
docker image prune -f

echo ""
echo "Neuer Stand:"
git log -1 --format="  %h  %s  (%cr)"
echo ""
echo "Update abgeschlossen."
