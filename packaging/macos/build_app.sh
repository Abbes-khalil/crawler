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

APP_PATH="dist/${APP_NAME}.app"

# CI builds the bundle in a prior step; only build here if it is missing
# (e.g. a local invocation).
if [[ ! -d "$APP_PATH" ]]; then
  pyinstaller packaging/launcher.spec --noconfirm
fi
test -d "$APP_PATH"

if [[ -n "${CODESIGN_IDENTITY:-}" ]]; then
  echo "Signing $APP_PATH with $CODESIGN_IDENTITY"
  codesign --deep --force --options runtime --timestamp \
    --sign "$CODESIGN_IDENTITY" "$APP_PATH"
else
  # No paid Developer ID available: ad-hoc sign so the bundle carries a valid
  # (self-referential) signature. This does not remove the "unidentified
  # developer" prompt, but it prevents the harsher "app is damaged and can't
  # be opened" error that unsigned PyInstaller bundles hit on Apple Silicon.
  echo "Ad-hoc signing $APP_PATH (no CODESIGN_IDENTITY set)"
  codesign --deep --force --sign - "$APP_PATH"
fi

# Always produce a zip of the .app - hdiutil on CI runners is flaky
# ("Resource busy" / "No space left"), so the zip is the reliable artifact
# and the .dmg is best-effort.
ZIP_PATH="dist/AS-Biz-Dev-Web-Intelligence-macos.zip"
rm -f "$ZIP_PATH"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"
echo "Built $ZIP_PATH"

DMG_PATH="dist/AS-Biz-Dev-Web-Intelligence.dmg"
STAGING="$(mktemp -d)"
cp -R "$APP_PATH" "$STAGING/"

make_dmg() {
  hdiutil detach "/Volumes/$APP_NAME" >/dev/null 2>&1 || true
  rm -f "$DMG_PATH"
  sync
  hdiutil create -volname "$APP_NAME" -srcfolder "$STAGING" \
    -fs HFS+ -ov -format UDZO "$DMG_PATH"
}

dmg_ok=""
for attempt in 1 2 3 4 5; do
  if make_dmg; then
    dmg_ok=1
    break
  fi
  echo "hdiutil create failed (attempt $attempt); retrying in 10s..."
  sleep 10
done
rm -rf "$STAGING"

if [[ -z "$dmg_ok" ]]; then
  echo "WARNING: could not build .dmg after 5 attempts; shipping the zip only."
fi

if [[ -n "$dmg_ok" && -n "${NOTARY_PROFILE:-}" ]]; then
  echo "Notarizing $DMG_PATH"
  xcrun notarytool submit "$DMG_PATH" --keychain-profile "$NOTARY_PROFILE" --wait
  xcrun stapler staple "$DMG_PATH"
fi

[[ -n "$dmg_ok" ]] && echo "Built $DMG_PATH"
echo "Done."
