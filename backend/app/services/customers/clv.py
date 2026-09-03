"""Customer Lifetime Value (CLV) — historical, transparent formula.

We use a *historical* CLV that is simple and explainable. No probabilistic
or BG/NBD models in Phase 2. The formula is documented inline so the
business user can compute it on a napkin.

    historical_clv = avg_order_value
                       x annual_purchase_frequency
                       x customer_lifetime_years

Where:
- avg_order_value = total_revenue / total_orders
- annual_purchase_frequency = total_orders / customer_lifetime_years
- customer_lifetime_years = customer_lifetime_days / 365.25

To avoid producing absurdly large numbers for one-off buyers with a 1-day
"lifetime," we cap the lifetime floor at 0.25 years (one quarter). For
customers with no orders, CLV is 0.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

MIN_LIFETIME_YEARS: float = 0.25  # floor to keep the formula stable


@dataclass
class CLVResult:
    """Per-customer CLV row."""

    customer_id: str
    avg_order_value: float
    annual_purchase_frequency: float
    customer_lifetime_years: float
    historical_clv: float
    formula: str  # human-readable formula string for transparency


def _row_formula(aov: float, freq: float, years: float) -> str:
    return f"CLV = {aov:.2f} (AOV) × {freq:.2f} (orders/yr) × {years:.2f} (years)"


def compute_clv(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Compute historical CLV per customer.

    Returns a DataFrame with columns: customer_id, avg_order_value,
    annual_purchase_frequency, customer_lifetime_years, historical_clv.
    """
    df = metrics_df.copy()

    # Only customers with order history have a CLV.
    mask = df["total_orders"].notna() & (df["total_orders"] > 0)
    df["avg_order_value"] = (df["total_revenue"] / df["total_orders"]).where(mask, 0.0)

    lifetime_years = (
        df["customer_lifetime_days"].fillna(0).clip(lower=MIN_LIFETIME_YEARS * 365.25) / 365.25
    )
    df["customer_lifetime_years"] = lifetime_years.where(mask, 0.0)
    df["annual_purchase_frequency"] = (df["total_orders"] / lifetime_years).where(mask, 0.0)

    df["historical_clv"] = (
        df["avg_order_value"] * df["annual_purchase_frequency"] * df["customer_lifetime_years"]
    ).where(mask, 0.0).round(2)

    return df[
        [
            "customer_id",
            "avg_order_value",
            "annual_purchase_frequency",
            "customer_lifetime_years",
            "historical_clv",
        ]
    ]


def summarize_clv(clv_df: pd.DataFrame) -> dict:
    """Return summary stats for the CLV dataset."""
    if clv_df.empty:
        return {
            "total_customers_with_orders": 0,
            "average_clv": 0.0,
            "median_clv": 0.0,
            "top_10_percent_clv": 0.0,
        }
    values = clv_df["historical_clv"]
    return {
        "total_customers_with_orders": int((clv_df["historical_clv"] > 0).sum()),
        "average_clv": float(round(values.mean(), 2)),
        "median_clv": float(round(values.median(), 2)),
        "top_10_percent_clv": float(
            round(values.nlargest(max(1, len(values) // 10)).mean(), 2)
        ),
    }


def explain_clv(customer_row: pd.Series) -> CLVResult:
    """Return a CLVResult with the human-readable formula for a single row."""
    aov = float(customer_row.get("avg_order_value", 0.0) or 0.0)
    freq = float(customer_row.get("annual_purchase_frequency", 0.0) or 0.0)
    years = float(customer_row.get("customer_lifetime_years", 0.0) or 0.0)
    clv = aov * freq * years
    return CLVResult(
        customer_id=str(customer_row["customer_id"]),
        avg_order_value=round(aov, 2),
        annual_purchase_frequency=round(freq, 2),
        customer_lifetime_years=round(years, 2),
        historical_clv=round(clv, 2),
        formula=_row_formula(aov, freq, years),
    )
