from delphi_backend.market_parser import parse_market, parse_resolution


def _raw(question: str, **overrides) -> dict:
    base = {
        "question": question,
        "slug": "test-slug",
        "conditionId": "0xabc",
        "endDate": "2026-12-31T00:00:00Z",
        "bestBid": 0.4,
        "bestAsk": 0.5,
    }
    base.update(overrides)
    return base


def test_barrier_reach_by_date():
    m = parse_market(_raw("Will Bitcoin reach $150,000 by December 31?"))
    assert m is not None
    assert m.asset == "BTC"
    assert m.target_price == 150_000
    assert m.event_type == "barrier"
    assert m.direction == "up"


def test_terminal_above_on_date():
    m = parse_market(_raw("Will Bitcoin be above $120k on December 31?"))
    assert m is not None
    assert m.target_price == 120_000
    assert m.event_type == "terminal"
    assert m.direction == "up"


def test_terminal_below():
    m = parse_market(_raw("Will Bitcoin be below $80,000 on December 31?"))
    assert m is not None
    assert m.target_price == 80_000
    assert m.event_type == "terminal"
    assert m.direction == "down"


def test_barrier_drop_to():
    m = parse_market(_raw("Will Bitcoin drop to $60,000 by year end?"))
    assert m is not None
    assert m.event_type == "barrier"
    assert m.direction == "down"


def test_non_crypto_market_is_skipped():
    m = parse_market(_raw("Will the Fed cut rates in December?"))
    assert m is None


def test_missing_target_price_is_skipped():
    m = parse_market(_raw("Will Bitcoin hit a new all-time high?"))
    assert m is None


def test_range_market_is_skipped():
    m = parse_market(
        _raw("Will the price of Bitcoin be between $60,000 and $62,000 on August 18?")
    )
    assert m is None


def test_missing_condition_id_is_skipped():
    m = parse_market(_raw("Will Bitcoin reach $150,000?", conditionId=None))
    assert m is None


def test_million_suffix():
    m = parse_market(_raw("Will Bitcoin reach $1.5m by 2030?"))
    assert m is not None
    assert m.target_price == 1_500_000


def test_parse_resolution_reads_yes_win():
    assert (
        parse_resolution(
            {
                "closed": True,
                "outcomes": '["Yes", "No"]',
                "outcomePrices": '["1", "0"]',
            }
        )
        is True
    )


def test_parse_resolution_reads_no_win():
    assert (
        parse_resolution(
            {
                "closed": True,
                "outcomes": '["Yes", "No"]',
                "outcomePrices": '["0", "1"]',
            }
        )
        is False
    )


def test_parse_resolution_follows_outcome_order():
    assert (
        parse_resolution(
            {
                "closed": True,
                "outcomes": '["No", "Yes"]',
                "outcomePrices": '["0", "1"]',
            }
        )
        is True
    )


def test_parse_resolution_ignores_open_market():
    assert (
        parse_resolution(
            {
                "closed": False,
                "outcomes": '["Yes", "No"]',
                "outcomePrices": '["1", "0"]',
            }
        )
        is None
    )


def test_parse_resolution_ignores_unsettled_prices():
    assert (
        parse_resolution(
            {
                "closed": True,
                "outcomes": '["Yes", "No"]',
                "outcomePrices": '["0.5", "0.5"]',
            }
        )
        is None
    )


def test_parse_resolution_ignores_malformed_payload():
    assert parse_resolution({"closed": True, "outcomes": "not json"}) is None
    assert (
        parse_resolution(
            {"closed": True, "outcomes": '["Yes"]', "outcomePrices": '["1"]'}
        )
        is None
    )
