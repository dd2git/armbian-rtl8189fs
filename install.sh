#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
set -euo pipefail

readonly SUPPORTED_KERNEL="6.18.43-ophub"
readonly MODULE_NAME="8189fs"
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly RUNNING_KERNEL="$(uname -r)"
readonly SOURCE_MODULE="${SCRIPT_DIR}/prebuilt/${RUNNING_KERNEL}/${MODULE_NAME}.ko"
readonly TARGET_DIR="/lib/modules/${RUNNING_KERNEL}/kernel/drivers/net/wireless"
readonly TARGET_MODULE="${TARGET_DIR}/${MODULE_NAME}.ko"
readonly AUTOLOAD_FILE="/etc/modules-load.d/${MODULE_NAME}.conf"

if [[ ${EUID} -ne 0 ]]; then
    echo "Fehler: Bitte als root ausfuehren: sudo ./install.sh" >&2
    exit 1
fi

if [[ "${RUNNING_KERNEL}" != "${SUPPORTED_KERNEL}" ]]; then
    echo "Fehler: Dieses fertige Modul ist nur fuer ${SUPPORTED_KERNEL} gebaut." >&2
    echo "Aktiver Kernel: ${RUNNING_KERNEL}" >&2
    echo "Bei einem anderen Kernel muss das Modul neu gebaut werden." >&2
    exit 1
fi

if [[ ! -f "${SOURCE_MODULE}" ]]; then
    echo "Fehler: Modul fehlt: ${SOURCE_MODULE}" >&2
    exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
    (cd "${SCRIPT_DIR}" && sha256sum --check SHA256SUMS)
fi

install -d -m 755 "${TARGET_DIR}"
if [[ -f "${TARGET_MODULE}" ]]; then
    cp -a "${TARGET_MODULE}" "${TARGET_MODULE}.backup"
fi
install -m 644 "${SOURCE_MODULE}" "${TARGET_MODULE}"
depmod -a "${RUNNING_KERNEL}"
printf '%s\n' "${MODULE_NAME}" > "${AUTOLOAD_FILE}"

modprobe -r "${MODULE_NAME}" 2>/dev/null || true
modprobe "${MODULE_NAME}"

if command -v rfkill >/dev/null 2>&1; then
    rfkill unblock wifi || true
fi
if command -v nmcli >/dev/null 2>&1; then
    nmcli radio wifi on || true
    nmcli device set wlan0 managed yes 2>/dev/null || true
fi
ip link set wlan0 up 2>/dev/null || true

echo
echo "Installation erfolgreich."
echo "Treiber: $(modinfo -F version "${MODULE_NAME}" 2>/dev/null || echo unbekannt)"
ip -brief link show wlan0 2>/dev/null || true
echo
echo "Netzwerke anzeigen mit: nmcli device wifi list"

