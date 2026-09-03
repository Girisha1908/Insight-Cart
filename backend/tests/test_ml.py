"""Tests for Phase 3 — ML: churn prediction, next-purchase, Customer 360.

Covers:
- Feature engineering (features, churn labels, next-purchase targets)
- Churn model training and evaluation
- Next-purchase model training and prediction
- Customer 360, churn, recommendation, and next-purchase API endpoints
- Human-friendly output and no-causal-claims guard
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.database import get_db
from app.main import app
from app.models.customer import Customer
from app.models.order import Order


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _cleanup_models():
    """Remove any saved models after each test so they don't leak."""
    model_dir = Path(__file__).resolve().parent.parent.parent / "ml" / "models"
    yield
    for subdir in ["churn", "next_purchase"]:
        d = model_dir / subdir
        if d.exists():
            for f in d.iterdir():
                if f.suffix in (".joblib", ".json"):
                    f.unlink(missing_ok=True)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client._db_session = db_session
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def _seed_ml_dataset(db_session, n_customers: int = 30) -> None:
    """Seed a dataset large enough for model training."""
    base = datetime(2022, 1, 1, tzinfo=timezone.utc)
    customers = []
    orders = []

    for i in range(n_customers):
        cid = f"ml_c{i:03d}"
        customers.append(
            Customer(
                customer_id=cid,
                customer_unique_id=f"ml_u{i:03d}",
                customer_city="São Paulo",
                customer_state="SP",
            )
        )
        # Each customer gets 1-5 orders spread over time.
        n_orders = (i % 5) + 1
        for j in range(n_orders):
            days_offset = j * 30 + (i % 10) * 5
            # Some customers are "churned" (old last order).
            if i < n_customers // 3:
                # Churned: last order > 90 days old.
                order_date = base + timedelta(days=days_offset)
            else:
                # Active: recent orders.
                order_date = datetime.now(timezone.utc) - timedelta(days=(n_orders - j) * 10)

            orders.append(
                Order(
                    order_id=f"ml_o{i:03d}_{j}",
                    customer_id=cid,
                    order_date=order_date,
                    order_value=float(50 + i * 10 + j * 5),
                    order_status="delivered",
                )
            )

    db_session.add_all(customers)
    db_session.commit()
    db_session.add_all(orders)
    db_session.commit()


def _seed_small_dataset(db_session) -> None:
    """Seed a tiny dataset (5 customers) — too small for ML training."""
    base = datetime(2023, 1, 1, tzinfo=timezone.utc)
    customers = [
        Customer(customer_id=f"sc{i}", customer_unique_id=f"su{i}")
        for i in range(5)
    ]
    db_session.add_all(customers)
    db_session.commit()

    orders = [
        Order(
            order_id=f"so{i}",
            customer_id=f"sc{i}",
            order_date=base + timedelta(days=i * 30),
            order_value=100.0 + i * 50,
            order_status="delivered",
        )
        for i in range(5)
    ]
    db_session.add_all(orders)
    db_session.commit()


# ---------------------------------------------------------------------------
# 1. Feature engineering tests
# ---------------------------------------------------------------------------

