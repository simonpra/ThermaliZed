#!/bin/bash
set -e  # Exit immediately on any error

# ─── Version ──────────────────────────────────────────────────────────────────
# Read version from VERSION file (single source of truth).
# To release a new version, just edit that file (e.g. "0.0.3-beta").
VERSION=$(cat VERSION | tr -d '[:space:]')
APP_NAME="ThermaliZed"
DMG_NAME="${APP_NAME}_Mac_v.${VERSION}.dmg"
DMG_PATH="dist/${DMG_NAME}"

echo "=================================================="
echo "  Building ${APP_NAME}  —  version ${VERSION}"
echo "=================================================="

# ─── Clean previous build artifacts ───────────────────────────────────────────
echo ""
echo "[1/4] Cleaning previous builds..."
rm -rf build/ dist/ /tmp/${APP_NAME}_dmg_staging

# ─── PyInstaller build ─────────────────────────────────────────────────────────
echo ""
echo "[2/4] Building .app bundle with PyInstaller..."
.venv/bin/python -m PyInstaller ThermaliZed.spec --clean --noconfirm

# Verify the .app was created
if [ ! -d "dist/${APP_NAME}.app" ]; then
    echo "❌  Error: dist/${APP_NAME}.app not found. Build failed?"
    exit 1
fi

# ─── Create .dmg ───────────────────────────────────────────────────────────────
echo ""
echo "[3/4] Creating .dmg installer..."

# Staging directory for the DMG contents
STAGING="/tmp/${APP_NAME}_dmg_staging"
mkdir -p "${STAGING}"

# Copy .app into staging and create a symlink to /Applications (drag-to-install UX)
cp -R "dist/${APP_NAME}.app" "${STAGING}/"
ln -s /Applications "${STAGING}/Applications"

# Build the DMG from the staging folder
hdiutil create \
    -volname "${APP_NAME} ${VERSION}" \
    -srcfolder "${STAGING}" \
    -ov \
    -format UDZO \
    "${DMG_PATH}"

# Clean up staging directory
rm -rf "${STAGING}"

# ─── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "[4/4] Done!"
echo "✅  Installer created: ${DMG_PATH}"
echo "    Size: $(du -sh "${DMG_PATH}" | cut -f1)"
