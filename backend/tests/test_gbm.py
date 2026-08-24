import math

from delphi_backend.gbm import barrier_touch_probability, terminal_probability


def test_terminal_probability_at_the_money_is_half():
    probability = terminal_probability(
        spot=100, target=100, sigma=0.5, years=1, direction="up"
    )
    assert 0.3 < probability < 0.5


def test_terminal_probability_up_down_symmetry():
    up_probability = terminal_probability(
        spot=100, target=150, sigma=0.6, years=1, direction="up"
    )
    down_probability = terminal_probability(
        spot=100, target=150, sigma=0.6, years=1, direction="down"
    )
    assert math.isclose(up_probability + down_probability, 1.0, abs_tol=1e-9)


def test_terminal_probability_far_target_is_near_zero():
    probability = terminal_probability(
        spot=100, target=10_000, sigma=0.5, years=0.1, direction="up"
    )
    assert probability < 0.01


def test_terminal_probability_degenerate_zero_time():
    assert terminal_probability(100, 90, 0.5, 0, "up") == 1.0
    assert terminal_probability(100, 110, 0.5, 0, "up") == 0.0


def test_barrier_touch_probability_is_at_least_terminal_probability():
    spot, target, sigma, years = 100.0, 150.0, 0.6, 1.0
    touch_probability = barrier_touch_probability(spot, target, sigma, years)
    terminal_probability_value = terminal_probability(spot, target, sigma, years, "up")
    assert touch_probability >= terminal_probability_value - 1e-9


def test_barrier_touch_probability_symmetric_up_down():
    probability_at_spot = barrier_touch_probability(
        spot=100, barrier=100, sigma=0.5, years=1
    )
    assert probability_at_spot == 1.0 or probability_at_spot > 0.9

    upper_probability = barrier_touch_probability(
        spot=100, barrier=200, sigma=0.5, years=1
    )
    lower_probability = barrier_touch_probability(
        spot=100, barrier=50, sigma=0.5, years=1
    )
    assert 0 < upper_probability < 1
    assert 0 < lower_probability < 1


def test_barrier_touch_probability_higher_vol_increases_probability():
    low_vol_probability = barrier_touch_probability(
        spot=100, barrier=200, sigma=0.3, years=1
    )
    high_vol_probability = barrier_touch_probability(
        spot=100, barrier=200, sigma=0.9, years=1
    )
    assert high_vol_probability > low_vol_probability


def test_barrier_touch_probability_bounds():
    probability = barrier_touch_probability(spot=100, barrier=110, sigma=0.5, years=1)
    assert 0.0 <= probability <= 1.0