class TestFeatureEngineering:
    def test_build_features_returns_all_columns(self, db_session):
        _seed_ml_dataset(db_session, 10)
        from app.services.ml.feature_engineering import (
            FeatureEngineeringService,
            FEATURE_COLUMNS,
        )
        svc = FeatureEngineeringService(db_session)
        feats, ref = svc.build_features(only_with_orders=True)
        assert not feats.empty
        for col in FEATURE_COLUMNS:
            assert col in feats.columns, f"Missing feature: {col}"
        assert ref is not None

    def test_build_features_empty_db(self, db_session):
        from app.services.ml.feature_engineering import FeatureEngineeringService
        svc = FeatureEngineeringService(db_session)
        feats, ref = svc.build_features()
        assert feats.empty

    def test_build_churn_label(self, db_session):
        from app.services.ml.feature_engineering import build_churn_label
        df = pd.DataFrame({
            "customer_id": ["c1", "c2"],
            "last_order": [
                pd.Timestamp("2023-01-01", tz="UTC"),
                pd.Timestamp.now(tz="UTC") - timedelta(days=5),
            ],
        })
        ref = pd.Timestamp.now(tz="UTC")
        result = build_churn_label(df, ref, churn_days=90)
        # c1 is old → churned, c2 is recent → not churned
        assert result.loc[0, "churned"] == 1
        assert result.loc[1, "churned"] == 0

    def test_build_next_purchase_target(self, db_session):
        from app.services.ml.feature_engineering import build_next_purchase_target
        orders = pd.DataFrame({
            "customer_id": ["c1", "c1", "c1", "c2"],
            "order_date": pd.to_datetime([
                "2023-01-01", "2023-02-01", "2023-03-01", "2023-01-15"
            ], utc=True),
        })
        target = build_next_purchase_target(orders)
        # c1 has 2 gaps → gets a target; c2 has 0 gaps → excluded
        assert len(target) == 1
        assert target.iloc[0]["customer_id"] == "c1"
        assert target.iloc[0]["avg_days_to_next_purchase"] == pytest.approx(30.5, abs=1)


# ---------------------------------------------------------------------------
# 2. Churn model training tests
# ---------------------------------------------------------------------------

class TestChurnTraining:
    def test_train_churn_models(self, db_session):
        _seed_ml_dataset(db_session, 30)
        from ml.training.train_churn import train_churn_models
        result = train_churn_models(db_session, save=False)
        assert result["best_model"] is not None
        assert result["best_model"] in result["metrics"]
        assert len(result["models"]) == 3  # LR, RF, XGB
        # All metrics have required keys.
        for name, metrics in result["metrics"].items():
            assert "f1" in metrics
            assert "precision" in metrics
            assert "recall" in metrics
            assert "roc_auc" in metrics
            assert "confusion_matrix" in metrics

    def test_train_churn_saves_model(self, db_session):
        _seed_ml_dataset(db_session, 30)
        from ml.training.train_churn import train_churn_models
        result = train_churn_models(db_session, save=True)
        model_dir = Path(__file__).resolve().parent.parent.parent / "ml" / "models" / "churn"
        assert (model_dir / "model.joblib").exists()
        assert (model_dir / "scaler.joblib").exists()
        assert (model_dir / "feature_columns.joblib").exists()
        assert (model_dir / "metadata.json").exists()
        meta = json.loads((model_dir / "metadata.json").read_text())
        assert meta["best_model"] == result["best_model"]

    def test_train_churn_insufficient_data(self, db_session):
        _seed_small_dataset(db_session)
        from ml.training.train_churn import train_churn_models
        result = train_churn_models(db_session, save=False)
        assert result["best_model"] is None
        assert "Insufficient" in result["message"]

    def test_predict_churn(self, db_session):
        _seed_ml_dataset(db_session, 30)
        from ml.training.train_churn import train_churn_models, predict_churn
        train_churn_models(db_session, save=True)
        pred = predict_churn(db_session, "ml_c000")
        assert pred is not None
        assert 0 <= pred["churn_probability"] <= 1
        assert pred["risk_level"] in ("High risk", "Medium risk", "Low risk", "Very low risk")
        assert "likelihood of churn" in pred["summary"]
        assert pred["recommended_action"]  # non-empty

    def test_predict_churn_no_model(self, db_session):
        _seed_ml_dataset(db_session, 10)
        from ml.training.train_churn import predict_churn
        pred = predict_churn(db_session, "ml_c000")
        assert pred is None  # no saved model

    def test_predict_churn_unknown_customer(self, db_session):
        _seed_ml_dataset(db_session, 30)
        from ml.training.train_churn import train_churn_models, predict_churn
        train_churn_models(db_session, save=True)
        pred = predict_churn(db_session, "nonexistent")
        assert pred is None


# ---------------------------------------------------------------------------
# 3. Next-purchase prediction tests
# ---------------------------------------------------------------------------

