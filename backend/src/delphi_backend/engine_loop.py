import asyncio
import logging

import aiohttp

from .config import ForecasterConfig
from .db import Database
from .events import EventLogger
from .forecast import run_poll_cycle

log = logging.getLogger(__name__)


async def run_forever(config: ForecasterConfig, db: Database, stop_event: asyncio.Event) -> None:
    events = EventLogger(db)
    async with aiohttp.ClientSession() as session:
        while not stop_event.is_set():
            try:
                await run_poll_cycle(session, config, db, events)
            except Exception as exc:
                log.exception("poll cycle failed")
                events.error("poll_cycle", f"poll cycle failed: {exc}")
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=config.poll_interval_s)
            except asyncio.TimeoutError:
                pass
