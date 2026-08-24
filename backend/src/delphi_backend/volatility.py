import math

TRADING_DAYS_PER_YEAR = 365


def annualized_volatility(daily_closes: list[float]) -> float:
    if len(daily_closes) < 2:
        raise ValueError("need at least 2 daily closes to compute volatility")

    log_returns = [
        math.log(daily_closes[i] / daily_closes[i - 1])
        for i in range(1, len(daily_closes))
        if daily_closes[i - 1] > 0 and daily_closes[i] > 0
    ]
    if len(log_returns) < 2:
        raise ValueError("insufficient valid daily closes to compute volatility")

    mean_return = sum(log_returns) / len(log_returns)
    variance = sum((r - mean_return) ** 2 for r in log_returns) / (len(log_returns) - 1)
    daily_volatility = math.sqrt(variance)
    return daily_volatility * math.sqrt(TRADING_DAYS_PER_YEAR)