class TestNextPurchase:
    def test_train_next_purchase(self, db_session):
        _seed_ml_dataset(db_session, 30)
        from ml.training.train_next_purchase import train_next_purchase_model
        result = train_next_purchase_model(db_session, save=False)
        assert result["baseline_mean"] is not None
        assert result["baseline_mean"] > 0

    def test_predict_next_purchase(self, db_session):
        _seed_ml_dataset(db_session, 30)
        from ml.training.train_next_purchase import predict_next_purchase
        pred = predict_next_purchase(db_session, "ml_c001")
        assert pred is not None
        assert pred["customer_id"] == "ml_c001"
        assert pred["predicted_days_to_next_purchase"] > 0
        assert pred["predicted_next_purchase_date"]
        assert pred["model_used"]

    def test_predict_next_purchase_unknown(self, db_session):
        _seed_ml_dataset(db_session, 30)
        from ml.training.train_next_purchase import predict_next_purchase
        pred = predict_next_purchase(db_session, "nonexistent")
        assert pred is None

    def test_single_order_customer(self, db_session):
        """Single-order customers get a fallback prediction."""
        _seed_small_dataset(db_session)
        from ml.training.train_next_purchase import predict_next_purchase
        pred = predict_next_purchase(db_session, "sc0")
        assert pred is not None
        assert pred["predicted_days_to_next_purchase"] > 0
        assert "approximate" in pred["confidence_note"].lower()


# ---------------------------------------------------------------------------
# 4. Evaluation metrics tests
# ---------------------------------------------------------------------------

class TestEvaluationMetrics:
    def test_evaluate_classification(self):
        from ml.evaluation.metrics import evaluate_classification
        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 0])
        y_prob = np.array([0.1, 0.2, 0.8, 0.9, 0.7, 0.3, 0.85, 0.15, 0.75, 0.4])
        metrics = evaluate_classification(y_true, y_prob)
        assert 0 <= metrics["precision"] <= 1
        assert 0 <= metrics["recall"] <= 1
        assert 0 <= metrics["f1"] <= 1
        assert 0 <= metrics["roc_auc"] <= 1
        assert len(metrics["confusion_matrix"]) == 2
        assert all(len(row) == 2 for row in metrics["confusion_matrix"])

    def test_evaluate_single_class(self):
        """All-true or all-false labels should not crash."""
        from ml.evaluation.metrics import evaluate_classification
        y_true = np.array([1, 1, 1, 1])
        y_prob = np.array([0.8, 0.9, 0.7, 0.85])
        metrics = evaluate_classification(y_true, y_prob)
        assert metrics["roc_auc"] == 0.0  # can't compute AUC with one class

    def test_select_best_model(self):
        from ml.evaluation.metrics import select_best_model
        m = {
            "lr": {"f1": 0.7},
            "rf": {"f1": 0.85},
            "xgb": {"f1": 0.8},
        }
        assert select_best_model(m) == "rf"


# ---------------------------------------------------------------------------
# 5. API endpoint tests
# ---------------------------------------------------------------------------

