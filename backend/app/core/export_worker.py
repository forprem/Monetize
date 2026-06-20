from __future__ import annotations

import asyncio
import logging

from app.adapters.contracts import ExportStore

logger = logging.getLogger(__name__)


class ExportWorker:
    def __init__(
        self,
        export_store: ExportStore,
        poll_interval_seconds: float = 5.0,
        batch_size: int = 25,
    ) -> None:
        self.export_store = export_store
        self.poll_interval_seconds = poll_interval_seconds
        self.batch_size = batch_size
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return

        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run(), name="export-worker")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is None:
            return

        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.export_store.process_pending_export_jobs(limit=self.batch_size)
            except Exception:
                logger.exception("Export worker iteration failed")

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.poll_interval_seconds)
            except asyncio.TimeoutError:
                continue