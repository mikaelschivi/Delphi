from dataclasses import dataclass


@dataclass(frozen=True)
class ForecasterConfig:
    poll_interval_s: float = 60.0
    gamma_page_limit: int = 100
    gamma_max_offset: int = 2000
    request_timeout_s: float = 15.0
    max_retries: int = 4
    volatility_lookback_days: int = 90
    news_max_items: int = 40

    def __post_init__(self) -> None:
        if self.poll_interval_s <= 0:
            raise ValueError("poll_interval_s must be positive")
        if self.gamma_page_limit <= 0 or self.gamma_page_limit > 100:
            raise ValueError("gamma_page_limit must be in (0, 100]")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.news_max_items <= 0:
            raise ValueError("news_max_items must be positive")
        if not (0 < self.volatility_lookback_days <= 300):
            raise ValueError(
                "volatility_lookback_days must be in (0, 300] (Coinbase candle cap)"
            )