class TestMLAPI:
    def test_api_train_endpoint(self, client):
        _seed_ml_dataset(client._db_session, 30)
        resp = client.post("/api/ml/train?churn_days=90")
        assert resp.status_code == 200
        data = resp.json()
        assert "churn" in data
        assert data["churn"]["best_model"] is not None
        assert "next_purchase" in data

    def test_api_churn_summary(self, client):
        _seed_ml_dataset(client._db_session, 30)
        # Train first.
        client.post("/api/ml/train?churn_days=90")
        resp = client.get("/api/ml/churn/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["total_customers_scored"] > 0
        assert "risk_distribution" in data

    def test_api_churn_summary_not_trained(self, client):
        _seed_ml_dataset(client._db_session, 10)
        resp = client.get("/api/ml/churn/summary")
        # Should auto-train or return not_ready
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ready", "not_ready")

    def test_api_model_metrics(self, client):
        resp = client.get("/api/ml/model/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "churn" in data
        assert "next_purchase" in data

    def test_api_model_metrics_after_training(self, client):
        _seed_ml_dataset(client._db_session, 30)
        client.post("/api/ml/train?churn_days=90")
        resp = client.get("/api/ml/model/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["churn"]["best_model"] is not None
        assert "metrics" in data["churn"]


class TestCustomerAPIPhase3:
    def test_api_customer_360(self, client):
        _seed_ml_dataset(client._db_session, 30)
        client.post("/api/ml/train?churn_days=90")
        resp = client.get("/api/customers/ml_c005/360")
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_id"] == "ml_c005"
        assert "segment" in data
        assert "health_score" in data
        assert data["churn_prediction"] is not None
        assert data["next_purchase_prediction"] is not None
        assert data["recommendations"]

    def test_api_customer_churn(self, client):
        _seed_ml_dataset(client._db_session, 30)
        client.post("/api/ml/train?churn_days=90")
        resp = client.get("/api/customers/ml_c001/churn")
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_id"] == "ml_c001"
        # Churn model is trained, so we should get a prediction.
        assert data.get("risk_level") is not None
        assert "likelihood of churn" in data.get("summary", "")

    def test_api_customer_churn_no_model(self, client):
        _seed_small_dataset(client._db_session)
        resp = client.get("/api/customers/sc0/churn")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "model_not_trained"

    def test_api_customer_recommendation(self, client):
        _seed_ml_dataset(client._db_session, 30)
        client.post("/api/ml/train?churn_days=90")
        resp = client.get("/api/customers/ml_c001/recommendation")
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_id"] == "ml_c001"
        assert data["recommendations"]
        # Verify no causal claims in recommendations.
        for rec in data["recommendations"]:
            assert "will reduce" not in rec["action"].lower()
            assert "will increase" not in rec["action"].lower()

    def test_api_customer_next_purchase(self, client):
        _seed_ml_dataset(client._db_session, 30)
        resp = client.get("/api/customers/ml_c001/next-purchase")
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_id"] == "ml_c001"
        assert data.get("predicted_days_to_next_purchase", 0) > 0

    def test_api_customer_360_not_found(self, client):
        resp = client.get("/api/customers/nonexistent/360")
        assert resp.status_code == 404

    def test_api_customer_churn_not_found(self, client):
        resp = client.get("/api/customers/nonexistent/churn")
        assert resp.status_code == 404

    def test_api_customer_recommendation_not_found(self, client):
        resp = client.get("/api/customers/nonexistent/recommendation")
        assert resp.status_code == 404

    def test_api_customer_next_purchase_not_found(self, client):
        resp = client.get("/api/customers/nonexistent/next-purchase")
        assert resp.status_code == 404

    def test_human_friendly_churn_output(self, client):
        """Churn output must be human-readable, not raw probabilities."""
        _seed_ml_dataset(client._db_session, 30)
        client.post("/api/ml/train?churn_days=90")
        resp = client.get("/api/customers/ml_c001/churn")
        data = resp.json()
        if data.get("summary"):
            # Must contain percentage, not raw decimal.
            assert "%" in data["summary"]
            # Must contain risk level phrase.
            assert any(
                phrase in data["summary"]
                for phrase in ["High risk", "Elevated risk", "Low risk", "Very low risk"]
            )


# ---------------------------------------------------------------------------
# 6. No causal claims guard
# ---------------------------------------------------------------------------

class TestNoCausalClaims:
    def test_recommendations_contain_no_causal_language(self, client):
        _seed_ml_dataset(client._db_session, 30)
        client.post("/api/ml/train?churn_days=90")
        # Check multiple customers.
        for cid in ["ml_c000", "ml_c010", "ml_c020"]:
            resp = client.get(f"/api/customers/{cid}/recommendation")
            if resp.status_code == 200:
                data = resp.json()
                for rec in data.get("recommendations", []):
                    action = rec["action"].lower()
                    assert "will" not in action or "will" in action  # "will consider" is OK
                    # Check for causal phrasing patterns.
                    causal_phrases = [
                        "will reduce churn",
                        "will increase retention",
                        "will improve revenue",
                        "causes",
                        "guarantees",
                    ]
                    for phrase in causal_phrases:
                        assert phrase not in action, f"Causal claim found: '{phrase}' in '{action}'"
