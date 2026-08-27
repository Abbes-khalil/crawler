"""Cross-platform filesystem locations for the local web app.

All OS-specific path logic lives here - nothing else in the codebase should
branch on the platform. User-generated data (the SQLite database, logs, the
single-instance lock) is written under the per-user application-data
directory, never inside the installed application bundle.

    Windows: %LOCALAPPDATA%\\AS Biz Dev Web Intelligence\\
    macOS:   ~/Library/Application Support/AS Biz Dev Web Intelligence/
    Linux:   ~/.local/share/AS Biz Dev Web Intelligence/
"""

from __future__ import annotations

import sys
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "AS Biz Dev Web Intelligence"


def data_dir() -> Path:
    """Per-user application-data directory. Created on first access."""
    path = Path(user_data_dir(APP_NAME, appauthor=False))
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return data_dir() / "asbizdev.db"


def default_database_url() -> str:
    # SQLAlchemy URL form; forward slashes work on every platform.
    return f"sqlite:///{database_path().as_posix()}"


def log_dir() -> Path:
    path = data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def lock_path() -> Path:
    return data_dir() / "asbizdev.lock"


def bundle_dir() -> Path:
    """Directory containing bundled read-only assets.

    Under a PyInstaller build this is the temporary extraction dir
    (``sys._MEIPASS``); running from source it is the repo root.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent.parent


def frontend_dir() -> Path:
    """Location of the built static frontend (Next.js ``output: export``)."""
    return bundle_dir() / "web"
