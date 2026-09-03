"""Customer domain API. Owned by Developer 1 (Kuldeep).

Phase 1: upload + health (see upload.py).
Phase 2: customer analytics — GET /api/customers/* endpoints.

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
    CustomerRead,
    CustomersListResponse,
    HealthResponse,
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
# 3. Parameterised routes (LAST — would otherwise capture static paths)
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
