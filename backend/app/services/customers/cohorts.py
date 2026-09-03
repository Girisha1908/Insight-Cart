"""First-purchase-month cohort analysis.

A cohort = all customers whose first order fell in a given calendar month.
The cohort retention matrix has months (M0, M1, M2, ...) as columns and
cohort months as rows. Each cell is the fraction of the cohort still
active in that offset month.

This complements the retention-curve in ``retention.py`` with a pivoted
table view that the API can return directly to the frontend.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd


def build_cohort_matrix(retention_curve: pd.DataFrame) -> pd.DataFrame:
    """Pivot the retention curve into a cohort × month-offset matrix.

    Parameters
    ----------
    retention_curve : DataFrame
        Output of :func:`app.services.customers.retention.compute_retention_curve`.
    """
    if retention_curve.empty:
        return pd.DataFrame()

    matrix = retention_curve.pivot_table(
        index="cohort_month",
        columns="month_offset",
        values="retention",
        aggfunc="first",
    )
    # Add cohort size as a leading column.
    cohort_size = retention_curve.drop_duplicates("cohort_month").set_index("cohort_month")["cohort_size"]
    matrix.insert(0, "cohort_size", cohort_size)
    return matrix.fillna(0.0).round(4)


def build_cohort_revenue_matrix(orders_df: pd.DataFrame) -> pd.DataFrame:
    """Revenue contribution per cohort × month-offset.

    Useful for understanding which cohorts continue to spend and which taper
    off after their first month.
    """
    if orders_df.empty or orders_df["order_date"].isna().all():
        return pd.DataFrame()

    df = orders_df.dropna(subset=["order_date", "customer_id"]).copy()
    df["order_month"] = df["order_date"].dt.tz_convert("UTC").dt.to_period("M").astype(str)
    first = df.groupby("customer_id")["order_month"].min().rename("cohort_month")
    df = df.merge(first, on="customer_id", how="left")

    df["cohort_dt"] = pd.to_datetime(df["cohort_month"] + "-01", utc=True)
    df["order_dt"] = pd.to_datetime(df["order_month"] + "-01", utc=True)
    df["month_offset"] = (
        (df["order_dt"].dt.year - df["cohort_dt"].dt.year) * 12
        + (df["order_dt"].dt.month - df["cohort_dt"].dt.month)
    )

    rev_matrix = df.pivot_table(
        index="cohort_month",
        columns="month_offset",
        values="order_value",
        aggfunc="sum",
    ).fillna(0.0).round(2)
    return rev_matrix
