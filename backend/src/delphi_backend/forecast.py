import logging
from datetime import datetime, timezone

import aiohttp

from .coinbase_client import CoinbaseClient
from .config import ForecasterConfig
from .db import Database
from .events import EventLogger
from .gamma_client import GammaClient
from .gbm import barrier_touch_probability, terminal_probability
from .market_parser import parse_market, parse_resolution
from .models import Forecast
from .news_client import NEWS_SOURCE, NewsClient
from .volatility import annualized_volatility

log = logging.getLogger(__name__)


def _years_until(deadline: datetime) -> float:
    now = datetime.now(timezone.utc)
    seconds_remaining = (deadline - now).total_seconds()
    return max(seconds_remaining, 0.0) / (365.0 * 24 * 3600)


async def run_poll_cycle(
    session: aiohttp.ClientSession,
    config: ForecasterConfig,
    db: Database,
    events: EventLogger,
) -> int:
    gamma = GammaClient(session, config)
    coinbase = CoinbaseClient(session, config)

    events.info("poll_cycle", "starting poll cycle")

    with events.timed_api_call("gamma", "fetch_markets"):
        raw_markets = await gamma.fetch_active_markets()
    events.info(
        "fetch_markets",
        f"received {len(raw_markets)} active markets from Polymarket Gamma",
        api="gamma",
        detail={"count": len(raw_markets)},
    )

    crypto_markets = [
        parsed_market
        for raw_market in raw_markets
        if (parsed_market := parse_market(raw_market)) is not None
    ]
    events.info(
        "parse_markets",
        f"identified {len(crypto_markets)} BTC price-target markets after parsing",
        detail={"count": len(crypto_markets)},
    )
    if not crypto_markets:
        events.info("poll_cycle", "no crypto price-target markets found this cycle")
        return 0

    newly_delisted = db.mark_stale_markets(
        [market.condition_id for market in crypto_markets]
    )
    events.info(
        "delist",
        f"{len(crypto_markets)} markets live, {newly_delisted} newly delisted",
        detail={"live": len(crypto_markets), "newly_delisted": newly_delisted},
    )

    with events.timed_api_call("coinbase", "fetch_spot"):
        spot_price = await coinbase.fetch_spot_price_usd()
    events.info(
        "fetch_spot",
        f"BTC-USD spot ${spot_price:,.2f}",
        api="coinbase",
        detail={"spot_price": spot_price},
    )

    with events.timed_api_call("coinbase", "fetch_history"):
        daily_closes = await coinbase.fetch_price_history()
    events.info(
        "fetch_history",
        f"received {len(daily_closes)} daily candles from Coinbase",
        api="coinbase",
        detail={"count": len(daily_closes)},
    )

    sigma = annualized_volatility(daily_closes)
    events.info(
        "volatility",
        f"annualized volatility sigma={sigma:.4f}",
        detail={"sigma": sigma},
    )

    forecast_timestamp = datetime.now(timezone.utc)

    for market in crypto_markets:
        db.upsert_market(market)

        years_to_deadline = _years_until(market.deadline)
        if market.event_type == "barrier":
            model_probability = barrier_touch_probability(
                spot_price, market.target_price, sigma, years_to_deadline
            )
        else:
            model_probability = terminal_probability(
                spot_price,
                market.target_price,
                sigma,
                years_to_deadline,
                market.direction,
            )

        forecast = Forecast(
            condition_id=market.condition_id,
            spot_price=spot_price,
            sigma=sigma,
            model_probability=model_probability,
            market_implied_probability=market.market_implied_probability,
            updated_at=forecast_timestamp,
        )
        db.upsert_forecast(forecast)
        db.insert_forecast_history(forecast, years_to_deadline)

    await sweep_resolutions(gamma, db, events)
    await refresh_news(session, config, db, events)

    events.info(
        "poll_cycle",
        f"cycle complete: forecasted {len(crypto_markets)} markets, "
        f"spot=${spot_price:,.2f}, sigma={sigma:.4f}",
        detail={"count": len(crypto_markets), "spot_price": spot_price, "sigma": sigma},
    )
    return len(crypto_markets)


async def sweep_resolutions(
    gamma: GammaClient, db: Database, events: EventLogger
) -> int:
    pending_ids = db.fetch_unresolved_delisted_ids()
    if not pending_ids:
        return 0

    with events.timed_api_call("gamma", "fetch_resolutions"):
        closed_markets = await gamma.fetch_closed_markets_by_condition_id(pending_ids)

    recorded = 0
    for raw_market in closed_markets:
        condition_id = raw_market.get("conditionId")
        outcome = parse_resolution(raw_market)
        if condition_id is None or outcome is None:
            continue
        db.record_resolution(
            str(condition_id), outcome, str(raw_market.get("outcomePrices", ""))
        )
        recorded += 1

    events.info(
        "resolutions",
        f"checked {len(pending_ids)} delisted markets, recorded {recorded} outcomes",
        api="gamma",
        detail={"pending": len(pending_ids), "recorded": recorded},
    )
    return recorded


async def refresh_news(
    session: aiohttp.ClientSession,
    config: ForecasterConfig,
    db: Database,
    events: EventLogger,
) -> int:
    news = NewsClient(session, config)
    try:
        with events.timed_api_call("news", "fetch_news"):
            items = await news.fetch_bitcoin_news()
    except Exception as exc:
        log.warning("news refresh failed: %s", exc)
        return 0

    stored = db.upsert_news_items(items)
    events.info(
        "news",
        f"stored {stored} Bitcoin headlines from {NEWS_SOURCE}",
        api="news",
        detail={"count": stored, "source": NEWS_SOURCE},
    )
    return stored
