import importlib.resources
import logging
from datetime import datetime

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .models import CryptoMarket, Forecast, NewsItem

log = logging.getLogger(__name__)

EVENTS_RETAINED = 500
NEWS_RETAINED = 200


class Database:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def apply_schema(self) -> None:
        schema_sql = (
            importlib.resources.files("delphi_backend")
            .joinpath("schema.sql")
            .read_text()
        )
        with psycopg.connect(self._dsn) as conn:
            conn.execute(schema_sql)
            conn.commit()

    def upsert_market(self, market: CryptoMarket) -> None:
        with psycopg.connect(self._dsn) as conn:
            conn.execute(
                """
                INSERT INTO crypto_markets
                    (condition_id, question, slug, asset, target_price,
                     deadline, event_type, direction)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (condition_id) DO UPDATE SET
                    question = EXCLUDED.question,
                    slug = EXCLUDED.slug,
                    target_price = EXCLUDED.target_price,
                    deadline = EXCLUDED.deadline,
                    event_type = EXCLUDED.event_type,
                    direction = EXCLUDED.direction
                """,
                (
                    market.condition_id,
                    market.question,
                    market.slug,
                    market.asset,
                    market.target_price,
                    market.deadline,
                    market.event_type,
                    market.direction,
                ),
            )
            conn.commit()

    def mark_stale_markets(self, current_condition_ids: list[str]) -> int:
        with psycopg.connect(self._dsn) as conn:
            conn.execute(
                """
                UPDATE crypto_markets
                SET last_seen_at = now(), delisted_at = NULL
                WHERE condition_id = ANY(%s)
                """,
                (current_condition_ids,),
            )
            newly_delisted = conn.execute(
                """
                UPDATE crypto_markets
                SET delisted_at = now()
                WHERE condition_id != ALL(%s) AND delisted_at IS NULL
                """,
                (current_condition_ids,),
            ).rowcount
            conn.execute(
                "DELETE FROM forecasts WHERE condition_id != ALL(%s)",
                (current_condition_ids,),
            )
            conn.commit()
        return newly_delisted

    def upsert_forecast(self, forecast: Forecast) -> None:
        with psycopg.connect(self._dsn) as conn:
            conn.execute(
                """
                INSERT INTO forecasts
                    (condition_id, spot_price, sigma, model_probability,
                     market_implied_probability, edge, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (condition_id) DO UPDATE SET
                    spot_price = EXCLUDED.spot_price,
                    sigma = EXCLUDED.sigma,
                    model_probability = EXCLUDED.model_probability,
                    market_implied_probability = EXCLUDED.market_implied_probability,
                    edge = EXCLUDED.edge,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    forecast.condition_id,
                    forecast.spot_price,
                    forecast.sigma,
                    forecast.model_probability,
                    forecast.market_implied_probability,
                    forecast.edge,
                    forecast.updated_at,
                ),
            )
            conn.commit()

    def insert_forecast_history(
        self, forecast: Forecast, years_to_deadline: float
    ) -> None:
        with psycopg.connect(self._dsn) as conn:
            conn.execute(
                """
                INSERT INTO forecast_history
                    (condition_id, spot_price, sigma, model_probability,
                     market_implied_probability, edge, years_to_deadline,
                     recorded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    forecast.condition_id,
                    forecast.spot_price,
                    forecast.sigma,
                    forecast.model_probability,
                    forecast.market_implied_probability,
                    forecast.edge,
                    years_to_deadline,
                    forecast.updated_at,
                ),
            )
            conn.commit()

    def fetch_unresolved_delisted_ids(self, limit: int = 50) -> list[str]:
        with psycopg.connect(self._dsn) as conn:
            rows = conn.execute(
                """
                SELECT m.condition_id
                FROM crypto_markets m
                LEFT JOIN market_resolutions r ON r.condition_id = m.condition_id
                WHERE m.delisted_at IS NOT NULL AND r.condition_id IS NULL
                ORDER BY m.delisted_at ASC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        return [row[0] for row in rows]

    def record_resolution(
        self, condition_id: str, outcome: bool, outcome_prices: str
    ) -> None:
        with psycopg.connect(self._dsn) as conn:
            conn.execute(
                """
                INSERT INTO market_resolutions
                    (condition_id, outcome, outcome_prices)
                VALUES (%s, %s, %s)
                ON CONFLICT (condition_id) DO NOTHING
                """,
                (condition_id, outcome, outcome_prices),
            )
            conn.commit()

    def upsert_health(
        self,
        api_name: str,
        status: str,
        latency_ms: float,
        checked_at: datetime,
        error: str | None = None,
    ) -> None:
        with psycopg.connect(self._dsn) as conn:
            conn.execute(
                """
                INSERT INTO api_health
                    (api_name, status, latency_ms, last_checked_at,
                     last_success_at, last_error)
                VALUES (%(api_name)s, %(status)s, %(latency_ms)s, %(checked_at)s,
                        CASE WHEN %(status)s = 'up' THEN %(checked_at)s ELSE NULL END,
                        %(error)s)
                ON CONFLICT (api_name) DO UPDATE SET
                    status = EXCLUDED.status,
                    latency_ms = EXCLUDED.latency_ms,
                    last_checked_at = EXCLUDED.last_checked_at,
                    last_success_at = CASE
                        WHEN EXCLUDED.status = 'up' THEN EXCLUDED.last_checked_at
                        ELSE api_health.last_success_at
                    END,
                    last_error = CASE
                        WHEN EXCLUDED.status = 'up' THEN NULL
                        ELSE EXCLUDED.last_error
                    END
                """,
                {
                    "api_name": api_name,
                    "status": status,
                    "latency_ms": latency_ms,
                    "checked_at": checked_at,
                    "error": error,
                },
            )
            conn.commit()

    def insert_event(
        self,
        level: str,
        step: str,
        message: str,
        api: str | None = None,
        detail: dict | None = None,
    ) -> None:
        with psycopg.connect(self._dsn) as conn:
            conn.execute(
                """
                INSERT INTO app_events (level, api, step, message, detail)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    level,
                    api,
                    step,
                    message,
                    Jsonb(detail) if detail is not None else None,
                ),
            )
            conn.execute(
                """
                DELETE FROM app_events
                WHERE id NOT IN (SELECT id FROM app_events ORDER BY id DESC LIMIT %s)
                """,
                (EVENTS_RETAINED,),
            )
            conn.commit()

    def fetch_forecasts(self) -> list[dict]:
        with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
            return conn.execute(
                """
                SELECT
                    m.condition_id,
                    m.question,
                    m.slug,
                    m.asset,
                    m.target_price,
                    m.deadline,
                    m.event_type,
                    m.direction,
                    f.spot_price,
                    f.sigma,
                    f.model_probability,
                    f.market_implied_probability,
                    f.edge,
                    f.updated_at
                FROM crypto_markets m
                JOIN forecasts f ON f.condition_id = m.condition_id
                WHERE m.delisted_at IS NULL
                ORDER BY m.deadline ASC
                """
            ).fetchall()

    def fetch_health(self) -> list[dict]:
        with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
            return conn.execute(
                """
                SELECT api_name, status, latency_ms, last_checked_at, last_success_at, last_error
                FROM api_health
                ORDER BY api_name ASC
                """
            ).fetchall()

    def fetch_events(self, api: str | None = None, limit: int = 100) -> list[dict]:
        with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
            if api is not None:
                query = """
                    SELECT id, ts, level, api, step, message, detail
                    FROM app_events
                    WHERE api = %s
                    ORDER BY id DESC
                    LIMIT %s
                """
                params = (api, limit)
            else:
                query = """
                    SELECT id, ts, level, api, step, message, detail
                    FROM app_events
                    ORDER BY id DESC
                    LIMIT %s
                """
                params = (limit,)
            return conn.execute(query, params).fetchall()

    def fetch_scored_forecasts(self) -> list[dict]:
        with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
            return conn.execute(
                """
                SELECT DISTINCT ON (h.condition_id)
                    h.condition_id,
                    m.question,
                    m.event_type,
                    m.direction,
                    h.model_probability,
                    h.market_implied_probability,
                    h.years_to_deadline,
                    h.recorded_at,
                    r.outcome,
                    r.resolved_at
                FROM forecast_history h
                JOIN market_resolutions r ON r.condition_id = h.condition_id
                JOIN crypto_markets m ON m.condition_id = h.condition_id
                ORDER BY h.condition_id, h.recorded_at DESC
                """
            ).fetchall()

    def upsert_news_items(self, items: list[NewsItem]) -> int:
        if not items:
            return 0

        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO news_items
                        (url, title, source, summary, published_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE SET
                        title = EXCLUDED.title,
                        source = EXCLUDED.source,
                        summary = EXCLUDED.summary,
                        published_at = EXCLUDED.published_at
                    """,
                    [
                        (
                            item.url,
                            item.title,
                            item.source,
                            item.summary,
                            item.published_at,
                        )
                        for item in items
                    ],
                )
            conn.execute(
                """
                DELETE FROM news_items
                WHERE url NOT IN (
                    SELECT url FROM news_items
                    ORDER BY published_at DESC NULLS LAST, fetched_at DESC
                    LIMIT %s
                )
                """,
                (NEWS_RETAINED,),
            )
            conn.commit()
        return len(items)

    def fetch_news(self, limit: int = 30) -> list[dict]:
        with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
            return conn.execute(
                """
                SELECT url, title, source, summary, published_at, fetched_at
                FROM news_items
                ORDER BY published_at DESC NULLS LAST, fetched_at DESC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
