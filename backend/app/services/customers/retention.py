"""Retention and repeat-purchase analytics.

Repeat purchase rate = (# customers with ≥2 orders) / (total customers).
Retention = the fraction of customers from period T who are still active
in period T+1, T+2, ...

We use a simple monthly grain because the Olist dataset's order dates are
spread over a multi-year window.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class RetentionResult:
    """Headline retention numbers."""

    repeat_purchase_rate: float  # 0..1
    total_customers: int
    repeat_customers: int
    average_orders_per_customer: float
    average_repeat_orders_per_repeat_customer: float
    one_time_buyers: int
    active_customers: int  # customers with ≥1 order in the last 90 days (relative to ref)


def compute_repeat_purchase_rate(metrics_df: pd.DataFrame) -> RetentionResult:
    """Compute repeat-purchase metrics from a customer-metrics DataFrame.

    The DataFrame must contain ``customer_id`` and ``total_orders`` columns.
    """
    if metrics_df.empty or metrics_df["total_orders"].isna().all():
        return RetentionResult(
            repeat_purchase_rate=0.0,
            total_customers=0,
            repeat_customers=0,
            average_orders_per_customer=0.0,
            average_repeat_orders_per_repeat_customer=0.0,
            one_time_buyers=0,
            active_customers=0,
        )

    orders = metrics_df["total_orders"].fillna(0)
    total_customers = int(len(metrics_df))
    repeat_customers = int((orders >= 2).sum())
    one_time_buyers = int((orders == 1).sum())
    average_orders = float(round(orders.mean(), 2))
    average_repeat = (
        float(round(orders[orders >= 2].mean(), 2)) if repeat_customers > 0 else 0.0
    )
    rate = (repeat_customers / total_customers) if total_customers > 0 else 0.0

    # Active = recency_days <= 90
    if "recency_days" in metrics_df.columns:
        recency = pd.to_numeric(metrics_df["recency_days"], errors="coerce").fillna(9999)
        active = int((recency <= 90).sum())
    else:
        active = 0

    return RetentionResult(
        repeat_purchase_rate=round(rate, 4),
        total_customers=total_customers,
        repeat_customers=repeat_customers,
        average_orders_per_customer=average_orders,
        average_repeat_orders_per_repeat_customer=average_repeat,
        one_time_buyers=one_time_buyers,
        active_customers=active,
    )


def compute_retention_curve(orders_df: pd.DataFrame) -> pd.DataFrame:
    """Build a cohort-style retention curve per customer.

    The output is a DataFrame with columns: ``cohort_month``,
    ``month_offset``, ``active_customers``, ``cohort_size``, ``retention``.

    For each customer's first-purchase month (cohort), we count how many
    of those customers are active in each subsequent month offset (0, 1, 2, ...).
    """
    if orders_df.empty or orders_df["order_date"].isna().all():
        return pd.DataFrame(
            columns=[
                "cohort_month",
                "month_offset",
                "active_customers",
                "cohort_size",
                "retention",
            ]
        )

    df = orders_df.dropna(subset=["order_date", "customer_id"]).copy()
    df["order_month"] = df["order_date"].dt.tz_convert(None).dt.to_period("M").astype(str)

    first = df.groupby("customer_id")["order_month"].min().rename("cohort_month")
    df = df.merge(first, on="customer_id", how="left")

    # Compute month offset (integer) between cohort_month and order_month.
    df["cohort_dt"] = pd.to_datetime(df["cohort_month"] + "-01", utc=True)
    df["order_dt"] = pd.to_datetime(df["order_month"] + "-01", utc=True)
    df["month_offset"] = (
        (df["order_dt"].dt.year - df["cohort_dt"].dt.year) * 12
        + (df["order_dt"].dt.month - df["cohort_dt"].dt.month)
    )

    cohort_sizes = df.groupby("cohort_month")["customer_id"].nunique()
    active = (
        df.groupby(["cohort_month", "month_offset"])["customer_id"].nunique().reset_index()
        .rename(columns={"customer_id": "active_customers"})
    )
    active["cohort_size"] = active["cohort_month"].map(cohort_sizes)
    active["retention"] = (active["active_customers"] / active["cohort_size"]).round(4)
    return active.sort_values(["cohort_month", "month_offset"]).reset_index(drop=True)
