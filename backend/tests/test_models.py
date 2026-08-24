from datetime import datetime, timezone

from delphi_backend.models import CryptoMarket


def _make_market(best_bid, best_ask) -> CryptoMarket:
    return CryptoMarket(
        condition_id="0x1",
        question="Will Bitcoin reach $150,000 by December 31?",
        slug="test",
        asset="BTC",
        target_price=150_000,
        deadline=datetime(2026, 12, 31, tzinfo=timezone.utc),
        event_type="barrier",
        direction="up",
        best_bid=best_bid,
        best_ask=best_ask,
    )


def test_midpoint_when_both_quoted():
    assert _make_market(0.4, 0.5).market_implied_probability == 0.45


def test_falls_back_to_ask_when_bid_missing():
    assert _make_market(None, 0.001).market_implied_probability == 0.001


def test_falls_back_to_bid_when_ask_missing():
    assert _make_market(0.99, None).market_implied_probability == 0.99


def test_none_when_both_missing():
    assert _make_market(None, None).market_implied_probability is None
