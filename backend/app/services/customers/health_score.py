"""Customer health score (0-100).

Health is a composite score built from three equally-weighted dimensions,
each independently normalized to 0-100 and then averaged:

    health_score = (recency_score + frequency_score + monetary_score) / 3

Each dimension uses a capped percentile rank relative to the dataset:

- **Recency (40% weight):** How recently did the customer purchase relative to
  their own history and the cohort?  Customers with recency_days = 0 score 100;
  score decays as recency increases.  Customers with no orders score 0.
- **Frequency (30% weight):** How often does this customer purchase compared
  to the median?  Above-median frequency → 100; lower frequencies scale down.
- **Monetary (30% weight):** How does this customer's average order value
  compare to the median?  Above-median AOV → 100.

Health score thresholds (human-friendly labels):
    80-100  → "Excellent"
    60-79   → "Good"
    40-59   → "Fair"
    20-39   → "Poor"
    0-19    → "Critical"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

# Weights for each dimension.
WEIGHT_RECENCY = 0.4
WEIGHT_FREQUENCY = 0.3
WEIGHT_MONETARY = 0.3

# Health band thresholds.
HEALTH_BANDS = [
    (80, "Excellent"),
    (60, "Good"),
    (40, "Fair"),
    (20, "Poor"),
    (0, "Critical"),
]


@dataclass
class HealthScoreResult:
    customer_id: str
    health_score: float  # 0-100, rounded to 1 dp
    health_label: str
    recency_score: float
    frequency_score: float
    monetary_score: float
    recency_days: Optional[int]
    total_orders: int
    avg_order_value: float


def _cap_percentile_rank(series: pd.Series, min_val: float = 1.0) -> pd.Series:
    """Cap-percentile rank: values below the minimum get 0, values at median → 50,
    values at max → 100."""
    if series.empty or series.isna().all():
        return series
    capped = series.clip(lower=min_val)
    return ((capped - capped.min()) / (capped.max() - capped.min()) * 100).fillna(0.0)


def _recency_score(recency_days: pd.Series) -> pd.Series:
    """Recency: 0 recency_days = 100; decays linearly to 0 at the 90th percentile."""
    if recency_days.empty:
        return recency_days
    # Clip at 0 and convert to float.
    r = recency_days.fillna(9999).clip(lower=0).astype(float)
    p90 = r.quantile(0.90)
    if p90 <= 0:
        return r * 0 + 100.0
    return (1 - (r / p90)).clip(0, 1) * 100


def _frequency_score(total_orders: pd.Series) -> pd.Series:
    """Frequency: customers with only 1 order → 20; above-median → 100."""
    if total_orders.empty:
        return total_orders
    orders = total_orders.fillna(0).astype(float)
    median = orders.median()
    if median <= 1:
        return (orders / max(orders.max(), 1) * 80 + 20).clip(0, 100)
    return ((orders - 1) / (orders.max() - 1) * 80 + 20).clip(0, 100)


def _monetary_score(avg_order_value: pd.Series) -> pd.Series:
    """Monetary: below median → linearly from 20→50; above median → 50→100."""
    if avg_order_value.empty:
        return avg_order_value
    aov = avg_order_value.fillna(0).astype(float)
    median = aov.median()
    if median <= 0:
        return aov * 0
    below = aov <= median
    above = ~below
    scores = pd.Series(0.0, index=aov.index)
    scores[below] = ((aov[below] / median) * 50).clip(0, 50)
    scores[above] = (50 + ((aov[above] - median) / (aov.max() - median + 1e-9) * 50)).clip(50, 100)
    return scores


def compute_health_scores(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Compute health score (0-100) per customer.

    Returns a DataFrame with columns: customer_id, health_score, health_label,
    recency_score, frequency_score, monetary_score.
    """
    df = metrics_df.copy()

    has_orders = df["total_orders"].notna() & (df["total_orders"] > 0)
    df["recency_score"] = 0.0
    df["frequency_score"] = 0.0
    df["monetary_score"] = 0.0

    scored = df[has_orders].copy()
    if not scored.empty:
        scored["recency_score"] = _recency_score(scored["recency_days"])
        scored["frequency_score"] = _frequency_score(scored["total_orders"])
        scored["monetary_score"] = _monetary_score(scored["avg_order_value"])

        scored["health_score"] = (
            scored["recency_score"] * WEIGHT_RECENCY
            + scored["frequency_score"] * WEIGHT_FREQUENCY
            + scored["monetary_score"] * WEIGHT_MONETARY
        ).round(1)

        # Label each band.
        def label(score: float) -> str:
            for threshold, name in HEALTH_BANDS:
                if score >= threshold:
                    return name
            return "Critical"

        scored["health_label"] = scored["health_score"].apply(label)
        df = scored

    else:
        df["health_score"] = 0.0
        df["health_label"] = "Critical"

    return df[
        [
            "customer_id",
            "health_score",
            "health_label",
            "recency_score",
            "frequency_score",
            "monetary_score",
            "recency_days",
            "total_orders",
            "avg_order_value",
        ]
    ]


def health_score_summary(health_df: pd.DataFrame) -> dict:
    """Return aggregate health statistics for the dataset."""
    if health_df.empty:
        return {
            "average_health_score": 0.0,
            "median_health_score": 0.0,
            "excellent_count": 0,
            "good_count": 0,
            "fair_count": 0,
            "poor_count": 0,
            "critical_count": 0,
            "total_scored": 0,
        }
    scores = health_df["health_score"]
    labels = health_df["health_label"]
    return {
        "average_health_score": round(float(scores.mean()), 1),
        "median_health_score": round(float(scores.median()), 1),
        "excellent_count": int((labels == "Excellent").sum()),
        "good_count": int((labels == "Good").sum()),
        "fair_count": int((labels == "Fair").sum()),
        "poor_count": int((labels == "Poor").sum()),
        "critical_count": int((labels == "Critical").sum()),
        "total_scored": int(len(health_df)),
    }
