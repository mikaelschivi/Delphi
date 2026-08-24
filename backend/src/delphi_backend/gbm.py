import math

_SQRT2 = math.sqrt(2.0)


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / _SQRT2))


def terminal_probability(
    spot: float, target: float, sigma: float, years: float, direction: str
) -> float:
    if spot <= 0 or target <= 0:
        raise ValueError("spot and target must be positive")
    if sigma <= 0 or years <= 0:
        target_already_met = spot >= target if direction == "up" else spot <= target
        return 1.0 if target_already_met else 0.0

    z_score = (math.log(spot / target) - 0.5 * sigma**2 * years) / (
        sigma * math.sqrt(years)
    )
    return _norm_cdf(z_score) if direction == "up" else _norm_cdf(-z_score)


def barrier_touch_probability(
    spot: float, barrier: float, sigma: float, years: float
) -> float:
    if spot <= 0 or barrier <= 0:
        raise ValueError("spot and barrier must be positive")
    if sigma <= 0 or years <= 0:
        return 1.0 if spot == barrier else 0.0

    log_drift = -0.5 * sigma**2
    log_barrier_distance = math.log(barrier / spot)
    reflection_sign = 1.0 if log_barrier_distance >= 0 else -1.0
    log_barrier_distance = abs(log_barrier_distance)

    effective_log_drift = log_drift * reflection_sign
    diffusion_scale = sigma * math.sqrt(years)
    direct_term = _norm_cdf(
        (effective_log_drift * years - log_barrier_distance) / diffusion_scale
    )
    reflected_term = math.exp(
        2 * effective_log_drift * log_barrier_distance / sigma**2
    ) * _norm_cdf(
        (-effective_log_drift * years - log_barrier_distance) / diffusion_scale
    )
    return direct_term + reflected_term
