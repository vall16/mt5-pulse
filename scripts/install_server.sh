#!/usr/bin/env bash
# Installazione una tantum dei servizi systemd sul server Ubuntu.
# Eseguire come utente vibe:  ./scripts/install_server.sh
set -euo pipefail

[ "$(uname -s)" = "Linux" ] || { echo "Questo script va eseguito su Linux" >&2; exit 1; }

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR=/etc/systemd/system

for unit in mt5pulse-backend.service mt5pulse-frontend.service; do
  echo "==> Installo $unit"
  sudo install -m 0644 "$SRC/deploy/systemd/$unit" "$UNIT_DIR/$unit"
done

sudo systemctl daemon-reload
sudo systemctl enable mt5pulse-backend mt5pulse-frontend

echo
echo "Servizi installati e abilitati all'avvio."
echo "Avvio iniziale:"
echo "  sudo systemctl start mt5pulse-backend mt5pulse-frontend"
echo "Stato:"
echo "  systemctl status mt5pulse-backend mt5pulse-frontend"
