# PyInstaller build definition for the Plutus desktop application.

import sys

app = Analysis(
    ["plutus/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(app.pure)

exe = EXE(
    pyz,
    app.scripts,
    app.binaries,
    app.datas,
    [],
    name="plutus",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=False,
)

if sys.platform == "darwin":
    app_bundle = BUNDLE(
        exe,
        name="Plutus.app",
        bundle_identifier="com.plutus.plutus",
    )
