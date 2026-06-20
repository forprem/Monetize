from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.container import container
from app.core.export_worker import ExportWorker
from app.core.settings import settings


def _build_export_worker() -> ExportWorker:
    return ExportWorker(
        export_store=container.export_store,
        poll_interval_seconds=settings.export_worker_poll_interval_seconds,
        batch_size=settings.export_worker_batch_size,
    )


def create_app() -> FastAPI:
    export_worker = _build_export_worker()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if settings.export_worker_enabled:
            await export_worker.start()
        try:
            yield
        finally:
            await export_worker.stop()

    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()
