import logging
from datetime import datetime, timedelta, timezone

import aiohttp
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from .config import ForecasterConfig

log = logging.getLogger(__name__)

SPOT_PRICE_URL = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
CANDLES_URL = "https://api.exchange.coinbase.com/products/BTC-USD/candles"
DAY_GRANULARITY_S = 86400

_RETRYABLE = (aiohttp.ClientError, TimeoutError)


class CoinbaseClient:
    def __init__(
        self, session: aiohttp.ClientSession, config: ForecasterConfig
    ) -> None:
        self._session = session
        self._config = config

    async def fetch_spot_price_usd(self) -> float:
        payload = await self._get_json(SPOT_PRICE_URL, params={})
        return float(payload["data"]["amount"])

    async def fetch_price_history(self) -> list[float]:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=self._config.volatility_lookback_days)
        candles = await self._get_json(
            CANDLES_URL,
            params={
                "granularity": str(DAY_GRANULARITY_S),
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
        )
        closing_prices = [float(candle[4]) for candle in candles]
        return list(reversed(closing_prices))

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=0.5, max=8),
        retry=retry_if_exception_type(_RETRYABLE),
    )
    async def _get_json(self, url: str, params: dict[str, str]):
        timeout = aiohttp.ClientTimeout(total=self._config.request_timeout_s)
        async with self._session.get(url, params=params, timeout=timeout) as response:
            response.raise_for_status()
            return await response.json(content_type=None)
