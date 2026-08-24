import logging
from datetime import datetime, timezone

import aiohttp
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from .config import ForecasterConfig
from .models import NewsItem
from .news_parser import deduplicate, parse_feed

log = logging.getLogger(__name__)

NEWS_SOURCE = "Cointelegraph"
NEWS_FEED_URL = "https://cointelegraph.com/rss/tag/bitcoin"

USER_AGENT = "delphi/0.1 (+bitcoin forecast dashboard)"

_RETRYABLE = (aiohttp.ClientError, TimeoutError)
_UNDATED = datetime(1970, 1, 1, tzinfo=timezone.utc)


class NewsClient:
    def __init__(
        self, session: aiohttp.ClientSession, config: ForecasterConfig
    ) -> None:
        self._session = session
        self._config = config

    async def fetch_bitcoin_news(self) -> list[NewsItem]:
        items = parse_feed(await self._get_text(NEWS_FEED_URL), NEWS_SOURCE)
        items.sort(key=lambda item: item.published_at or _UNDATED, reverse=True)
        return deduplicate(items)[: self._config.news_max_items]

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.5, max=8),
        retry=retry_if_exception_type(_RETRYABLE),
    )
    async def _get_text(self, url: str) -> str:
        timeout = aiohttp.ClientTimeout(total=self._config.request_timeout_s)
        async with self._session.get(
            url,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        ) as response:
            response.raise_for_status()
            return await response.text()
