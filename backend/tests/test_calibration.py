import pytest

from delphi_backend.calibration import brier_score, calibration_buckets, summarize


def test_brier_score_rewards_confident_correct_forecasts():
    assert brier_score([(1.0, True), (0.0, False)]) == 0.0
    assert brier_score([(0.0, True), (1.0, False)]) == 1.0
    assert brier_score([(0.5, True), (0.5, False)]) == 0.25


def test_brier_score_of_empty_sample_is_none():
    assert brier_score([]) is None


def test_calibration_buckets_group_by_forecast_probability():
    buckets = calibration_buckets([(0.05, False), (0.95, True), (0.95, False)], 10)

    assert buckets[0]["count"] == 1
    assert buckets[0]["observed_frequency"] == 0.0
    assert buckets[9]["count"] == 2
    assert buckets[9]["observed_frequency"] == 0.5
    assert buckets[5]["count"] == 0
    assert buckets[5]["mean_forecast"] is None


def test_calibration_buckets_put_probability_of_one_in_last_bucket():
    buckets = calibration_buckets([(1.0, True)], 10)

    assert buckets[9]["count"] == 1


def test_calibration_buckets_reject_non_positive_bucket_count():
    with pytest.raises(ValueError):
        calibration_buckets([(0.5, True)], 0)


def test_summarize_compares_model_and_market_on_the_same_markets():
    rows = [
        {"model_probability": 0.9, "market_implied_probability": 0.6, "outcome": True},
        {"model_probability": 0.2, "market_implied_probability": 0.4, "outcome": False},
        {"model_probability": 0.7, "market_implied_probability": None, "outcome": True},
    ]

    result = summarize(rows)

    assert result["resolved_markets"] == 3
    assert result["compared_markets"] == 2
    assert result["model_brier_compared"] == pytest.approx((0.01 + 0.04) / 2)
    assert result["market_brier_compared"] == pytest.approx((0.16 + 0.16) / 2)
    assert result["skill_vs_market"] == pytest.approx(0.16 - 0.025)
    assert result["base_rate"] == pytest.approx(2 / 3)


def test_summarize_without_resolutions_reports_no_scores():
    result = summarize([])

    assert result["resolved_markets"] == 0
    assert result["model_brier"] is None
    assert result["skill_vs_market"] is None
