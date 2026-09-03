"""Data Ingestion & Upload API router.

Shared foundation between developers for uploading datasets, inspecting
ingestion status, and populating demo datasets.
"""

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.customer import Customer
from app.models.order import Order
from app.schemas.customer import DataSummaryResponse, IngestionStats, UploadResponse
from app.services.ingestion.customer_ingestion import CustomerOrderIngestionService

router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload dataset CSV file (customers or orders)",
)
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_type: str = Form(..., description="Either 'customers' or 'orders'"),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """Upload a CSV dataset, validate records, and ingest into the database."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported.",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    ingestion_service = CustomerOrderIngestionService(db)

    if dataset_type.lower() in ("customers", "customer"):
        stats = ingestion_service.ingest_customers(content)
        return UploadResponse(
            status="ok",
            message=f"Successfully processed {stats.rows_processed} customers ({stats.rows_inserted} inserted/updated).",
            stats={"customers": stats},
        )
    elif dataset_type.lower() in ("orders", "order"):
        stats = ingestion_service.ingest_orders(content)
        return UploadResponse(
            status="ok",
            message=f"Successfully processed {stats.rows_processed} orders ({stats.rows_inserted} inserted/updated).",
            stats={"orders": stats},
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown dataset_type '{dataset_type}'. Supported: 'customers', 'orders'.",
        )


@router.post(
    "/upload/bundle",
    response_model=UploadResponse,
    summary="Upload multiple CSVs together (customers, orders, payments)",
)
async def upload_bundle(
    customers_file: Optional[UploadFile] = File(None),
    orders_file: Optional[UploadFile] = File(None),
    payments_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """Upload and ingest customers, orders, and optional payment files in a coordinated flow."""
    if not customers_file and not orders_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file (customers_file or orders_file) must be provided.",
        )

    ingestion_service = CustomerOrderIngestionService(db)
    stats_dict = {}

    if customers_file:
        cust_content = await customers_file.read()
        if len(cust_content) > 0:
            stats_dict["customers"] = ingestion_service.ingest_customers(cust_content)

    if orders_file:
        ord_content = await orders_file.read()
        pay_content = (await payments_file.read()) if payments_file else None
        if len(ord_content) > 0:
            stats_dict["orders"] = ingestion_service.ingest_orders(
                ord_content, pay_content if pay_content and len(pay_content) > 0 else None
            )

    return UploadResponse(
        status="ok",
        message="Bundle ingestion completed successfully.",
        stats=stats_dict,
    )


@router.post(
    "/ingest-demo",
    response_model=UploadResponse,
    summary="Ingest demo dataset from local data directory",
)
def ingest_demo(
    limit_rows: Optional[int] = Query(None, description="Limit rows for fast development testing"),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """Ingest the Olist dataset from data/demo/olist/raw or data/raw."""
    ingestion_service = CustomerOrderIngestionService(db)
    try:
        stats = ingestion_service.ingest_olist_bundle(limit_rows=limit_rows)
        return UploadResponse(
            status="ok",
            message="Demo dataset ingested successfully.",
            stats=stats,
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ingesting demo data: {str(e)}",
        )


@router.get(
    "/summary",
    response_model=DataSummaryResponse,
    summary="Get overall database ingestion summary",
)
def get_data_summary(db: Session = Depends(get_db)) -> DataSummaryResponse:
    """Return counts and aggregate metrics for ingested customer and order records."""
    total_customers = db.scalar(select(func.count(Customer.customer_id))) or 0
    unique_identities = db.scalar(select(func.count(func.distinct(Customer.customer_unique_id)))) or 0
    total_orders = db.scalar(select(func.count(Order.order_id))) or 0
    total_revenue_raw = db.scalar(select(func.sum(Order.order_value))) or 0.0
    earliest_date = db.scalar(select(func.min(Order.order_date)))
    latest_date = db.scalar(select(func.max(Order.order_date)))

    return DataSummaryResponse(
        total_customers=total_customers,
        total_orders=total_orders,
        unique_customer_identities=unique_identities,
        total_revenue=float(total_revenue_raw),
        earliest_order_date=earliest_date,
        latest_order_date=latest_date,
        status="ok",
    )


@router.get(
    "/health",
    summary="Data pipeline health check",
)
def upload_health() -> dict:
    """Health check for data pipeline."""
    return {"status": "ok", "service": "data-pipeline", "environment": settings.ENVIRONMENT}
