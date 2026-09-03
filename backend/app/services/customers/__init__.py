"""Customer domain analytics.

Modules
-------
- ``customer_metrics``  : base recency/frequency/monetary/lifetime metrics
- ``rfm``               : RFM scoring and human-friendly segment names
- ``clv``               : historical Customer Lifetime Value
- ``retention``         : repeat-purchase rate and retention curves
- ``cohorts``           : first-purchase-month cohort analysis
- ``health_score``      : composite 0-100 customer health score
"""

from app.services.customers.clv import compute_clv, summarize_clv, explain_clv, CLVResult
from app.services.customers.cohorts import build_cohort_matrix, build_cohort_revenue_matrix
from app.services.customers.customer_metrics import (
    CustomerMetricsService,
    MetricsContext,
)
from app.services.customers.health_score import (
    compute_health_scores,
    health_score_summary,
    HealthScoreResult,
)
from app.services.customers.retention import (
    compute_repeat_purchase_rate,
    compute_retention_curve,
    RetentionResult,
)
from app.services.customers.rfm import (
    compute_rfm,
    build_rfm_summary,
    compute_segment_distribution,
    RFMScore,
    RFMSegment,
    SEGMENT_DESCRIPTIONS,
)

__all__ = [
    # Metrics
    "CustomerMetricsService",
    "MetricsContext",
    # RFM
    "compute_rfm",
    "build_rfm_summary",
    "compute_segment_distribution",
    "RFMScore",
    "RFMSegment",
    "SEGMENT_DESCRIPTIONS",
    # CLV
    "compute_clv",
    "summarize_clv",
    "explain_clv",
    "CLVResult",
    # Retention
    "compute_repeat_purchase_rate",
    "compute_retention_curve",
    "RetentionResult",
    # Cohorts
    "build_cohort_matrix",
    "build_cohort_revenue_matrix",
    # Health
    "compute_health_scores",
    "health_score_summary",
    "HealthScoreResult",
]
