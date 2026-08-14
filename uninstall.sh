#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
set -euo pipefail

readonly MODULE_NAME="8189fs"
readonly RUNNING_KERNEL="$(uname -r)"
readonly TARGET_MODULE="/lib/modules/${RUNNING_KERNEL}/kernel/drivers/net/wireless/${MODULE_NAME}.ko"
readonly AUTOLOAD_FILE="/etc/modules-load.d/${MODULE_NAME}.conf"

if [[ ${EUID} -ne 0 ]]; then
    echo "Fehler: Bitte als root ausfuehren: sudo ./uninstall.sh" >&2
    exit 1
fi

modprobe -r "${MODULE_NAME}" 2>/dev/null || true

if [[ -f "${TARGET_MODULE}.backup" ]]; then
    mv "${TARGET_MODULE}.backup" "${TARGET_MODULE}"
else
    rm -f "${TARGET_MODULE}"
fi
rm -f "${AUTOLOAD_FILE}"
depmod -a "${RUNNING_KERNEL}"

echo "${MODULE_NAME} wurde entfernt."

