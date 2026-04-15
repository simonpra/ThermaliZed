#!/bin/bash

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ ThermaliZed_Mac.zip

# Build the app using PyInstaller
echo "Building the application with PyInstaller..."
.venv/bin/python -m PyInstaller ThermaliZed.spec --clean --noconfirm

# Zip the resulting .app bundle (preserving macOS extended attributes/permissions)
echo "Zipping the .app bundle..."
if [ -d "dist/ThermaliZed.app" ]; then
    ditto -c -k --sequesterRsrc --keepParent dist/ThermaliZed.app ThermaliZed_Mac.zip
    echo "Success! The app has been zipped to ThermaliZed_Mac.zip."
else
    echo "Error: dist/ThermaliZed.app not found. Build failed?"
    exit 1
fi
