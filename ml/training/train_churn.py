"""Churn model training pipeline.

Trains Logistic Regression, Random Forest, and XGBoost classifiers on
customer features, evaluates each, saves the best model to
``ml/models/churn/`` via Joblib, and returns metrics for the ML API.

Usage (standalone)::

    cd backend
    python -m ml.training.train_churn

Usage (from API / tests)::

    from ml.training.train_churn import train_churn_models
    result = train_churn_models(db_session)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.services.ml.feature_engineering import (
    FEATURE_COLUMNS,
    FeatureEngineeringService,
    build_churn_label,
    build_feature_matrix,
)
from ml.evaluation.metrics import evaluate_classification, select_best_model

# Where the best model and metadata are saved.
_MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "churn"

# recency_days deterministically encodes the churn label (label = last order
# older than churn_days), so it leaks the target into training and yields
# artificially perfect metrics. Exclude it from the trained model.
CHURN_TRAINING_COLUMNS = [c for c in FEATURE_COLUMNS if c != "recency_days"]


def _get_models() -> dict[str, Any]:
    """Return fresh, untrained model instances."""
    return {
        "logistic_regression": LogisticRegression(
            max_iter=1000,
            random_state=42,
            class_weight="balanced",
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight="balanced",
            n_jobs=-1,
        ),
        "xgboost": _get_xgboost(random_state=42),
    }


def _get_xgboost(**kwargs: Any) -> Any:
    try:
        from xgboost import XGBClassifier

        return XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            scale_pos_weight=1,
            eval_metric="logloss",
            **kwargs,
        )
    except ImportError:
        from sklearn.ensemble import GradientBoostingClassifier

        return GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=kwargs.get("random_state", 42),
        )


def train_churn_models(
    db: Session,
    test_size: float = 0.2,
    churn_days: int = 90,
    save: bool = True,
) -> dict[str, Any]:
    """Train churn models and optionally save the best one.

    Parameters
    ----------
    db : SQLAlchemy session
    test_size : fraction of data for the test set
    churn_days : recency threshold (days) for churn labelling
    save : whether to persist the best model to disk

    Returns
    -------
    dict with keys: models, metrics, best_model, features, labels
    """
    # 1. Build features and labels.
    svc = FeatureEngineeringService(db)
    features_df, ref_date = svc.build_features(only_with_orders=True)
    orders_df = svc._load_orders()

    if features_df.empty or len(features_df) < 10:
        return {
            "models": {},
            "metrics": {},
            "best_model": None,
            "features": features_df,
            "labels": pd.DataFrame(),
            "message": "Insufficient data for training (need >= 10 customers with orders)",
        }

    labels_df = build_churn_label(orders_df, ref_date, churn_days=churn_days)
    # Labels are keyed by the same identity as the feature matrix
    # (customer_unique_id when available, else customer_id).
    label_key = "customer_unique_id" if "customer_unique_id" in labels_df.columns else "customer_id"
    labels_df = labels_df[[label_key, "churned"]]

    X_full = build_feature_matrix(features_df, labels_df)
    feat_cols = [c for c in CHURN_TRAINING_COLUMNS if c in X_full.columns]
    X = X_full[feat_cols].values
    y = X_full["churned"].values

    # 2. Train/test split.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y if len(np.unique(y)) > 1 else None,
    )

    # 3. Scale features.
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # 4. Train all models.
    candidates = _get_models()
    trained_models: dict[str, Any] = {}
    model_metrics: dict[str, dict[str, Any]] = {}

    for name, model in candidates.items():
        model.fit(X_train_s, y_train)
        y_prob = model.predict_proba(X_test_s)[:, 1]
        metrics = evaluate_classification(y_test, y_prob)
        trained_models[name] = model
        model_metrics[name] = metrics

    # 5. Select and save best.
    best_name = select_best_model(model_metrics)
    best_model = trained_models[best_name]

    if save:
        _MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(best_model, _MODEL_DIR / "model.joblib")
        joblib.dump(scaler, _MODEL_DIR / "scaler.joblib")
        joblib.dump(feat_cols, _MODEL_DIR / "feature_columns.joblib")
        meta = {
            "best_model": best_name,
            "churn_days": churn_days,
            "reference_date": ref_date.isoformat(),
            "feature_columns": feat_cols,
            "metrics": model_metrics,
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
        }
        (_MODEL_DIR / "metadata.json").write_text(json.dumps(meta, indent=2))

    return {
        "models": trained_models,
        "metrics": model_metrics,
        "best_model": best_name,
        "features": features_df,
        "labels": labels_df,
    }


def predict_churn(
    db: Session,
    customer_id: str,
) -> dict[str, Any] | None:
    """Predict churn for a single customer using the saved model.

    Returns a dict with ``churn_probability``, ``churn_label``,
    ``risk_level``, and a human-friendly ``summary`` — or ``None`` if
    the model is not available.
    """
    model_path = _MODEL_DIR / "model.joblib"
    scaler_path = _MODEL_DIR / "scaler.joblib"
    feat_path = _MODEL_DIR / "feature_columns.joblib"
    meta_path = _MODEL_DIR / "metadata.json"

    if not all(p.exists() for p in [model_path, scaler_path, feat_path, meta_path]):
        return None

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    feat_cols: list[str] = joblib.load(feat_path)
    meta = json.loads(meta_path.read_text())

    # Resolve the requested id to the unique-customer feature row. The input
    # may be a transaction-level customer_id or a customer_unique_id.
    uid = db.execute(
        select(Customer.customer_unique_id).where(
            or_(Customer.customer_id == customer_id, Customer.customer_unique_id == customer_id)
        )
    ).first()
    if uid is None:
        return None

    svc = FeatureEngineeringService(db)
    features_df, _ = svc.build_features(only_with_orders=True)
    row = features_df[features_df["customer_unique_id"] == uid[0]]
    if row.empty:
        return None

    X = row[[c for c in feat_cols if c in row.columns]].values
    X_s = scaler.transform(X)
    prob = float(model.predict_proba(X_s)[:, 1][0])
    churned = bool(model.predict(X_s)[0])

    risk_level, summary = _churn_summary(prob)
    action = _recommended_action(prob, row.iloc[0])

    return {
        "customer_id": customer_id,
        "churn_probability": round(prob, 4),
        "churned": churned,
        "risk_level": risk_level,
        "summary": summary,
        "recommended_action": action,
        "model_used": meta.get("best_model", "unknown"),
        "features_used": feat_cols,
    }


def _churn_summary(prob: float) -> tuple[str, str]:
    """Map churn probability to a human-friendly risk level and summary."""
    if prob >= 0.75:
        return "High risk", f"High risk — {prob:.0%} likelihood of churn"
    if prob >= 0.50:
        return "Medium risk", f"Elevated risk — {prob:.0%} likelihood of churn"
    if prob >= 0.25:
        return "Low risk", f"Low risk — {prob:.0%} likelihood of churn"
    return "Very low risk", f"Very low risk — {prob:.0%} likelihood of churn"


def _recommended_action(prob: float, row: pd.Series) -> str:
    """Suggest a non-causal retention action based on risk level."""
    recency = row.get("recency_days", 0)
    orders = row.get("total_orders", 0)

    if prob >= 0.75:
        if recency and recency > 180:
            return "Urgent: reach out with a personalized win-back offer."
        return "Consider a targeted retention offer to re-engage."
    if prob >= 0.50:
        if orders and orders >= 3:
            return "Reward loyalty to reinforce continued engagement."
        return "Consider a small incentive to encourage a return visit."
    if prob >= 0.25:
        return "Maintain engagement through regular updates and value-adds."
    return "Keep up current engagement strategy — this customer is healthy."
