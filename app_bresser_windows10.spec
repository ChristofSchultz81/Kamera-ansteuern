# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


PROJECT_ROOT = Path(SPECPATH)

analysis = Analysis(
    ["app_bresser_windows10.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=[
        (
            str(PROJECT_ROOT / "driver" / "Bresser#" / "bressercam.dll"),
            ".",
        )
    ],
    datas=[(str(PROJECT_ROOT / "templates"), "templates")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["vmbpy"],
    noarchive=False,
)
pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    [],
    name="BresserCameraDashboard-Windows10",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)