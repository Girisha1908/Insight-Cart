"""RFM (Recency, Frequency, Monetary) segmentation.

Each customer receives a Recency score (1-5), Frequency score (1-5), and
Monetary score (1-5).  The triplet (R, F, M) maps to a human-friendly
segment name following the standard RFM taxonomy.

The segment mapping is intentionally explainable — a business user can
understand "At Risk" without knowing what an RFM score is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from app.services.customers.customer_metrics import CustomerMetricsService


# ---------------------------------------------------------------------------
# Segment catalogue
# ---------------------------------------------------------------------------

# Keys are lowercase to match segment_key values produced by _map_rfm_to_segment.
SEGMENT_DESCRIPTIONS: dict[str, str] = {
    "champions": "Your best customers — recent, frequent, and high spenders. Keep them happy.",
    "loyal_customers": "Loyal buyers who spend well. Reward them for their loyalty.",
    "potential_loyalist": "Recent customers with decent spending. Convert them into Loyal Customers.",
    "new_customer": "Just made their first purchase. Nurture them for future repeat business.",
    "promising": "Showing early signs of engagement but not yet frequent buyers. Re-engage them.",
    "at_risk": "Were good customers but haven't purchased recently. Win them back now.",
    "cannot_lose_them": "High-value customers who haven't purchased in a long time. Urgent win-back needed.",
    "hibernating": "Last purchase was a long time ago and low spend. Low priority unless reactivation is cheap.",
    "lost": "Very long time no purchase, low frequency, low spend. Minimal investment unless part of a campaign.",
    "no_orders": "Customer has no order history yet.",
}


@dataclass
class RFMScore:
    """Individual R, F, M component score (1-5)."""

    recency: int  # 5 = most recent, 1 = least recent
    frequency: int  # 5 = most frequent, 1 = least frequent
    monetary: int  # 5 = highest spend, 1 = lowest spend


@dataclass
class RFMSegment:
    """RFM segment with human-friendly metadata."""

    segment_key: str  # e.g. "at_risk"
    segment_name: str  # e.g. "At Risk"
    description: str
    rfm_score: RFMScore
    rfm_code: str  # e.g. "352"
    customer_count: int = 0
    avg_revenue: float = 0.0


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _quintile_score(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """Assign a 1-5 score based on quintile (20th-percentile) boundaries.

    - Recency: lower recency_days is *better* → higher_is_better=False.
    - Frequency / Monetary: higher values are *better* → higher_is_better=True.

    NaN values (customers with no orders) receive score 0 and are excluded from
    segments.
    """
    labels = [1, 2, 3, 4, 5]
    if higher_is_better:
        return pd.cut(series, bins=5, labels=labels, include_lowest=True).astype(float)
    # For recency, invert: lowest days → highest score
    scores = pd.cut(series, bins=5, labels=list(reversed(labels)), include_lowest=True).astype(float)
    return scores


# ---------------------------------------------------------------------------
# Segment mapping
# ---------------------------------------------------------------------------

def _map_rfm_to_segment(r: int, f: int, m: int) -> str:
    """Map (R, F, M) integer scores to a segment key."""
    if r >= 4 and f >= 4 and m >= 4:
        return "champions"
    if f >= 4 and m >= 4:
        return "loyal_customers"
    if r >= 4 and f <= 2 and m <= 2:
        return "new_customer"
    if 3 <= r <= 4 and 2 <= f <= 4 and 2 <= m <= 4:
        return "potential_loyalist"
    if r <= 2 and f >= 3 and m >= 3:
        return "cannot_lose_them"
    if r <= 2 and f >= 3:
        return "at_risk"
    if r <= 2 and f <= 2 and m <= 2:
        return "hibernating"
    if 2 <= r <= 3 and 2 <= f <= 3 and 2 <= m <= 3:
        return "promising"
    return "hibernating"


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def compute_rfm(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-customer RFM scores and segment names.

    Parameters
    ----------
    metrics_df : DataFrame
        Must contain at minimum: ``customer_id``, ``recency_days``,
        ``total_orders``, ``total_revenue``.

    Returns
    -------
    DataFrame
        Adds columns: ``r_score``, ``f_score``, ``m_score``, ``rfm_code``,
        ``segment_key``, ``segment_name``.
    """
    df = metrics_df.copy()

    # Only score customers with order history.
    has_orders = df["recency_days"].notna()
    scored = df[has_orders].copy()
    not_scored = df[~has_orders].copy()

    # Quintile scoring (1-5). Guard against empty DataFrame and a constant
    # series (e.g. all customers share the same recency), where pd.cut fails.
    if scored.empty:
        scored["r_score"] = []
        scored["f_score"] = []
        scored["m_score"] = []
        scored["rfm_code"] = []
        scored["segment_key"] = []
        scored["segment_name"] = []
    else:
        try:
            scored["r_score"] = _quintile_score(
                scored["recency_days"], higher_is_better=False
            ).fillna(0).astype(int)
        except ValueError:
            # Constant series (e.g. all customers purchased today) → all 5s
            scored["r_score"] = 5
        try:
            scored["f_score"] = _quintile_score(
                scored["total_orders"].fillna(0), higher_is_better=True
            ).fillna(0).astype(int)
        except ValueError:
            scored["f_score"] = 5
        try:
            scored["m_score"] = _quintile_score(
                scored["total_revenue"].fillna(0), higher_is_better=True
            ).fillna(0).astype(int)
        except ValueError:
            scored["m_score"] = 5

        scored["rfm_code"] = (
            scored["r_score"].astype(str)
            + scored["f_score"].astype(str)
            + scored["m_score"].astype(str)
        )

        scored["segment_key"] = scored.apply(
            lambda row: _map_rfm_to_segment(
                int(row["r_score"]), int(row["f_score"]), int(row["m_score"])
            ),
            axis=1,
        )
        scored["segment_name"] = scored["segment_key"].str.replace("_", " ").str.title()

    # Not-scored customers get a special segment.
    if not not_scored.empty:
        not_scored["r_score"] = 0
        not_scored["f_score"] = 0
        not_scored["m_score"] = 0
        not_scored["rfm_code"] = "000"
        not_scored["segment_key"] = "no_orders"
        not_scored["segment_name"] = "No Orders"

    return pd.concat([scored, not_scored], ignore_index=True)


