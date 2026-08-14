#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
    echo "Fehler: Bitte als root ausfuehren: sudo ./uninstall-hotspot.sh" >&2
    exit 1
fi

systemctl disable --now armbian-wifi-setup.service 2>/dev/null || true
nmcli connection delete armbian-setup-hotspot 2>/dev/null || true
rm -f /etc/systemd/system/armbian-wifi-setup.service
rm -f /usr/local/sbin/armbian-wifi-setup
systemctl daemon-reload
echo "WLAN-Einrichtungs-Hotspot wurde entfernt."
