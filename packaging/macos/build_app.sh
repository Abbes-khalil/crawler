#!/usr/bin/env bash
# Build (and optionally sign + notarize) the macOS .app bundle.
#
# Prerequisites, run from the repo root beforehand:
#   npm --prefix web ci && npm --prefix web run build
#   python -m pip install -r requirements-build.txt
#
# Optional signing env vars (leave unset for an unsigned local build):
#   CODESIGN_IDENTITY   "Developer ID Application: ..."
#   NOTARY_PROFILE      notarytool keychain profile name
set -euo pipefail

APP_NAME="AS Biz Dev Web Intelligence"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

pyinstaller packaging/launcher.spec --noconfirm

APP_PATH="dist/${APP_NAME}.app"
test -d "$APP_PATH"

if [[ -n "${CODESIGN_IDENTITY:-}" ]]; then
  echo "Signing $APP_PATH"
  codesign --deep --force --options runtime --timestamp \
    --sign "$CODESIGN_IDENTITY" "$APP_PATH"
fi

DMG_PATH="dist/AS-Biz-Dev-Web-Intelligence.dmg"
rm -f "$DMG_PATH"
hdiutil create -volname "$APP_NAME" -srcfolder "$APP_PATH" \
  -ov -format UDZO "$DMG_PATH"

if [[ -n "${NOTARY_PROFILE:-}" ]]; then
  echo "Notarizing $DMG_PATH"
  xcrun notarytool submit "$DMG_PATH" --keychain-profile "$NOTARY_PROFILE" --wait
  xcrun stapler staple "$DMG_PATH"
fi

echo "Built $DMG_PATH"
