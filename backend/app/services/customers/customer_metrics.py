"""Base customer-level metrics.

Computes the raw Recency / Frequency / Monetary / Lifetime metrics that
RFM, CLV, retention, cohorts, and health score all depend on.

This is a pure, SQLAlchemy-only service: it returns pandas DataFrames so
the analytics layers can compose on top without re-querying the database.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.order import Order


@dataclass(frozen=True)
class MetricsContext:
    """Context passed to metric calculators.

    `reference_date` is "today" for the analysis — defaults to the latest
    order date in the dataset so the metrics are stable across re-runs.
    """

    reference_date: pd.Timestamp
    total_customer_count: int
    total_order_count: int


class CustomerMetricsService:
    """Compute base customer-level metrics from the canonical schema."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------ loaders

    def load_customers(self) -> pd.DataFrame:
        """Return a DataFrame of all customers (id, unique_id, city, state)."""
        stmt = select(
            Customer.customer_id,
            Customer.customer_unique_id,
            Customer.customer_city,
            Customer.customer_state,
        )
        return pd.DataFrame(self.db.execute(stmt).all())

    def load_orders(self) -> pd.DataFrame:
        """Return a DataFrame of orders with parsed dates and numeric values."""
        stmt = select(
            Order.order_id,
            Order.customer_id,
            Order.order_date,
            Order.order_status,
            Order.order_value,
        )
        df = pd.DataFrame(self.db.execute(stmt).all())
        if df.empty:
            return df
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce", utc=True)
        df["order_value"] = pd.to_numeric(df["order_value"], errors="coerce").fillna(0.0)
        return df

    # --------------------------------------------------------- reference date

    def _reference_date(self, orders: pd.DataFrame) -> pd.Timestamp:
        """Pick a stable reference date for the analysis.

        If orders exist, we use the latest order date in the dataset so RFM
        numbers are reproducible regardless of when the script is run.
        Otherwise we use "now" in UTC.
        """
        if not orders.empty and orders["order_date"].notna().any():
            return pd.Timestamp(orders["order_date"].max()).tz_convert("UTC")
        return pd.Timestamp(datetime.now(timezone.utc))

    # ---------------------------------------------------------- core metrics

    def build_customer_metrics(
        self, only_with_orders: bool = True
    ) -> tuple[pd.DataFrame, MetricsContext]:
        """Return one row per customer with core metrics.

        Columns: customer_id, customer_unique_id, first_order, last_order,
        total_orders, total_revenue, avg_order_value, recency_days,
        customer_lifetime_days, purchase_frequency.
        """
        customers = self.load_customers()
        orders = self.load_orders()
        ref = self._reference_date(orders)

        if customers.empty:
            return pd.DataFrame(), MetricsContext(
                reference_date=ref, total_customer_count=0, total_order_count=0
            )

        if orders.empty:
            metrics = customers.copy()
            for col in (
                "first_order",
                "last_order",
                "total_orders",
                "total_revenue",
                "avg_order_value",
                "recency_days",
                "customer_lifetime_days",
                "purchase_frequency",
            ):
                metrics[col] = pd.NA
            return metrics, MetricsContext(
                reference_date=ref,
                total_customer_count=len(customers),
                total_order_count=0,
            )

        # Drop rows without a parseable date or customer_id (orphan data).
        clean_orders = orders.dropna(subset=["order_date", "customer_id"]).copy()
        delivered_mask = clean_orders["order_status"].fillna("").str.lower().eq("delivered")
        # For revenue/monetary metrics we consider any non-cancelled order.
        # We still derive a "delivered_revenue" column for later analytics.
        clean_orders["is_delivered"] = delivered_mask
        clean_orders["is_cancelled"] = (
            clean_orders["order_status"].fillna("").str.lower().eq("canceled")
            | clean_orders["order_status"].fillna("").str.lower().eq("cancelled")
        )

        agg = (
            clean_orders.groupby("customer_id", as_index=False)
            .agg(
                first_order=("order_date", "min"),
                last_order=("order_date", "max"),
                total_orders=("order_id", "count"),
                total_revenue=("order_value", "sum"),
                avg_order_value=("order_value", "mean"),
                delivered_orders=("is_delivered", "sum"),
                cancelled_orders=("is_cancelled", "sum"),
            )
        )
        agg["delivered_revenue"] = (
            clean_orders[clean_orders["is_delivered"]]
            .groupby("customer_id")["order_value"]
            .sum()
            .reindex(agg["customer_id"])
            .fillna(0.0)
            .values
        )

        metrics = customers.merge(agg, on="customer_id", how="left")

        if only_with_orders:
            metrics = metrics[metrics["total_orders"].notna()].copy()

        # Days-based metrics are computed against the reference date.
        ref_naive = ref.tz_convert("UTC") if ref.tzinfo else ref
        last_naive = pd.to_datetime(metrics["last_order"], utc=True, errors="coerce")
        first_naive = pd.to_datetime(metrics["first_order"], utc=True, errors="coerce")
        metrics["recency_days"] = (ref_naive - last_naive).dt.days
        metrics["customer_lifetime_days"] = (last_naive - first_naive).dt.days

        # Purchase frequency = total_orders / lifetime_years (clipped at >=1 yr
        # for the formula's stability when a customer has 1-day lifetime).
        lifetime_years = (metrics["customer_lifetime_days"].fillna(0) / 365.25).clip(lower=0.25)
        metrics["purchase_frequency"] = (metrics["total_orders"].fillna(0) / lifetime_years).round(2)

        return metrics, MetricsContext(
            reference_date=ref,
            total_customer_count=len(customers),
            total_order_count=int(clean_orders["order_id"].nunique()),
        )
