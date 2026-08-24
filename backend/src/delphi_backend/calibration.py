from typing import Any

DEFAULT_BUCKET_COUNT = 10


def brier_score(pairs: list[tuple[float, bool]]) -> float | None:
    if not pairs:
        return None
    return sum((probability - float(outcome)) ** 2 for probability, outcome in pairs) / len(pairs)


def calibration_buckets(
    pairs: list[tuple[float, bool]], bucket_count: int = DEFAULT_BUCKET_COUNT
) -> list[dict[str, Any]]:
    if bucket_count <= 0:
        raise ValueError("bucket_count must be positive")

    buckets: list[list[tuple[float, bool]]] = [[] for _ in range(bucket_count)]
    for probability, outcome in pairs:
        clamped = min(max(probability, 0.0), 1.0)
        index = min(int(clamped * bucket_count), bucket_count - 1)
        buckets[index].append((clamped, outcome))

    summary = []
    for index, bucket in enumerate(buckets):
        summary.append(
            {
                "lower": index / bucket_count,
                "upper": (index + 1) / bucket_count,
                "count": len(bucket),
                "mean_forecast": (
                    sum(p for p, _ in bucket) / len(bucket) if bucket else None
                ),
                "observed_frequency": (
                    sum(1 for _, outcome in bucket if outcome) / len(bucket)
                    if bucket
                    else None
                ),
            }
        )
    return summary


def summarize(
    scored_rows: list[dict[str, Any]], bucket_count: int = DEFAULT_BUCKET_COUNT
) -> dict[str, Any]:
    model_pairs = [
        (float(row["model_probability"]), bool(row["outcome"])) for row in scored_rows
    ]
    comparable = [
        row for row in scored_rows if row["market_implied_probability"] is not None
    ]
    model_pairs_common = [
        (float(row["model_probability"]), bool(row["outcome"])) for row in comparable
    ]
    market_pairs_common = [
        (float(row["market_implied_probability"]), bool(row["outcome"]))
        for row in comparable
    ]

    model_brier_common = brier_score(model_pairs_common)
    market_brier_common = brier_score(market_pairs_common)
    skill = (
        market_brier_common - model_brier_common
        if model_brier_common is not None and market_brier_common is not None
        else None
    )

    return {
        "resolved_markets": len(scored_rows),
        "compared_markets": len(comparable),
        "model_brier": brier_score(model_pairs),
        "model_brier_compared": model_brier_common,
        "market_brier_compared": market_brier_common,
        "skill_vs_market": skill,
        "base_rate": (
            sum(1 for _, outcome in model_pairs if outcome) / len(model_pairs)
            if model_pairs
            else None
        ),
        "buckets": calibration_buckets(model_pairs, bucket_count),
    }
