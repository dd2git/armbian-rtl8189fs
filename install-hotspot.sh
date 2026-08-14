#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ "$(id -u)" -ne 0 ]; then
    echo "Fehler: Bitte als root ausfuehren: sudo ./install-hotspot.sh" >&2
    exit 1
fi
if ! command -v nmcli >/dev/null || ! command -v python3 >/dev/null; then
    echo "Fehler: NetworkManager (nmcli) und Python 3 werden benoetigt." >&2
    exit 1
fi

install -m 0755 "$SCRIPT_DIR/hotspot/armbian-wifi-setup.py" /usr/local/sbin/armbian-wifi-setup
install -m 0644 "$SCRIPT_DIR/hotspot/armbian-wifi-setup.service" /etc/systemd/system/armbian-wifi-setup.service
systemctl daemon-reload
systemctl enable --now armbian-wifi-setup.service
echo "Hotspot: Armbian-Setup / Passwort: armbian-setup"
echo "Webseite: http://10.42.0.1/"
