"""WSGI entrypoint for Passenger / serv00 deployments."""

from __future__ import annotations

import atexit
import asyncio
import sys
import threading
from pathlib import Path

from a2wsgi import ASGIMiddleware

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api.app import create_app, shutdown_runtime, startup_runtime  # noqa: E402

app = create_app()
_wsgi_loop = asyncio.new_event_loop()
_wsgi_thread = threading.Thread(
    target=_wsgi_loop.run_forever,
    name="chatgpt2api-wsgi-loop",
    daemon=True,
)
_wsgi_thread.start()


def _run(coro):
    return asyncio.run_coroutine_threadsafe(coro, _wsgi_loop).result()


_run(startup_runtime(app))


def _shutdown_wsgi_runtime() -> None:
    if _wsgi_loop.is_closed():
        return
    try:
        _run(shutdown_runtime(app))
    finally:
        try:
            _wsgi_loop.call_soon_threadsafe(_wsgi_loop.stop)
        except RuntimeError:
            return
        if _wsgi_thread.is_alive():
            _wsgi_thread.join(timeout=5)
        if not _wsgi_loop.is_running() and not _wsgi_loop.is_closed():
            _wsgi_loop.close()


atexit.register(_shutdown_wsgi_runtime)

application = ASGIMiddleware(app, loop=_wsgi_loop)

