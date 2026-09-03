"""Cross-domain analytics orchestrators.

Modules
-------
- ``customer_analytics`` : aggregates RFM, CLV, retention, cohorts and health
                            score into a single computed object.
"""

from app.services.analytics.customer_analytics import (
    CustomerAnalyticsService,
    CustomerAnalytics,
    RFMOverview,
    SegmentOverview,
    CLVOverview,
    RetentionOverview,
    HealthOverview,
)

__all__ = [
    "CustomerAnalyticsService",
    "CustomerAnalytics",
    "RFMOverview",
    "SegmentOverview",
    "CLVOverview",
    "RetentionOverview",
    "HealthOverview",
]
