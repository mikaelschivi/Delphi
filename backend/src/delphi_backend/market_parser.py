import json
import re
from datetime import datetime, timezone
from typing import Any

from .models import CryptoMarket

_ASSET_RE = re.compile(r"\b(bitcoin|btc)\b", re.IGNORECASE)

_RANGE_RE = re.compile(r"\bbetween\b", re.IGNORECASE)

_PRICE_RE = re.compile(r"\$\s?([\d,]+(?:\.\d+)?)\s?(k|K|m|M)?")

_BARRIER_WORDS = re.compile(r"\b(reach|hit|top|exceed|surpass|touch)\b", re.IGNORECASE)
_TERMINAL_WORDS = re.compile(
    r"\b(above|below|over|under|at least|at most|greater than|less than)\b",
    re.IGNORECASE,
)
_DOWN_WORDS = re.compile(
    r"\b(below|under|at most|less than|drop|fall|dip|crash)\b", re.IGNORECASE
)


def _parse_price(question: str) -> float | None:
    match = _PRICE_RE.search(question)
    if not match:
        return None
    number = float(match.group(1).replace(",", ""))
    suffix = (match.group(2) or "").lower()
    if suffix == "k":
        number *= 1_000
    elif suffix == "m":
        number *= 1_000_000
    return number


def _classify_event_type(question: str) -> str:
    if _BARRIER_WORDS.search(question):
        return "barrier"
    if _TERMINAL_WORDS.search(question):
        return "terminal"
    return "barrier" if re.search(r"\bby\b", question, re.IGNORECASE) else "terminal"


def _classify_direction(question: str) -> str:
    return "down" if _DOWN_WORDS.search(question) else "up"


def parse_market(raw_market: dict[str, Any]) -> CryptoMarket | None:
    question = raw_market.get("question") or ""
    if not _ASSET_RE.search(question):
        return None
    if _RANGE_RE.search(question):
        return None

    target_price = _parse_price(question)
    if target_price is None:
        return None

    raw_deadline = raw_market.get("endDate")
    if not raw_deadline:
        return None
    try:
        deadline = datetime.fromisoformat(str(raw_deadline).replace("Z", "+00:00"))
    except ValueError:
        return None
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    condition_id = raw_market.get("conditionId")
    if not condition_id:
        return None

    best_bid = raw_market.get("bestBid")
    best_ask = raw_market.get("bestAsk")

    return CryptoMarket(
        condition_id=str(condition_id),
        question=question,
        slug=str(raw_market.get("slug", "")),
        asset="BTC",
        target_price=target_price,
        deadline=deadline,
        event_type=_classify_event_type(question),
        direction=_classify_direction(question),
        best_bid=float(best_bid) if best_bid is not None else None,
        best_ask=float(best_ask) if best_ask is not None else None,
    )


def _parse_json_list(raw: Any) -> list[str] | None:
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, str):
        try:
            decoded = json.loads(raw)
        except ValueError:
            return None
        if isinstance(decoded, list):
            return [str(item) for item in decoded]
    return None


def parse_resolution(raw_market: dict[str, Any]) -> bool | None:
    if not raw_market.get("closed"):
        return None

    outcomes = _parse_json_list(raw_market.get("outcomes"))
    prices = _parse_json_list(raw_market.get("outcomePrices"))
    if not outcomes or not prices or len(outcomes) != len(prices) or len(prices) != 2:
        return None

    try:
        numeric_prices = [float(price) for price in prices]
    except ValueError:
        return None

    winners = [i for i, price in enumerate(numeric_prices) if price > 0.99]
    losers = [i for i, price in enumerate(numeric_prices) if price < 0.01]
    if len(winners) != 1 or len(losers) != 1:
        return None

    yes_index = next(
        (i for i, label in enumerate(outcomes) if label.strip().lower() == "yes"), 0
    )
    return winners[0] == yes_index
