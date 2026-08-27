# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build for AS Biz Dev Web Intelligence.

Bundles the launcher, FastAPI app, crawler, and the pre-built static
frontend (web/out -> "web/" inside the bundle) into a single executable.

Run from the repository root:

    pyinstaller packaging/launcher.spec --noconfirm

Produces:
    dist/AS Biz Dev Web Intelligence           (Windows / Linux executable)
    dist/AS Biz Dev Web Intelligence.app       (macOS bundle)
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files

# SPECPATH is injected by PyInstaller; the repo root is its parent.
ROOT = Path(SPECPATH).parent
APP_NAME = "AS Biz Dev Web Intelligence"

datas = []
binaries = []
hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.protocols.websockets.websockets_impl",
    "uvicorn.lifespan.on",
]

for package in ("trafilatura", "justext", "courlan", "htmldate"):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hidden
    except Exception:
        pass

datas += collect_data_files("phonenumbers")

# Ship the built static frontend. `npm --prefix web run build` must have run.
web_out = ROOT / "web" / "out"
if not (web_out / "index.html").exists():
    raise SystemExit(
        "web/out/index.html not found - run `npm --prefix web ci && "
        "npm --prefix web run build` before packaging."
    )
datas.append((str(web_out), "web"))

a = Analysis(
    [str(ROOT / "launcher" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    # No console window: diagnostics go to
    # <app-data>/AS Biz Dev Web Intelligence/logs/app.log
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name=f"{APP_NAME}.app",
        icon=None,
        bundle_identifier="dev.asbizdev.webintelligence",
        info_plist={
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "LSMinimumSystemVersion": "11.0",
            "NSHighResolutionCapable": True,
            # Background server + browser hand-off; no dock icon needed.
            "LSUIElement": True,
        },
    )
