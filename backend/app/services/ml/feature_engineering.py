"""ML feature engineering service.

Builds an ML-ready feature matrix from the canonical Customer + Order schema.
Designed to be called by training scripts (standalone) and by the prediction
API (with a live DB session).

Features produced
-----------------
recency_days, total_orders, total_revenue, purchase_frequency,
average_order_value, days_between_orders, discount_usage,
return_rate, category_count, customer_lifetime_days

Design notes
------------
- discount_usage, return_rate, and category_count are derived from order_items
  when available; otherwise default to 0 so the pipeline never fails.
- Churn labels are derived using a configurable recency threshold (default 90 days).
- Next-purchase target is the average inter-purchase gap for repeat customers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.order import Order

FEATURE_COLUMNS: list[str] = [
    "recency_days",
    "total_orders",
    "total_revenue",
    "purchase_frequency",
    "average_order_value",
    "days_between_orders",
    "discount_usage",
    "return_rate",
    "category_count",
    "customer_lifetime_days",
]


class FeatureEngineeringService:
    """Compute ML features from the canonical schema via a DB session."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ---------------------------------------------------------------- loaders

    def _load_customers(self) -> pd.DataFrame:
        stmt = select(
            Customer.customer_id,
            Customer.customer_unique_id,
            Customer.customer_city,
            Customer.customer_state,
        )
        return pd.DataFrame(self.db.execute(stmt).all())

    def _load_orders(self) -> pd.DataFrame:
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

    def _load_order_items(self) -> pd.DataFrame:
        """Load order items if the table exists, otherwise return empty."""
        try:
            from app.models.order_item import OrderItem  # type: ignore[import-untyped]

            stmt = select(
                OrderItem.order_id,
                OrderItem.product_id,
                OrderItem.quantity,
                OrderItem.unit_price,
                OrderItem.discount,  # type: ignore[attr-defined]
            )
            return pd.DataFrame(self.db.execute(stmt).all())
        except (ImportError, Exception):
            return pd.DataFrame()

    # ---------------------------------------------------------------- reference

    def _reference_date(self, orders: pd.DataFrame) -> pd.Timestamp:
        if not orders.empty and orders["order_date"].notna().any():
            return pd.Timestamp(orders["order_date"].max()).tz_convert("UTC")
        return pd.Timestamp(datetime.now(timezone.utc))

    # ---------------------------------------------------------------- features

    def build_features(
        self,
        only_with_orders: bool = True,
    ) -> tuple[pd.DataFrame, pd.Timestamp]:
        """Return one row per customer with all ML features.

        Returns
        -------
        (features_df, reference_date)
            features_df has ``customer_id`` plus every column in ``FEATURE_COLUMNS``.
        """
        customers = self._load_customers()
        orders = self._load_orders()
        ref = self._reference_date(orders)

        if customers.empty:
            return pd.DataFrame(columns=["customer_id", *FEATURE_COLUMNS]), ref

        if orders.empty:
            feats = customers[["customer_id"]].copy()
            for col in FEATURE_COLUMNS:
                feats[col] = 0.0
            return feats, ref

        clean = orders.dropna(subset=["order_date", "customer_id"]).copy()

        # ---- core aggregation per customer ----
        agg = (
            clean.groupby("customer_id", as_index=False)
            .agg(
                first_order=("order_date", "min"),
                last_order=("order_date", "max"),
                total_orders=("order_id", "count"),
                total_revenue=("order_value", "sum"),
                average_order_value=("order_value", "mean"),
            )
        )

        ref_naive = ref.tz_convert("UTC") if ref.tzinfo else ref
        last = pd.to_datetime(agg["last_order"], utc=True, errors="coerce")
        first = pd.to_datetime(agg["first_order"], utc=True, errors="coerce")

        agg["recency_days"] = (ref_naive - last).dt.days.astype(float)
        agg["customer_lifetime_days"] = (last - first).dt.days.clip(lower=0).astype(float)

        lifetime_years = (agg["customer_lifetime_days"] / 365.25).clip(lower=0.25)
        agg["purchase_frequency"] = (agg["total_orders"] / lifetime_years).round(2)

        # ---- average days between consecutive orders ----
        gap = clean.sort_values(["customer_id", "order_date"])
        gap["prev"] = gap.groupby("customer_id")["order_date"].shift(1)
        gap["gap_days"] = (gap["order_date"] - gap["prev"]).dt.days
        avg_gap = (
            gap.dropna(subset=["gap_days"])
            .groupby("customer_id")["gap_days"]
            .mean()
            .rename("days_between_orders")
        )
        agg = agg.merge(avg_gap, on="customer_id", how="left")

        # ---- optional product features from order_items ----
        items = self._load_order_items()
        if not items.empty:
            prod = (
                items.groupby("order_id", as_index=False)
                .agg(
                    product_count=("product_id", "nunique"),
                    total_discount=("discount", "sum"),
                    total_item_value=("unit_price", "sum"),
                )
            )
            order_prod = clean[["order_id", "customer_id"]].merge(prod, on="order_id", how="left")
            cust_prod = order_prod.groupby("customer_id", as_index=False).agg(
                category_count=("product_count", "sum"),
                total_discount=("total_discount", "sum"),
                total_item_value=("total_item_value", "sum"),
            )
            cust_prod["discount_usage"] = (
                cust_prod["total_discount"] / cust_prod["total_item_value"].clip(lower=1e-9)
            ).fillna(0.0)
            cust_prod["return_rate"] = 0.0  # no explicit return data
            agg = agg.merge(
                cust_prod[["customer_id", "category_count", "discount_usage", "return_rate"]],
                on="customer_id",
                how="left",
            )

        # ---- merge with customers and fill defaults ----
        feats = customers[["customer_id"]].merge(
            agg[
                [
                    "customer_id",
                    "recency_days",
                    "total_orders",
                    "total_revenue",
                    "purchase_frequency",
                    "average_order_value",
                    "days_between_orders",
                    "customer_lifetime_days",
                ]
                + (["category_count", "discount_usage", "return_rate"]
                   if "category_count" in agg.columns else [])
            ],
            on="customer_id",
            how="left",
        )

        if only_with_orders:
            feats = feats[feats["total_orders"].notna()].copy()

        for col in FEATURE_COLUMNS:
            if col not in feats.columns:
                feats[col] = 0.0
            feats[col] = feats[col].fillna(0.0)

        return feats, ref


