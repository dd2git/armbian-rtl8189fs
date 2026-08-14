#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
set -euo pipefail

interface="${1:-wlan0}"

if ! ip link show "${interface}" >/dev/null 2>&1; then
    echo "Fehler: Schnittstelle ${interface} wurde nicht gefunden." >&2
    exit 1
fi

if command -v nmcli >/dev/null 2>&1; then
    nmcli --fields SSID,CHAN,FREQ,SIGNAL,SECURITY device wifi list ifname "${interface}" --rescan yes
else
    if [[ ${EUID} -ne 0 ]]; then
        echo "Ohne NetworkManager bitte als root ausfuehren." >&2
        exit 1
    fi
    ip link set "${interface}" up
    iw dev "${interface}" scan | grep -E '^BSS |SSID:|signal:|freq:'
fi

