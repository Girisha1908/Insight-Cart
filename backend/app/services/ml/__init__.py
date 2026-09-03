"""ML feature engineering and prediction services.

Modules
-------
- ``feature_engineering`` : builds ML-ready feature matrices from canonical schema
"""

from app.services.ml.feature_engineering import (
    FeatureEngineeringService,
    FEATURE_COLUMNS,
    build_churn_label,
    build_feature_matrix,
    build_next_purchase_target,
)

__all__ = [
    "FeatureEngineeringService",
    "FEATURE_COLUMNS",
    "build_churn_label",
    "build_feature_matrix",
    "build_next_purchase_target",
]
