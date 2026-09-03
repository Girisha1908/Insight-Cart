"""Customer domain API. Owned by Developer 1 (Kuldeep).

Phase 1: upload + health (see upload.py).
Phase 2: customer analytics — GET /api/customers/* endpoints.
Phase 3: Customer 360, churn prediction, recommendations, next-purchase.

IMPORTANT: route registration order matters. Static paths (``/rfm``,
``/segments``, ``/retention``, ``/cohorts``, ``/health``) MUST be registered
before the parameterised path (``/{customer_id}``), otherwise FastAPI will
route ``/rfm`` into the ``{customer_id}`` handler.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.customer import Customer
from app.schemas.customer import (
    CustomerAnalyticsDetail,
    Customer360Response,
    CustomerChurnResponse,
    CustomerRead,
    CustomersListResponse,
    CustomerRecommendationResponse,
    HealthResponse,
    NextPurchaseResponse,
    RFMResponse,
    RetentionResponse,
)
from app.services.analytics import CustomerAnalyticsService

router = APIRouter()


# ---------------------------------------------------------------------------
# 1. List (root)
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=CustomersListResponse,
    summary="List all customers",
)
def list_customers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Page size"),
    db: Session = Depends(get_db),
) -> CustomersListResponse:
    """Return paginated customer list with basic info."""
    total = db.scalar(select(func.count(Customer.customer_id))) or 0
    offset = (page - 1) * page_size
    stmt = select(Customer).offset(offset).limit(page_size)
    rows = db.scalars(stmt).all()
    return CustomersListResponse(
        items=[CustomerRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# 2. Analytics endpoints (STATIC paths first — they would otherwise be
#    captured by /{customer_id} below)
# ---------------------------------------------------------------------------

@router.get(
    "/rfm",
    response_model=RFMResponse,
    summary="RFM segmentation overview",
)
def get_rfm(db: Session = Depends(get_db)) -> RFMResponse:
    """Return RFM segment counts and human-friendly segment descriptions."""
    svc = CustomerAnalyticsService(db)
    analytics = svc.compute_all()
    return RFMResponse(
        segments=[s.__dict__ for s in analytics.rfm.segments],
        segment_distribution=analytics.rfm.segment_distribution,
        reference_date=analytics.rfm.reference_date,
    )


@router.get(
    "/segments",
    response_model=RFMResponse,
    summary="Customer segment overview",
)
def get_segments(db: Session = Depends(get_db)) -> RFMResponse:
    """Alias for /rfm — returns RFM segment counts and descriptions."""
    return get_rfm(db)


@router.get(
    "/retention",
    response_model=RetentionResponse,
    summary="Retention and cohort analysis",
)
def get_retention(db: Session = Depends(get_db)) -> RetentionResponse:
    """Return repeat-purchase rate, cohort matrix, and retention curve."""
    svc = CustomerAnalyticsService(db)
    analytics = svc.compute_all()
    return RetentionResponse(
        repeat_purchase_rate=analytics.retention.repeat_purchase_rate,
        total_customers=analytics.retention.total_customers,
        repeat_customers=analytics.retention.repeat_customers,
        average_orders_per_customer=analytics.retention.average_orders_per_customer,
        one_time_buyers=analytics.retention.one_time_buyers,
        active_customers=analytics.retention.active_customers,
        retention_curve=analytics.retention.retention_curve,
        cohort_matrix=analytics.retention.cohort_matrix,
    )


@router.get(
    "/cohorts",
    response_model=RetentionResponse,
    summary="Cohort analysis matrix",
)
def get_cohorts(db: Session = Depends(get_db)) -> RetentionResponse:
    """Return cohort matrix and retention curve (alias for /retention)."""
    return get_retention(db)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Customer health score distribution",
)
def get_health(db: Session = Depends(get_db)) -> HealthResponse:
    """Return aggregate customer health score distribution."""
    svc = CustomerAnalyticsService(db)
    analytics = svc.compute_all()
    return HealthResponse(
        average_health_score=analytics.health.average_health_score,
        median_health_score=analytics.health.median_health_score,
        excellent_count=analytics.health.excellent_count,
        good_count=analytics.health.good_count,
        fair_count=analytics.health.fair_count,
        poor_count=analytics.health.poor_count,
        critical_count=analytics.health.critical_count,
        total_scored=analytics.health.total_scored,
    )


# ---------------------------------------------------------------------------
# 3. ML-powered single-customer endpoints (STATIC sub-paths first)
# ---------------------------------------------------------------------------

@router.get(
    "/{customer_id}/360",
    response_model=Customer360Response,
    summary="Customer 360 — full profile with ML predictions",
)
def get_customer_360(
    customer_id: str,
    db: Session = Depends(get_db),
) -> Customer360Response:
    """Return a complete 360-degree view of one customer."""
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    svc = CustomerAnalyticsService(db)
    analytics = svc.get_customer_analytics(customer_id)
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analytics data found for this customer",
        )

    # ML predictions (graceful fallback if model not trained).
    churn_pred = _safe_churn_prediction(db, customer_id)
    next_pred = _safe_next_purchase(db, customer_id)
    recommendation = _build_recommendation(analytics, churn_pred)

    return Customer360Response(
        customer_id=customer_id,
        segment=analytics["segment"],
        segment_key=analytics["segment_key"],
        segment_description=analytics["segment_description"],
        rfm_code=analytics["rfm_code"],
        recency_days=analytics["recency_days"],
        total_orders=analytics["total_orders"],
        total_revenue=analytics["total_revenue"],
        avg_order_value=analytics["avg_order_value"],
        historical_clv=analytics["historical_clv"],
        clv_formula=analytics["clv_formula"],
        health_score=analytics["health_score"],
        health_label=analytics["health_label"],
        churn_prediction=churn_pred,
        next_purchase_prediction=next_pred,
        recommendations=recommendation,
    )


@router.get(
    "/{customer_id}/churn",
    response_model=CustomerChurnResponse,
    summary="Churn prediction for one customer",
)
def get_customer_churn(
    customer_id: str,
    db: Session = Depends(get_db),
) -> CustomerChurnResponse:
    """Return churn probability and human-friendly risk assessment."""
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    pred = _safe_churn_prediction(db, customer_id)
    if pred is None:
        return CustomerChurnResponse(
            customer_id=customer_id,
            status="model_not_trained",
            summary="Churn model has not been trained yet. Call POST /api/ml/train first.",
        )
    return CustomerChurnResponse(**pred)


@router.get(
    "/{customer_id}/recommendation",
    response_model=CustomerRecommendationResponse,
    summary="Retention recommendation for one customer",
)
def get_customer_recommendation(
    customer_id: str,
    db: Session = Depends(get_db),
) -> CustomerRecommendationResponse:
    """Return actionable, non-causal retention recommendations."""
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    svc = CustomerAnalyticsService(db)
    analytics = svc.get_customer_analytics(customer_id)
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analytics data found for this customer",
        )

    churn_pred = _safe_churn_prediction(db, customer_id)
    recommendation = _build_recommendation(analytics, churn_pred)

    return CustomerRecommendationResponse(
        customer_id=customer_id,
        segment=analytics["segment"],
        health_label=analytics["health_label"],
        recommendations=recommendation,
    )


@router.get(
    "/{customer_id}/next-purchase",
    response_model=NextPurchaseResponse,
    summary="Next-purchase prediction for one customer",
)
def get_customer_next_purchase(
    customer_id: str,
    db: Session = Depends(get_db),
) -> NextPurchaseResponse:
    """Return predicted next purchase date for one customer."""
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    pred = _safe_next_purchase(db, customer_id)
    if pred is None:
        return NextPurchaseResponse(
            customer_id=customer_id,
            status="no_data",
            summary="No order data available to predict next purchase.",
        )
    return NextPurchaseResponse(**pred)


# ---------------------------------------------------------------------------
# 4. Parameterised routes (LAST — would otherwise capture static paths)
# ---------------------------------------------------------------------------

@router.get(
    "/{customer_id}",
    response_model=CustomerRead,
    summary="Get a single customer by ID",
)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
) -> CustomerRead:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return CustomerRead.model_validate(customer)


@router.get(
    "/{customer_id}/analytics",
    response_model=CustomerAnalyticsDetail,
    summary="Full analytics for one customer",
)
def get_customer_analytics(
    customer_id: str,
    db: Session = Depends(get_db),
) -> CustomerAnalyticsDetail:
    """Return RFM segment, CLV formula, health score and all metrics for one customer."""
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    svc = CustomerAnalyticsService(db)
    result = svc.get_customer_analytics(customer_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analytics data found for this customer",
        )
    return CustomerAnalyticsDetail(**result)


# ---------------------------------------------------------------------------
# ML helper functions
# ---------------------------------------------------------------------------

def _safe_churn_prediction(db: Session, customer_id: str) -> dict | None:
    """Attempt churn prediction; return None if model unavailable."""
    try:
        from ml.training.train_churn import predict_churn
        return predict_churn(db, customer_id)
    except Exception:
        return None


def _safe_next_purchase(db: Session, customer_id: str) -> dict | None:
    """Attempt next-purchase prediction; return None if unavailable."""
    try:
        from ml.training.train_next_purchase import predict_next_purchase
        return predict_next_purchase(db, customer_id)
    except Exception:
        return None


def _build_recommendation(analytics: dict, churn_pred: dict | None) -> list[dict]:
    """Generate non-causal retention recommendations based on analytics + churn."""
    recs: list[dict] = []
    segment = analytics.get("segment_key", "")
    health = analytics.get("health_label", "")
    recency = analytics.get("recency_days")
    orders = analytics.get("total_orders", 0)

    # Segment-based recommendation.
    segment_actions = {
        "champions": "Maintain engagement through loyalty rewards and early access to new products.",
        "loyal_customers": "Recognize their loyalty with exclusive offers or a thank-you program.",
        "potential_loyalist": "Encourage a second purchase with a targeted follow-up offer.",
        "new_customer": "Welcome them and guide them toward a second purchase.",
        "at_risk": "Re-engagement campaign may help — consider a personalized outreach.",
        "cannot_lose_them": "Priority win-back: this customer has high historical value.",
        "hibernating": "A reactivation campaign could test interest — keep costs low.",
    }
    if segment in segment_actions:
        recs.append({
            "type": "segment",
            "title": f"Segment: {analytics.get('segment', segment)}",
            "action": segment_actions[segment],
        })

    # Health-based recommendation.
    if health == "Critical":
        recs.append({
            "type": "health",
            "title": "Critical health score",
            "action": "This customer needs immediate attention — review recent experience.",
        })
    elif health == "Poor":
        recs.append({
            "type": "health",
            "title": "Poor health score",
            "action": "Consider a small gesture to re-engage (e.g. personalized communication).",
        })

    # Churn-risk recommendation.
    if churn_pred:
        risk = churn_pred.get("risk_level", "")
        if risk in ("High risk", "Medium risk"):
            recs.append({
                "type": "churn_risk",
                "title": f"Churn risk: {risk}",
                "action": churn_pred.get("recommended_action", "Consider a retention outreach."),
            })

    # Recency-based recommendation.
    if recency and recency > 180:
        recs.append({
            "type": "recency",
            "title": "No purchase in 6+ months",
            "action": "Consider a win-back campaign to test renewed interest.",
        })

    if not recs:
        recs.append({
            "type": "general",
            "title": "Healthy customer",
            "action": "Maintain current engagement strategy.",
        })

    return recs
