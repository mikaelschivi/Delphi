from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from .calibration import summarize
from .db import Database

router = APIRouter()


def get_db(request: Request) -> Database:
    return request.app.state.db


@router.get("/api/forecasts")
def api_forecasts(request: Request):
    db = get_db(request)
    return JSONResponse(jsonable_encoder(db.fetch_forecasts()))


@router.get("/api/health")
def api_health(request: Request):
    db = get_db(request)
    return JSONResponse(jsonable_encoder(db.fetch_health()))


@router.get("/api/events")
def api_events(request: Request, api: str | None = None, limit: int = 100):
    db = get_db(request)
    return JSONResponse(jsonable_encoder(db.fetch_events(api=api, limit=min(limit, 500))))


@router.get("/api/calibration")
def api_calibration(request: Request):
    db = get_db(request)
    return JSONResponse(jsonable_encoder(summarize(db.fetch_scored_forecasts())))


@router.get("/api/news")
def api_news(request: Request, limit: int = 30):
    db = get_db(request)
    return JSONResponse(jsonable_encoder(db.fetch_news(limit=min(limit, 100))))


@router.get("/healthz")
def healthz():
    return {"status": "ok"}
