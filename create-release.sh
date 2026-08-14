#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly VERSION="${1:-6.18.43-ophub}"
readonly ARCHIVE="armbian-rtl8189fs-${VERSION}.tar.gz"

cd "${SCRIPT_DIR}"
sha256sum "prebuilt/${VERSION}/8189fs.ko" > SHA256SUMS
tar --transform="s,^,armbian-rtl8189fs-${VERSION}/," \
    --exclude='.git' --exclude="${ARCHIVE}" -czf "${ARCHIVE}" \
    README.md LICENSE install.sh uninstall.sh scan-wifi.sh SHA256SUMS prebuilt
sha256sum "${ARCHIVE}"
echo "Erstellt: ${SCRIPT_DIR}/${ARCHIVE}"
