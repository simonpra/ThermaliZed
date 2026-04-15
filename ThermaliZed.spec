# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['cv2', 'PIL']
hiddenimports += collect_submodules('src.core.components')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('plugins', 'plugins'), ('src/core/components', 'src/core/components')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ThermaliZed',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ThermaliZed',
)
app = BUNDLE(
    coll,
    name='ThermaliZed.app',
    icon='./thermalized.icns',
    bundle_identifier=None,
    info_plist={
        'NSCameraUsageDescription': 'ThermaliZed requires camera access to view and process thermal USB video streams.',
    },
)
