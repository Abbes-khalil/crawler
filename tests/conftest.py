"""Point every test run at a throwaway SQLite database and disable the
Playwright fallback, before ``app`` is imported anywhere."""

import os
import tempfile

_tmp_db = os.path.join(tempfile.gettempdir(), "asbizdev-test.db")

os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp_db}")
os.environ.setdefault("PLAYWRIGHT_ENABLED", "false")
