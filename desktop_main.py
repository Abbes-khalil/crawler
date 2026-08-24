"""Production entrypoint for the packaged desktop sidecar.

Bundled by PyInstaller into a standalone executable that Tauri launches as
a sidecar process. Binds to 127.0.0.1 only - never exposed to the LAN or
public internet. Playwright is disabled: the JS-rendering fallback is not
bundled in v1, so pages that need it degrade to INSUFFICIENT_CONTENT
instead of the crawl failing to package.
"""

import os
import sys

os.environ.setdefault("PLAYWRIGHT_ENABLED", "false")

import uvicorn

DEFAULT_PORT = 8756


def main() -> None:
    port = DEFAULT_PORT

    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    from app.main import app

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
