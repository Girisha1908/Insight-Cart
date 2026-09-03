"""Tests for Phase 2 customer analytics.

Covers:
- Base customer metrics (recency / frequency / monetary / lifetime)
- RFM segmentation and human-friendly segment names
- Historical CLV
- Repeat purchase rate
- Customer health score (0-100) and band labels
- API endpoints: /api/customers, /segments, /rfm, /retention, /cohorts
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.database import get_db
from app.main import app
from app.models.customer import Customer
from app.models.order import Order
from app.services.customers import (
    CustomerMetricsService,
    compute_rfm,
    compute_clv,
    compute_repeat_purchase_rate,
    compute_health_scores,
    health_score_summary,
)
from app.services.customers.cohorts import build_cohort_matrix
from app.services.customers.rfm import (
    build_rfm_summary,
    compute_segment_distribution,
    SEGMENT_DESCRIPTIONS,
)
from app.services.analytics import CustomerAnalyticsService


# ---------------------------------------------------------------------------
# Test DB fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    """In-memory SQLite session with the canonical schema."""
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
        # The TestClient now uses the db_session. Expose the session via a
        # private attribute so API tests can seed the same DB the API reads.
        test_client._db_session = db_session
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def _seed_basic_dataset(db_session) -> None:
    """Seed a tiny but realistic dataset: 3 customers, multiple orders."""
    customers = [
        Customer(
            customer_id="c1",
            customer_unique_id="u1",
            customer_city="São Paulo",
            customer_state="SP",
        ),
        Customer(
            customer_id="c2",
            customer_unique_id="u2",
            customer_city="Rio de Janeiro",
            customer_state="RJ",
        ),
        Customer(
            customer_id="c3",
            customer_unique_id="u3",
            customer_city="Curitiba",
            customer_state="PR",
        ),
    ]
    db_session.add_all(customers)
    db_session.commit()

    base = datetime(2023, 1, 1, tzinfo=timezone.utc)
    orders = [
        # c1 — repeat customer, recent, high value
        Order(order_id="o1", customer_id="c1", order_date=base, order_value=100.0, order_status="delivered"),
        Order(order_id="o2", customer_id="c1", order_date=base + timedelta(days=30), order_value=200.0, order_status="delivered"),
        Order(order_id="o3", customer_id="c1", order_date=base + timedelta(days=60), order_value=300.0, order_status="delivered"),
        # c2 — single order, mid value
        Order(order_id="o4", customer_id="c2", order_date=base + timedelta(days=10), order_value=150.0, order_status="delivered"),
        # c3 — single order, very old
        Order(order_id="o5", customer_id="c3", order_date=base - timedelta(days=400), order_value=50.0, order_status="delivered"),
    ]
    db_session.add_all(orders)
    db_session.commit()


# ---------------------------------------------------------------------------
# 1. Base metrics tests
# ---------------------------------------------------------------------------

def test_customer_metrics_basic(db_session):
    _seed_basic_dataset(db_session)
    svc = CustomerMetricsService(db_session)
    metrics, ctx = svc.build_customer_metrics(only_with_orders=False)
    assert not metrics.empty
    # Three customers in the dataset.
    assert len(metrics) == 3
    # At least one customer has 3 orders (c1).
    counts = metrics["total_orders"].fillna(0).astype(int)
    assert counts.max() == 3
    # Total revenue includes 100 + 200 + 300 + 150 + 50 = 800.
    assert float(metrics["total_revenue"].sum()) == pytest.approx(800.0)
    # The reference date is the max order date.
    assert ctx.reference_date >= pd.Timestamp(base := datetime(2023, 1, 1, tzinfo=timezone.utc))


def test_customer_metrics_empty_db(db_session):
    svc = CustomerMetricsService(db_session)
    metrics, ctx = svc.build_customer_metrics()
    assert metrics.empty
    assert ctx.total_customer_count == 0


# ---------------------------------------------------------------------------
# 2. RFM tests
# ---------------------------------------------------------------------------

def test_rfm_segment_names_human_friendly(db_session):
    _seed_basic_dataset(db_session)
    svc = CustomerMetricsService(db_session)
    metrics, _ = svc.build_customer_metrics(only_with_orders=False)
    rfm = compute_rfm(metrics)
    # Every scored row should map to a known segment.
    scored = rfm[rfm["segment_key"] != "no_orders"]
    assert len(scored) == 3
    for key in scored["segment_key"]:
        assert key in SEGMENT_DESCRIPTIONS
    # c1 is recent + frequent + high spend → Champions.
    c1 = rfm[rfm["customer_id"] == "c1"].iloc[0]
    assert c1["segment_key"] == "champions"
    assert c1["segment_name"] == "Champions"


def test_rfm_summary(db_session):
    _seed_basic_dataset(db_session)
    svc = CustomerMetricsService(db_session)
    metrics, _ = svc.build_customer_metrics(only_with_orders=False)
    rfm = compute_rfm(metrics)
    summary = build_rfm_summary(rfm)
    assert len(summary) >= 1
    for seg in summary:
        assert seg.customer_count >= 1
        assert seg.description  # human-readable description
    distribution = compute_segment_distribution(rfm)
    assert sum(distribution.values()) == 3


def test_rfm_handles_no_orders(db_session):
    svc = CustomerMetricsService(db_session)
    # Customer with no orders
    db_session.add(Customer(customer_id="c_only", customer_unique_id="u_only"))
    db_session.commit()
    metrics, _ = svc.build_customer_metrics(only_with_orders=False)
    rfm = compute_rfm(metrics)
    no_orders = rfm[rfm["customer_id"] == "c_only"].iloc[0]
    assert no_orders["segment_key"] == "no_orders"
    assert no_orders["segment_name"] == "No Orders"


# ---------------------------------------------------------------------------
# 3. CLV tests
# ---------------------------------------------------------------------------

def test_clv_known_calculation(db_session):
    _seed_basic_dataset(db_session)
    svc = CustomerMetricsService(db_session)
    metrics, _ = svc.build_customer_metrics(only_with_orders=False)
    clv = compute_clv(metrics)
    c1 = clv[clv["customer_id"] == "c1"].iloc[0]
    # c1: AOV = (100 + 200 + 300) / 3 = 200
    #     total_orders = 3
    #     lifetime_years = 60 / 365.25 ≈ 0.164 → clipped to 0.25
    #     freq = 3 / 0.25 = 12
    #     CLV = 200 * 12 * 0.25 = 600
    assert float(c1["avg_order_value"]) == pytest.approx(200.0, rel=0.01)
    assert float(c1["customer_lifetime_years"]) == pytest.approx(0.25, rel=0.01)
    assert float(c1["historical_clv"]) > 0
    # c2: only 1 order, low value
    c2 = clv[clv["customer_id"] == "c2"].iloc[0]
    assert float(c2["avg_order_value"]) == pytest.approx(150.0)
    assert float(c2["historical_clv"]) > 0


def test_clv_no_orders(db_session):
    db_session.add(Customer(customer_id="c_no_ord", customer_unique_id="u_no_ord"))
    db_session.commit()
    svc = CustomerMetricsService(db_session)
    metrics, _ = svc.build_customer_metrics(only_with_orders=False)
    clv = compute_clv(metrics)
    row = clv[clv["customer_id"] == "c_no_ord"].iloc[0]
    assert float(row["historical_clv"]) == 0.0


# ---------------------------------------------------------------------------
# 4. Retention tests
# ---------------------------------------------------------------------------

def test_repeat_purchase_rate(db_session):
    _seed_basic_dataset(db_session)
    svc = CustomerMetricsService(db_session)
    metrics, _ = svc.build_customer_metrics(only_with_orders=False)
    retention = compute_repeat_purchase_rate(metrics)
    # 1 of 3 customers is a repeat customer (c1 with 3 orders).
    assert retention.total_customers == 3
    assert retention.repeat_customers == 1
    assert retention.one_time_buyers == 2
    assert retention.repeat_purchase_rate == pytest.approx(1 / 3, rel=0.01)
    assert retention.average_orders_per_customer == pytest.approx(5 / 3, rel=0.01)


def test_cohort_matrix(db_session):
    _seed_basic_dataset(db_session)
    svc = CustomerMetricsService(db_session)
    orders = svc.load_orders()
    from app.services.customers.retention import compute_retention_curve
    curve = compute_retention_curve(orders)
    matrix = build_cohort_matrix(curve)
    assert not matrix.empty
    # Should have a cohort_size column.
    assert "cohort_size" in matrix.columns


# ---------------------------------------------------------------------------
# 5. Health score tests
# ---------------------------------------------------------------------------

def test_health_score_range_and_labels(db_session):
    _seed_basic_dataset(db_session)
    svc = CustomerMetricsService(db_session)
    metrics, _ = svc.build_customer_metrics(only_with_orders=False)
    health = compute_health_scores(metrics)
    assert len(health) == 3
    # All scores should be in 0..100
    assert (health["health_score"] >= 0).all()
    assert (health["health_score"] <= 100).all()
    # Every row has a label
    for label in health["health_label"]:
        assert label in {"Excellent", "Good", "Fair", "Poor", "Critical"}


def test_health_summary_aggregates(db_session):
    _seed_basic_dataset(db_session)
    svc = CustomerMetricsService(db_session)
    metrics, _ = svc.build_customer_metrics(only_with_orders=False)
    health = compute_health_scores(metrics)
    summary = health_score_summary(health)
    assert summary["total_scored"] == 3
    assert summary["excellent_count"] + summary["good_count"] + summary["fair_count"] + summary["poor_count"] + summary["critical_count"] == 3
    assert summary["average_health_score"] > 0


# ---------------------------------------------------------------------------
# 6. Orchestrator / full pipeline
# ---------------------------------------------------------------------------

def test_customer_analytics_orchestrator(db_session):
    _seed_basic_dataset(db_session)
    svc = CustomerAnalyticsService(db_session)
    result = svc.compute_all()
    # All sections are populated.
    assert result.rfm.segments
    assert result.clv.average_clv >= 0
    assert result.retention.total_customers == 3
    assert result.health.total_scored == 3
    assert "reference_date" in result.context


def test_single_customer_analytics(db_session):
    _seed_basic_dataset(db_session)
    svc = CustomerAnalyticsService(db_session)
    detail = svc.get_customer_analytics("c1")
    assert detail is not None
    assert detail["customer_id"] == "c1"
    # c1 should be a Champion
    assert detail["segment_key"] == "champions"
    assert detail["historical_clv"] > 0
    assert "CLV =" in detail["clv_formula"]
    assert detail["health_label"] in {"Excellent", "Good", "Fair", "Poor", "Critical"}


# ---------------------------------------------------------------------------
# 7. API endpoint tests
# ---------------------------------------------------------------------------

def test_api_list_customers(client):
    _seed_basic_dataset(client._db_session)
    response = client.get("/api/customers")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


def test_api_rfm_endpoint(client):
    _seed_basic_dataset(client._db_session)
    response = client.get("/api/customers/rfm")
    assert response.status_code == 200
    data = response.json()
    assert "segments" in data
    assert "segment_distribution" in data
    assert "reference_date" in data
    # At least one segment
    assert len(data["segments"]) >= 1
    # Every segment has a description (human-friendly)
    for seg in data["segments"]:
        assert seg["description"]


def test_api_segments_endpoint(client):
    _seed_basic_dataset(client._db_session)
    response = client.get("/api/customers/segments")
    assert response.status_code == 200
    assert "segments" in response.json()


def test_api_retention_endpoint(client):
    _seed_basic_dataset(client._db_session)
    response = client.get("/api/customers/retention")
    assert response.status_code == 200
    data = response.json()
    assert "repeat_purchase_rate" in data
    assert "retention_curve" in data
    assert "cohort_matrix" in data
    assert 0 <= data["repeat_purchase_rate"] <= 1


def test_api_cohorts_endpoint(client):
    _seed_basic_dataset(client._db_session)
    response = client.get("/api/customers/cohorts")
    assert response.status_code == 200
    assert "cohort_matrix" in response.json()


def test_api_health_endpoint(client):
    _seed_basic_dataset(client._db_session)
    response = client.get("/api/customers/health")
    assert response.status_code == 200
    data = response.json()
    assert "average_health_score" in data
    assert "total_scored" in data


def test_api_customer_analytics_detail(client):
    _seed_basic_dataset(client._db_session)
    response = client.get("/api/customers/c1/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "c1"
    assert "CLV =" in data["clv_formula"]
    assert data["segment_key"] == "champions"


def test_api_404_for_unknown_customer(client):
    response = client.get("/api/customers/nonexistent")
    assert response.status_code == 404


def test_api_404_for_unknown_customer_analytics(client):
    _seed_basic_dataset(client._db_session)
    response = client.get("/api/customers/nonexistent/analytics")
    assert response.status_code == 404
