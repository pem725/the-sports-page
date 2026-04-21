#!/usr/bin/env bash
# Regenerate the QR code at assets/qr-code.png.
# Encodes the site URL with a UTM tag so QR-scan traffic is
# distinguishable in GoatCounter from direct/typed traffic.
#
# Requires: `qr` CLI (from `pipx install qrcode`).

set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
URL='https://pem725.github.io/the-sports-page/?utm_source=qr&utm_medium=print'

qr --error-correction=M "$URL" > "$REPO/assets/qr-code.png"
echo "Wrote QR encoding: $URL"
echo "  → $REPO/assets/qr-code.png"
