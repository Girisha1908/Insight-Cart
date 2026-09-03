"""Next-purchase prediction training pipeline.

Uses historical inter-purchase intervals to predict when a customer will
next buy.  Two approaches are implemented:

1. **Statistical baseline** (always available): average inter-purchase gap
   per customer, robust and explainable.
2. **Gradient-Boosted regression** (optional): learns from features to
   predict the gap, giving slightly better accuracy when enough data exists.

The statistical baseline is the default; the ML model is trained only
when there are enough repeat customers (>= 30).

Usage (standalone)::

    cd backend
    python -m ml.training.train_next_purchase

Usage (from API / tests)::

    from ml.training.train_next_purchase import train_next_purchase_model
    result = train_next_purchase_model(db_session)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.services.ml.feature_engineering import (
    FEATURE_COLUMNS,
    FeatureEngineeringService,
    build_next_purchase_target,
)
from ml.evaluation.metrics import evaluate_classification

_MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "next_purchase"

# Features that leak the target, avg_days_to_next_purchase:
# - days_between_orders is the same inter-purchase gap being predicted.
# - customer_lifetime_days / total_orders algebraically reconstruct the mean
#   inter-purchase gap (lifetime ≈ gap × orders), and purchase_frequency is a
#   direct reciprocal of that ratio.
# Excluding them yields a generalizable model instead of R²≈1.0. Keep standard
# historical/recency features (recency, revenue, order value, etc.) that don't
# directly compute the target ratio.
_NEXT_PURCHASE_LEAKY = {
    "days_between_orders",
    "customer_lifetime_days",
    "total_orders",
    "purchase_frequency",
}
NEXT_PURCHASE_TRAINING_COLUMNS = [c for c in FEATURE_COLUMNS if c not in _NEXT_PURCHASE_LEAKY]


def train_next_purchase_model(
    db: Session,
    test_size: float = 0.2,
    save: bool = True,
) -> dict[str, Any]:
    """Train a next-purchase-interval prediction model.

    Returns
    -------
    dict with keys: model, baseline_mean, metrics, model_type, message
    """
    svc = FeatureEngineeringService(db)
    features_df, ref_date = svc.build_features(only_with_orders=False)
    orders_df = svc._load_orders()

    if orders_df.empty or features_df.empty:
        return {
            "model": None,
            "baseline_mean": None,
            "metrics": {},
            "model_type": "none",
            "message": "No order data available for training",
        }

    # Statistical baseline: mean inter-purchase gap per repeat customer.
    target_df = build_next_purchase_target(orders_df)
    baseline_mean = float(target_df["avg_days_to_next_purchase"].mean()) if not target_df.empty else None

    # ML model: only when enough data. Target is keyed by real customer
    # identity (customer_unique_id when available).
    target_key = "customer_unique_id" if "customer_unique_id" in target_df.columns else "customer_id"
    repeat_customers = target_df[target_key].nunique()

    if repeat_customers < 30 or features_df.empty:
        mean_txt = f"{baseline_mean:.1f}" if baseline_mean is not None else "N/A"
        return {
            "model": None,
            "baseline_mean": baseline_mean,
            "metrics": {},
            "model_type": "statistical_baseline",
            "message": f"Using statistical baseline (mean={mean_txt} days); "
                       f"need >= 30 repeat customers for ML model (have {repeat_customers})",
        }

    # Build ML training data — merge on the shared identity key.
    X_full = features_df.merge(target_df, on=target_key, how="inner")
    feat_cols = [c for c in NEXT_PURCHASE_TRAINING_COLUMNS if c in X_full.columns]
    X = X_full[feat_cols].values
    y = X_full["avg_days_to_next_purchase"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42,
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = GradientBoostingRegressor(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
    )
    model.fit(X_train_s, y_train)
    y_pred = model.predict(X_test_s)

    rmse = float(np.sqrt(np.mean((y_test - y_pred) ** 2)))
    mae = float(np.mean(np.abs(y_test - y_pred)))
    r2 = float(model.score(X_test_s, y_test))

    metrics = {
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "r2": round(r2, 4),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
    }

    if save:
        _MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, _MODEL_DIR / "model.joblib")
        joblib.dump(scaler, _MODEL_DIR / "scaler.joblib")
        joblib.dump(feat_cols, _MODEL_DIR / "feature_columns.joblib")
        meta = {
            "model_type": "gradient_boosted_regressor",
            "baseline_mean": baseline_mean,
            "feature_columns": feat_cols,
            "metrics": metrics,
        }
        (_MODEL_DIR / "metadata.json").write_text(json.dumps(meta, indent=2))

    return {
        "model": model,
        "baseline_mean": baseline_mean,
        "metrics": metrics,
        "model_type": "gradient_boosted_regressor",
        "message": f"ML model trained (RMSE={rmse:.1f} days, R²={r2:.4f})",
    }


def predict_next_purchase(
    db: Session,
    customer_id: str,
) -> dict[str, Any] | None:
    """Predict the next purchase date for a single customer.

    Returns ``None`` if no order data is available for this customer.
    """
    # Resolve the requested id to the unique-customer entity. The input may be
    # a transaction-level customer_id or a customer_unique_id.
    uid = db.execute(
        select(Customer.customer_unique_id).where(
            or_(Customer.customer_id == customer_id, Customer.customer_unique_id == customer_id)
        )
    ).first()
    if uid is None:
        return None
    unique_id = uid[0]

    svc = FeatureEngineeringService(db)
    features_df, ref_date = svc.build_features(only_with_orders=True)
    orders_df = svc._load_orders()

    row = features_df[features_df["customer_unique_id"] == unique_id]
    if row.empty:
        return None

    # Find the last order date across all orders of this unique customer.
    cust_orders = orders_df[orders_df["customer_unique_id"] == unique_id].dropna(subset=["order_date"])
    if cust_orders.empty:
        return None

    last_order = cust_orders["order_date"].max()
    total_orders = int(row.iloc[0].get("total_orders", 0))

    # Try ML model first.
    model_path = _MODEL_DIR / "model.joblib"
    if model_path.exists():
        model = joblib.load(_MODEL_DIR / "model.joblib")
        scaler = joblib.load(_MODEL_DIR / "scaler.joblib")
        feat_cols: list[str] = joblib.load(_MODEL_DIR / "feature_columns.joblib")

        X = row[[c for c in feat_cols if c in row.columns]].values
        X_s = scaler.transform(X)
        predicted_days = float(model.predict(X_s)[0])
        model_type = "gradient_boosted_regressor"
    else:
        # Statistical baseline.
        target_df = build_next_purchase_target(orders_df)
        target_key = "customer_unique_id" if "customer_unique_id" in target_df.columns else "customer_id"
        cust_target = target_df[target_df[target_key] == unique_id]
        if not cust_target.empty:
            predicted_days = float(cust_target.iloc[0]["avg_days_to_next_purchase"])
        elif total_orders > 1:
            # Compute from this customer's history.
            gaps = cust_orders.sort_values("order_date")["order_date"].diff().dt.days.dropna()
            predicted_days = float(gaps.mean()) if not gaps.empty else 30.0
        else:
            predicted_days = 30.0  # fallback for single-order customers
        model_type = "statistical_baseline"

    predicted_days = max(1.0, predicted_days)
    predicted_date = last_order + pd.Timedelta(days=predicted_days)

    return {
        "customer_id": customer_id,
        "last_order_date": last_order.isoformat(),
        "total_orders": total_orders,
        "predicted_days_to_next_purchase": round(predicted_days, 1),
        "predicted_next_purchase_date": predicted_date.isoformat(),
        "model_used": model_type,
        "confidence_note": (
            "Based on this customer's purchase history pattern."
            if total_orders > 1
            else "Limited history — prediction is approximate."
        ),
    }
