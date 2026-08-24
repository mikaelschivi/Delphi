import logging
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from .db import Database

log = logging.getLogger("delphi_backend.events")


class EventLogger:
    def __init__(self, db: Database) -> None:
        self._db = db

    def info(
        self,
        step: str,
        message: str,
        api: str | None = None,
        detail: dict | None = None,
    ) -> None:
        self._emit("info", step, message, api, detail)

    def warning(
        self,
        step: str,
        message: str,
        api: str | None = None,
        detail: dict | None = None,
    ) -> None:
        self._emit("warning", step, message, api, detail)

    def error(
        self,
        step: str,
        message: str,
        api: str | None = None,
        detail: dict | None = None,
    ) -> None:
        self._emit("error", step, message, api, detail)

    def _emit(
        self,
        level: str,
        step: str,
        message: str,
        api: str | None,
        detail: dict | None,
    ) -> None:
        getattr(log, level)("[%s] %s", step, message)
        try:
            self._db.insert_event(level, step, message, api=api, detail=detail)
        except Exception:
            log.exception("failed to persist event to app_events")

    @contextmanager
    def timed_api_call(self, api: str, step: str) -> Iterator[None]:
        start_time = time.monotonic()
        try:
            yield
        except Exception as exc:
            latency_ms = (time.monotonic() - start_time) * 1000
            self._emit(
                "error",
                step,
                f"{api} call failed: {exc}",
                api,
                {"latency_ms": round(latency_ms, 1)},
            )
            self._db.upsert_health(
                api, "down", latency_ms, datetime.now(timezone.utc), error=str(exc)
            )
            raise
        else:
            latency_ms = (time.monotonic() - start_time) * 1000
            self._db.upsert_health(api, "up", latency_ms, datetime.now(timezone.utc))
