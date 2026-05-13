from __future__ import annotations

from contextlib import asynccontextmanager
from threading import Event

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from api import accounts, ai, image_tasks, register, system
from api.support import resolve_web_asset, start_limited_account_watcher
from services.backup_service import backup_service
from services.config import config


async def startup_runtime(app: FastAPI) -> None:
    if getattr(app.state, "runtime_started", False):
        return

    stop_event = Event()
    watcher_thread = start_limited_account_watcher(stop_event)
    backup_service.start()
    config.cleanup_old_images()

    app.state.account_watcher_stop_event = stop_event
    app.state.account_watcher_thread = watcher_thread
    app.state.runtime_started = True


async def shutdown_runtime(app: FastAPI) -> None:
    if not getattr(app.state, "runtime_started", False):
        return

    stop_event = getattr(app.state, "account_watcher_stop_event", None)
    watcher_thread = getattr(app.state, "account_watcher_thread", None)

    if stop_event is not None:
        stop_event.set()
    if watcher_thread is not None:
        watcher_thread.join(timeout=1)
    backup_service.stop()

    app.state.account_watcher_stop_event = None
    app.state.account_watcher_thread = None
    app.state.runtime_started = False


def create_app() -> FastAPI:
    app_version = config.app_version

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await startup_runtime(app)
        try:
            yield
        finally:
            await shutdown_runtime(app)

    app = FastAPI(title="chatgpt2api", version=app_version, lifespan=lifespan)
    app.state.account_watcher_stop_event = None
    app.state.account_watcher_thread = None
    app.state.runtime_started = False
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(ai.create_router())
    app.include_router(accounts.create_router())
    app.include_router(image_tasks.create_router())
    app.include_router(register.create_router())
    app.include_router(system.create_router(app_version))
    if config.images_dir.exists():
        app.mount("/images", StaticFiles(directory=str(config.images_dir)), name="images")

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": app_version}

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_web(full_path: str):
        asset = resolve_web_asset(full_path)
        if asset is not None:
            return FileResponse(asset)
        if full_path.strip("/").startswith("_next/"):
            raise HTTPException(status_code=404, detail="Not Found")
        fallback = resolve_web_asset("")
        if fallback is None:
            if full_path.strip("/"):
                raise HTTPException(status_code=404, detail="Not Found")
            return HTMLResponse(
                f"""
                <!doctype html>
                <html lang="en">
                <head>
                  <meta charset="utf-8">
                  <meta name="viewport" content="width=device-width, initial-scale=1">
                  <title>chatgpt2api</title>
                  <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 40px; color: #111827; background: #f8fafc; }}
                    main {{ max-width: 760px; margin: 0 auto; padding: 32px; background: white; border-radius: 16px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); }}
                    code {{ background: #e2e8f0; padding: 2px 6px; border-radius: 6px; }}
                    a {{ color: #0369a1; }}
                  </style>
                </head>
                <body>
                  <main>
                    <h1>chatgpt2api</h1>
                    <p>Backend is running, but no prebuilt frontend assets were found.</p>
                    <p>Version: <code>{app_version}</code></p>
                    <p>Health: <a href="/health"><code>/health</code></a></p>
                    <p>API version: <a href="/version"><code>/version</code></a></p>
                    <p>If you want the web UI, build the frontend and place the exported files in <code>web_dist/</code>.</p>
                  </main>
                </body>
                </html>
                """
            )
        return FileResponse(fallback)

    return app
