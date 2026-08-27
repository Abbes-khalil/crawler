"""Application entrypoint for the local web app.

    launch
      |
      +-- local server already running?  (lock file + /api/health)
      |        yes -> open browser, exit
      |
      +-- pick a free port from PREFERRED_PORT upward
      +-- start uvicorn on 127.0.0.1:<port> (background thread)
      +-- wait for GET /api/health
      +-- open the default browser
      +-- run until Ctrl-C / window closed, then shut down and clear the lock

No arbitrary sleeps: readiness is polled via /api/health. The server binds
loopback only and is never exposed to the LAN.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser

# The packaged crawl must not depend on a bundled browser engine.
os.environ.setdefault("PLAYWRIGHT_ENABLED", "false")

from app.config import HOST, PREFERRED_PORT  # noqa: E402
from app.paths import lock_path, log_dir  # noqa: E402


def _configure_logging() -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    try:
        handlers.append(
            logging.FileHandler(log_dir() / "app.log", encoding="utf-8")
        )
    except OSError:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )

HEALTH_PATH = "/api/health"
STARTUP_TIMEOUT_S = 30.0
PORT_SCAN_RANGE = 50


def _health_ok(port: int, timeout: float = 1.0) -> bool:
    url = f"http://{HOST}:{port}{HEALTH_PATH}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            return resp.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        return False


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((HOST, port))
            return True
        except OSError:
            return False


def _pick_port() -> int:
    for candidate in range(PREFERRED_PORT, PREFERRED_PORT + PORT_SCAN_RANGE):
        if _port_is_free(candidate):
            return candidate
    raise RuntimeError(
        f"No free port in {PREFERRED_PORT}..{PREFERRED_PORT + PORT_SCAN_RANGE}"
    )


def _read_lock() -> dict | None:
    try:
        return json.loads(lock_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _running_instance_port() -> int | None:
    """Return the port of a healthy already-running instance, or None.
    Clears the lock file if it is stale."""
    info = _read_lock()
    if not info:
        return None
    port = info.get("port")
    if isinstance(port, int) and _health_ok(port):
        return port
    try:
        lock_path().unlink()
    except OSError:
        pass
    return None


def _write_lock(port: int) -> None:
    lock_path().write_text(
        json.dumps({"pid": os.getpid(), "port": port}), encoding="utf-8"
    )


def _clear_lock() -> None:
    info = _read_lock()
    if info and info.get("pid") == os.getpid():
        try:
            lock_path().unlink()
        except OSError:
            pass


def _open_browser(port: int) -> None:
    webbrowser.open(f"http://{HOST}:{port}/")


def main() -> int:
    _configure_logging()

    existing = _running_instance_port()
    if existing is not None:
        print(f"Already running on port {existing}; opening browser.")
        _open_browser(existing)
        return 0

    import uvicorn

    from app.main import app

    port = _pick_port()

    config = uvicorn.Config(app, host=HOST, port=port, log_level="info")
    server = uvicorn.Server(config)
    # We install our own signal handling below.
    server.install_signal_handlers = lambda: None

    thread = threading.Thread(target=server.run, name="uvicorn", daemon=True)
    thread.start()

    deadline = time.monotonic() + STARTUP_TIMEOUT_S
    while time.monotonic() < deadline:
        if server.started and _health_ok(port):
            break
        if not thread.is_alive():
            print("Server thread exited before becoming ready.", file=sys.stderr)
            return 1
        time.sleep(0.1)
    else:
        print("Server did not become ready in time.", file=sys.stderr)
        server.should_exit = True
        return 1

    _write_lock(port)

    def _shutdown(*_args) -> None:
        server.should_exit = True

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    print(f"AS Biz Dev Web Intelligence running at http://{HOST}:{port}/")
    _open_browser(port)

    try:
        while thread.is_alive():
            thread.join(timeout=0.5)
    except KeyboardInterrupt:
        server.should_exit = True
        thread.join(timeout=10)
    finally:
        _clear_lock()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
