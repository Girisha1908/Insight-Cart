"""ML / model domain API.

Endpoints for churn summary, model metrics, and model training.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db

router = APIRouter()

# Paths are relative to the repo root — ml/ lives at the top level
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_MODEL_DIR = _REPO_ROOT / "ml" / "models" / "churn"
_NEXT_MODEL_DIR = _REPO_ROOT / "ml" / "models" / "next_purchase"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_churn_metadata() -> dict | None:
    meta_path = _MODEL_DIR / "metadata.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text())
    return None


def _load_next_purchase_metadata() -> dict | None:
    meta_path = _NEXT_MODEL_DIR / "metadata.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text())
    return None


# ---------------------------------------------------------------------------
# 1. Churn summary
# ---------------------------------------------------------------------------

@router.get(
    "/churn/summary",
    summary="Churn model summary and distribution",
)
def get_churn_summary(db: Session = Depends(get_db)) -> dict:
    """Return churn prediction distribution across all customers.

    If the model has not been trained yet, trains on demand.
    """
    meta = _load_churn_metadata()
    if meta is None:
        # Train on demand.
        from ml.training.train_churn import train_churn_models

        result = train_churn_models(db, save=True)
        if not result["metrics"]:
            return {
                "status": "not_ready",
                "message": result.get("message", "Could not train churn models"),
            }
        meta = json.loads((_MODEL_DIR / "metadata.json").read_text())

    from app.services.ml.feature_engineering import FeatureEngineeringService
    from ml.training.train_churn import predict_churn

    svc = FeatureEngineeringService(db)
    features_df, _ = svc.build_features(only_with_orders=True)

    # Predict for all unique customers.
    predictions = []
    for cid in features_df["customer_unique_id"]:
        pred = predict_churn(db, cid)
        if pred:
            predictions.append(pred)

    if not predictions:
        return {"status": "not_ready", "message": "No predictions available"}

    probs = [p["churn_probability"] for p in predictions]
    risk_counts = {"High risk": 0, "Medium risk": 0, "Low risk": 0, "Very low risk": 0}
    for p in predictions:
        risk_counts[p["risk_level"]] = risk_counts.get(p["risk_level"], 0) + 1

    return {
        "status": "ready",
        "model_name": meta.get("best_model", "unknown"),
        "total_customers_scored": len(predictions),
        "average_churn_probability": round(sum(probs) / len(probs), 4),
        "risk_distribution": risk_counts,
        "reference_date": meta.get("reference_date"),
        "churn_days_threshold": meta.get("churn_days"),
        "model_metrics": meta.get("metrics", {}).get(meta.get("best_model", ""), {}),
    }


# ---------------------------------------------------------------------------
# 2. Model metrics
# ---------------------------------------------------------------------------

@router.get(
    "/model/metrics",
    summary="ML model evaluation metrics",
)
def get_model_metrics() -> dict:
    """Return evaluation metrics for trained models."""
    churn_meta = _load_churn_metadata()
    next_meta = _load_next_purchase_metadata()

    result: dict = {"churn": {}, "next_purchase": {}}

    if churn_meta:
        result["churn"] = {
            "best_model": churn_meta.get("best_model"),
            "train_samples": churn_meta.get("train_samples"),
            "test_samples": churn_meta.get("test_samples"),
            "churn_days": churn_meta.get("churn_days"),
            "models_evaluated": list(churn_meta.get("metrics", {}).keys()),
            "metrics": churn_meta.get("metrics", {}),
        }
    else:
        result["churn"] = {"status": "not_trained"}

    if next_meta:
        result["next_purchase"] = {
            "model_type": next_meta.get("model_type"),
            "baseline_mean": next_meta.get("baseline_mean"),
            "metrics": next_meta.get("metrics", {}),
        }
    else:
        result["next_purchase"] = {"status": "not_trained"}

    return result


# ---------------------------------------------------------------------------
# 3. Training trigger
# ---------------------------------------------------------------------------

@router.post(
    "/train",
    summary="Trigger model training",
)
def train_models(
    db: Session = Depends(get_db),
    churn_days: int = Query(90, description="Churn threshold in days"),
) -> dict:
    """Train churn and next-purchase models. Can be called on demand."""
    from ml.training.train_churn import train_churn_models
    from ml.training.train_next_purchase import train_next_purchase_model

    churn_result = train_churn_models(db, churn_days=churn_days, save=True)
    next_result = train_next_purchase_model(db, save=True)

    return {
        "churn": {
            "best_model": churn_result.get("best_model"),
            "metrics": churn_result.get("metrics", {}),
            "message": churn_result.get("message", "Trained successfully"),
        },
        "next_purchase": {
            "model_type": next_result.get("model_type"),
            "baseline_mean": next_result.get("baseline_mean"),
            "metrics": next_result.get("metrics", {}),
            "message": next_result.get("message", "Trained successfully"),
        },
    }