def build_rfm_summary(df: pd.DataFrame) -> list[RFMSegment]:
    """Build a list of RFMSegment objects, one per distinct segment.

    Used by the API endpoint to return a human-readable overview without
    enumerating every customer.
    """
    segments = (
        df.groupby(["segment_key", "segment_name"], as_index=False)
        .agg(
            customer_count=("customer_id", "count"),
            avg_revenue=("total_revenue", "mean"),
            avg_recency=("recency_days", "mean"),
            avg_frequency=("total_orders", "mean"),
            r_score=("r_score", "mean"),
            f_score=("f_score", "mean"),
            m_score=("m_score", "mean"),
        )
        .sort_values("customer_count", ascending=False)
    )

    results: list[RFMSegment] = []
    for _, row in segments.iterrows():
        results.append(
            RFMSegment(
                segment_key=str(row["segment_key"]),
                segment_name=str(row["segment_name"]),
                description=SEGMENT_DESCRIPTIONS.get(
                    str(row["segment_key"]),
                    "Segment description not available.",
                ),
                rfm_score=RFMScore(
                    recency=int(round(row["r_score"])),
                    frequency=int(round(row["f_score"])),
                    monetary=int(round(row["m_score"])),
                ),
                rfm_code=f"{int(round(row['r_score']))}{int(round(row['f_score']))}{int(round(row['m_score']))}",
                customer_count=int(row["customer_count"]),
                avg_revenue=float(round(row["avg_revenue"], 2)),
            )
        )
    return results


def compute_segment_distribution(df: pd.DataFrame) -> dict[str, int]:
    """Return a {segment_name: customer_count} dictionary."""
    return df.groupby("segment_key")["customer_id"].count().to_dict()
