from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CryptoMarket:
    condition_id: str
    question: str
    slug: str
    asset: str
    target_price: float
    deadline: datetime
    event_type: str
    direction: str
    best_bid: float | None
    best_ask: float | None

    @property
    def market_implied_probability(self) -> float | None:
        if self.best_bid is not None and self.best_ask is not None:
            return (self.best_bid + self.best_ask) / 2.0
        if self.best_bid is not None:
            return self.best_bid
        if self.best_ask is not None:
            return self.best_ask
        return None


@dataclass(frozen=True)
class Forecast:
    condition_id: str
    spot_price: float
    sigma: float
    model_probability: float
    market_implied_probability: float | None
    updated_at: datetime

    @property
    def edge(self) -> float | None:
        if self.market_implied_probability is None:
            return None
        return self.model_probability - self.market_implied_probability


@dataclass(frozen=True)
class NewsItem:
    url: str
    title: str
    source: str
    summary: str | None
    published_at: datetime | None
