"""Customer Analytics Orchestrator.

Combines all customer analytics (metrics → RFM → CLV → retention → cohorts →
health score) into a single pass over the database and returns structured
results ready for the API layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.services.customers.customer_metrics import CustomerMetricsService, MetricsContext
from app.services.customers.rfm import (
    SEGMENT_DESCRIPTIONS,
    RFMSegment,
    build_rfm_summary,
    compute_rfm,
    compute_segment_distribution,
)
from app.services.customers.clv import compute_clv, summarize_clv
from app.services.customers.retention import compute_repeat_purchase_rate, compute_retention_curve
from app.services.customers.cohorts import build_cohort_matrix, build_cohort_revenue_matrix
from app.services.customers.health_score import compute_health_scores, health_score_summary


# ---------------------------------------------------------------------------
# Pydantic-friendly result structures
# ---------------------------------------------------------------------------

@dataclass
class SegmentOverview:
    key: str
    name: str
    description: str
    customer_count: int
    avg_revenue: float
    rfm_code: str


@dataclass
class RFMOverview:
    segments: list[SegmentOverview]
    segment_distribution: dict[str, int]
    reference_date: str  # ISO-8601 string


@dataclass
class CLVOverview:
    total_customers_with_orders: int
    average_clv: float
    median_clv: float
    top_10_percent_clv: float


@dataclass
class RetentionOverview:
    repeat_purchase_rate: float
    total_customers: int
    repeat_customers: int
    average_orders_per_customer: float
    one_time_buyers: int
    active_customers: int
    retention_curve: list[dict]
    cohort_matrix: list[dict]


@dataclass
class HealthOverview:
    average_health_score: float
    median_health_score: float
    excellent_count: int
    good_count: int
    fair_count: int
    poor_count: int
    critical_count: int
    total_scored: int


@dataclass
class CustomerAnalytics:
    """All analytics for the customer domain, computed in one pass."""

    rfm: RFMOverview
    clv: CLVOverview
    retention: RetentionOverview
    health: HealthOverview
    context: dict  # raw context (reference_date, counts)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class CustomerAnalyticsService:
    """Compute all customer analytics from the canonical schema."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.metrics_svc = CustomerMetricsService(db)

    # ------------------------------------------------------------------ public

    def compute_all(self) -> CustomerAnalytics:
        """Run the full analytics pipeline and return structured results."""
        # 1. Base metrics (one DB query, shared by everything).
        metrics_df, context = self.metrics_svc.build_customer_metrics(only_with_orders=False)
        orders_df = self.metrics_svc.load_orders()

        ref_date = context.reference_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        # 2. RFM.
        rfm_df = compute_rfm(metrics_df)
        rfm_summary = build_rfm_summary(rfm_df)
        rfm_overview = RFMOverview(
            segments=[
                SegmentOverview(
                    key=s.segment_key,
                    name=s.segment_name,
                    description=s.description,
                    customer_count=s.customer_count,
                    avg_revenue=s.avg_revenue,
                    rfm_code=s.rfm_code,
                )
                for s in rfm_summary
            ],
            segment_distribution=compute_segment_distribution(rfm_df),
            reference_date=ref_date,
        )

        # 3. CLV.
        clv_df = compute_clv(metrics_df)
        clv_stats = summarize_clv(clv_df)
        clv_overview = CLVOverview(
            total_customers_with_orders=clv_stats["total_customers_with_orders"],
            average_clv=clv_stats["average_clv"],
            median_clv=clv_stats["median_clv"],
            top_10_percent_clv=clv_stats["top_10_percent_clv"],
        )

        # 4. Retention + Cohorts.
        retention_result = compute_repeat_purchase_rate(metrics_df)
        retention_df = compute_retention_curve(orders_df)
        cohort_matrix_df = build_cohort_matrix(retention_df)
        retention_overview = RetentionOverview(
            repeat_purchase_rate=retention_result.repeat_purchase_rate,
            total_customers=retention_result.total_customers,
            repeat_customers=retention_result.repeat_customers,
            average_orders_per_customer=retention_result.average_orders_per_customer,
            one_time_buyers=retention_result.one_time_buyers,
            active_customers=retention_result.active_customers,
            retention_curve=retention_df.to_dict(orient="records"),
            cohort_matrix=_matrix_to_dict(cohort_matrix_df),
        )

        # 5. Health score.
        health_df = compute_health_scores(metrics_df)
        health_stats = health_score_summary(health_df)
        health_overview = HealthOverview(
            average_health_score=health_stats["average_health_score"],
            median_health_score=health_stats["median_health_score"],
            excellent_count=health_stats["excellent_count"],
            good_count=health_stats["good_count"],
            fair_count=health_stats["fair_count"],
            poor_count=health_stats["poor_count"],
            critical_count=health_stats["critical_count"],
            total_scored=health_stats["total_scored"],
        )

        return CustomerAnalytics(
            rfm=rfm_overview,
            clv=clv_overview,
            retention=retention_overview,
            health=health_overview,
            context={
                "reference_date": ref_date,
                "total_customers": context.total_customer_count,
                "total_orders": context.total_order_count,
            },
        )

    # ---------------------------------------------------------------- single-customer

    def get_customer_analytics(self, customer_id: str) -> dict:
        """Return all analytics for one customer, enriched with CLV formula."""
        metrics_df, _ = self.metrics_svc.build_customer_metrics(only_with_orders=False)
        if metrics_df.empty:
            return {}
        rfm_df = compute_rfm(metrics_df)
        clv_df = compute_clv(metrics_df)
        health_df = compute_health_scores(metrics_df)

        customer_metrics = metrics_df[metrics_df["customer_id"] == customer_id]
        if customer_metrics.empty:
            return {}

        row = customer_metrics.iloc[0]
        rfm_row = rfm_df[rfm_df["customer_id"] == customer_id].iloc[0]
        clv_row = clv_df[clv_df["customer_id"] == customer_id].iloc[0]
        health_row = health_df[health_df["customer_id"] == customer_id].iloc[0]

        return {
            "customer_id": customer_id,
            "segment": rfm_row["segment_name"],
            "segment_key": rfm_row["segment_key"],
            "segment_description": SEGMENT_DESCRIPTIONS.get(str(rfm_row["segment_key"]), ""),
            "rfm_code": str(rfm_row["rfm_code"]),
            "recency_days": int(row["recency_days"]) if pd.notna(row["recency_days"]) else None,
            "total_orders": int(row["total_orders"]) if pd.notna(row["total_orders"]) else 0,
            "total_revenue": float(row["total_revenue"]) if pd.notna(row["total_revenue"]) else 0.0,
            "avg_order_value": float(clv_row["avg_order_value"]) if pd.notna(clv_row["avg_order_value"]) else 0.0,
            "historical_clv": float(clv_row["historical_clv"]) if pd.notna(clv_row["historical_clv"]) else 0.0,
            "annual_purchase_frequency": float(clv_row["annual_purchase_frequency"]) if pd.notna(clv_row["annual_purchase_frequency"]) else 0.0,
            "customer_lifetime_years": float(clv_row["customer_lifetime_years"]) if pd.notna(clv_row["customer_lifetime_years"]) else 0.0,
            "clv_formula": f"CLV = {float(clv_row['avg_order_value']):.2f} × {float(clv_row['annual_purchase_frequency']):.2f} × {float(clv_row['customer_lifetime_years']):.2f}",
            "health_score": float(health_row["health_score"]) if pd.notna(health_row["health_score"]) else 0.0,
            "health_label": str(health_row["health_label"]),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _matrix_to_dict(matrix: pd.DataFrame) -> list[dict]:
    """Convert a cohort matrix DataFrame to a list of dicts for JSON serialization."""
    if matrix.empty:
        return []
    matrix = matrix.reset_index()
    matrix.columns = [str(c) for c in matrix.columns]
    return matrix.to_dict(orient="records")