# ---------------------------------------------------------------------------
# Standalone helpers (no DB session required — accept DataFrames directly)
# ---------------------------------------------------------------------------

def build_churn_label(
    orders_df: pd.DataFrame,
    reference_date: pd.Timestamp,
    churn_days: int = 90,
) -> pd.DataFrame:
    """Derive churn labels from raw order data.

    Accepts either:
    - a raw orders DataFrame (with ``customer_id`` + ``order_date``), or
    - a pre-aggregated customer DataFrame (with ``customer_id`` + ``last_order``).

    Returns a DataFrame with ``customer_id`` and ``churned`` (1 = churned, 0 = active).
    A customer is labelled *churned* when they have no orders within
    ``churn_days`` of the reference date, or have no orders at all.
    """
    ref = reference_date.tz_convert("UTC") if reference_date.tzinfo else reference_date

    if "last_order" in orders_df.columns:
        # Pre-aggregated: already has customer-level last_order.
        df = orders_df[["customer_id", "last_order"]].copy()
    elif "order_date" in orders_df.columns:
        # Raw orders: aggregate to get last order per customer.
        clean = orders_df.dropna(subset=["customer_id", "order_date"]).copy()
        df = (
            clean.groupby("customer_id", as_index=False)["order_date"]
            .max()
            .rename(columns={"order_date": "last_order"})
        )
    else:
        return pd.DataFrame(columns=["customer_id", "churned"])

    last = pd.to_datetime(df["last_order"], utc=True, errors="coerce")
    recency = (ref - last).dt.days
    df["churned"] = ((recency > churn_days) | recency.isna()).astype(int)
    return df[["customer_id", "churned"]]


def build_feature_matrix(
    features_df: pd.DataFrame,
    labels_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return a clean feature matrix ready for model training.

    If *labels_df* is provided (must contain ``customer_id`` and ``churned``),
    it is merged in so the caller can do a train/test split directly.
    """
    feat_cols = [c for c in FEATURE_COLUMNS if c in features_df.columns]
    X = features_df[["customer_id"] + feat_cols].copy()

    if labels_df is not None and "churned" in labels_df.columns:
        X = X.merge(labels_df[["customer_id", "churned"]], on="customer_id", how="inner")

    return X


def build_next_purchase_target(
    orders_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute ``avg_days_to_next_purchase`` per customer.

    Only customers with 2+ orders receive a value; others get NaN (excluded
    from training).
    """
    if orders_df.empty or orders_df["order_date"].isna().all():
        return pd.DataFrame(columns=["customer_id", "avg_days_to_next_purchase"])

    df = orders_df.dropna(subset=["order_date", "customer_id"]).copy()
    df = df.sort_values(["customer_id", "order_date"])

    df["next_order"] = df.groupby("customer_id")["order_date"].shift(-1)
    df["days_to_next"] = (df["next_order"] - df["order_date"]).dt.days

    result = (
        df.dropna(subset=["days_to_next"])
        .groupby("customer_id")["days_to_next"]
        .mean()
        .reset_index()
        .rename(columns={"days_to_next": "avg_days_to_next_purchase"})
    )
    return result
