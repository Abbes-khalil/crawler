# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build for AS Biz Dev Web Intelligence.

Bundles the launcher, FastAPI app, crawler, and the pre-built static
frontend (web/out -> "web/" inside the bundle).

Run from the repository root:

    pyinstaller packaging/launcher.spec --noconfirm

Produces:
    Windows / Linux : dist/AS Biz Dev Web Intelligence[.exe]   (onefile)
    macOS           : dist/AS Biz Dev Web Intelligence.app      (onedir bundle)
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files

# SPECPATH is injected by PyInstaller; the repo root is its parent.
ROOT = Path(SPECPATH).parent
APP_NAME = "AS Biz Dev Web Intelligence"
IS_MACOS = sys.platform == "darwin"

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

# The packaged app never uses the Playwright fallback
# (PLAYWRIGHT_ENABLED=false), so keep the browser stack out of the bundle.
excludes = ["playwright", "pytest", "pytest_asyncio", "tkinter", "_tkinter"]

a = Analysis(
    [str(ROOT / "launcher" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

if IS_MACOS:
    # onedir + BUNDLE: a .app cannot be a single file, and onefile clashes
    # with macOS code-signing / Gatekeeper.
    exe = EXE(
        pyz,
        a.scripts,
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
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
        upx=False,
        name=APP_NAME,
    )
    app = BUNDLE(
        coll,
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
else:
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
