# fastapi_gui.spec
# Custom PyInstaller build file for FastAPI Controller GUI

import os
from PyInstaller.utils.hooks import collect_submodules

# --- Paths (relative) ---
icon_dir = os.path.join("src", "img")

# --- Hidden imports for psutil ---
hiddenimports = collect_submodules("psutil")

block_cipher = None

a = Analysis(
    ["api_gui.py"],  # your main Python file
    pathex=["."],
    binaries=[],
    datas=[
        (os.path.join(icon_dir, "app.ico"), "."),   # Include Windows icon
        (os.path.join(icon_dir, "app.icns"), ".")   # Include macOS icon
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FastAPI Controller",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Hide console window
    icon=os.path.join(icon_dir, "app.ico"),  # Windows icon
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False,
    upx=True,
    name="FastAPI Controller"
)