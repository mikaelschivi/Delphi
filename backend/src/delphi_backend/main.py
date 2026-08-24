import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from .config import ForecasterConfig
from .db import Database
from .engine_loop import run_forever
from .routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database(os.environ["DATABASE_URL"])
    db.apply_schema()
    app.state.db = db

    poll_interval_s = float(os.environ.get("POLL_INTERVAL_S", "60"))
    config = ForecasterConfig(poll_interval_s=poll_interval_s)
    stop_event = asyncio.Event()
    engine_task = asyncio.create_task(run_forever(config, db, stop_event))

    yield

    stop_event.set()
    await engine_task


def create_app() -> FastAPI:
    app = FastAPI(title="delphi", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()


def run() -> None:
    uvicorn.run("delphi_backend.main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
