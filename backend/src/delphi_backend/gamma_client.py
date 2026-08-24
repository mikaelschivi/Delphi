import json
import logging
from typing import Any

import aiohttp
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from .config import ForecasterConfig

log = logging.getLogger(__name__)

GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"

_RETRYABLE = (aiohttp.ClientError, TimeoutError)


class GammaClient:
    def __init__(
        self, session: aiohttp.ClientSession, config: ForecasterConfig
    ) -> None:
        self._session = session
        self._config = config

    async def fetch_active_markets(self) -> list[dict[str, Any]]:
        all_markets: list[dict[str, Any]] = []
        offset = 0
        while offset < self._config.gamma_max_offset:
            market_page = await self._get_with_retry(
                GAMMA_MARKETS_URL,
                params=[
                    ("active", "true"),
                    ("closed", "false"),
                    ("order", "volume"),
                    ("ascending", "false"),
                    ("limit", str(self._config.gamma_page_limit)),
                    ("offset", str(offset)),
                ],
            )
            if not market_page:
                break
            all_markets.extend(market_page)
            if len(market_page) < self._config.gamma_page_limit:
                break
            offset += self._config.gamma_page_limit
        return all_markets

    async def fetch_closed_markets_by_condition_id(
        self, condition_ids: list[str]
    ) -> list[dict[str, Any]]:
        if not condition_ids:
            return []

        found: list[dict[str, Any]] = []
        batch_size = self._config.gamma_page_limit
        for start in range(0, len(condition_ids), batch_size):
            batch = condition_ids[start : start + batch_size]
            params = [("closed", "true"), ("limit", str(len(batch)))]
            params.extend(("condition_ids", condition_id) for condition_id in batch)
            found.extend(await self._get_with_retry(GAMMA_MARKETS_URL, params))
        return found

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=0.5, max=8),
        retry=retry_if_exception_type(_RETRYABLE),
    )
    async def _get_with_retry(
        self, url: str, params: list[tuple[str, str]]
    ) -> list[dict[str, Any]]:
        timeout = aiohttp.ClientTimeout(total=self._config.request_timeout_s)
        async with self._session.get(url, params=params, timeout=timeout) as response:
            response.raise_for_status()
            response_text = await response.text()
            payload = json.loads(response_text)
            return payload if isinstance(payload, list) else []
