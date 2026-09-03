"""Customer and Order Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Order Schemas
# ---------------------------------------------------------------------------

class OrderBase(BaseModel):
    order_id: str = Field(..., description="Unique order ID")
    customer_id: str = Field(..., description="Customer ID reference")
    order_date: Optional[datetime] = Field(None, description="Timestamp of the order")
    order_status: Optional[str] = Field(None, description="Status (delivered, shipped, etc.)")
    order_value: Optional[Decimal] = Field(None, description="Total monetary value of the order")


class OrderCreate(OrderBase):
    pass


class OrderRead(OrderBase):
    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    items: List[OrderRead]
    total: int
    page: int = 1
    page_size: int = 50


# ---------------------------------------------------------------------------
# Customer Schemas
# ---------------------------------------------------------------------------

class CustomerBase(BaseModel):
    customer_unique_id: str = Field(..., description="Stable customer identity across orders")
    customer_city: Optional[str] = Field(None, description="City")
    customer_state: Optional[str] = Field(None, description="State / Province")
    customer_country: Optional[str] = Field("BR", description="Country")


class CustomerCreate(CustomerBase):
    customer_id: str = Field(..., description="Unique customer ID")
    created_at: Optional[datetime] = Field(None, description="First-seen timestamp")


class CustomerRead(CustomerBase):
    customer_id: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CustomerWithOrders(CustomerRead):
    orders: List[OrderRead] = []


class CustomerListResponse(BaseModel):
    items: List[CustomerRead]
    total: int
    page: int = 1
    page_size: int = 50


# ---------------------------------------------------------------------------
# Data Quality & Ingestion Schemas
# ---------------------------------------------------------------------------

class ValidationIssue(BaseModel):
    field: str
    issue_type: str
    severity: str = Field("warning", description="'error' or 'warning'")
    count: int
    sample_ids: List[str] = []
    message: str


class ValidationReport(BaseModel):
    dataset_name: str
    total_records: int
    valid_records: int
    invalid_records: int
    is_valid: bool
    issues: List[ValidationIssue] = []


class IngestionStats(BaseModel):
    dataset: str
    rows_processed: int
    rows_inserted: int
    rows_skipped: int = 0
    duration_seconds: float
    validation_report: Optional[ValidationReport] = None


class UploadResponse(BaseModel):
    status: str
    message: str
    stats: Dict[str, IngestionStats] = {}


class DataSummaryResponse(BaseModel):
    total_customers: int
    total_orders: int
    unique_customer_identities: int
    total_revenue: float
    earliest_order_date: Optional[datetime] = None
    latest_order_date: Optional[datetime] = None
    status: str = "ok"


# ---------------------------------------------------------------------------
# Analytics Schemas
# ---------------------------------------------------------------------------

class RFMScoreSchema(BaseModel):
    recency: int
    frequency: int
    monetary: int


class SegmentOverviewSchema(BaseModel):
    key: str
    name: str
    description: str
    customer_count: int
    avg_revenue: float
    rfm_code: str


class RFMResponse(BaseModel):
    segments: list[SegmentOverviewSchema]
    segment_distribution: Dict[str, int]
    reference_date: str


class CLVResponse(BaseModel):
    total_customers_with_orders: int
    average_clv: float
    median_clv: float
    top_10_percent_clv: float


class RetentionCurveEntry(BaseModel):
    cohort_month: str
    month_offset: int
    active_customers: int
    cohort_size: int
    retention: float


class CohortMatrixEntry(BaseModel):
    cohort_month: str
    cohort_size: int
    # Dynamic month columns (0, 1, 2, ...)
    model_config = ConfigDict(extra="allow")


class RetentionResponse(BaseModel):
    repeat_purchase_rate: float
    total_customers: int
    repeat_customers: int
    average_orders_per_customer: float
    one_time_buyers: int
    active_customers: int
    retention_curve: list[RetentionCurveEntry]
    cohort_matrix: list[Dict]


class HealthResponse(BaseModel):
    average_health_score: float
    median_health_score: float
    excellent_count: int
    good_count: int
    fair_count: int
    poor_count: int
    critical_count: int
    total_scored: int


class CustomerAnalyticsDetail(BaseModel):
    customer_id: str
    segment: str
    segment_key: str
    segment_description: str
    rfm_code: str
    recency_days: Optional[int]
    total_orders: int
    total_revenue: float
    avg_order_value: float
    historical_clv: float
    annual_purchase_frequency: float
    customer_lifetime_years: float
    clv_formula: str
    health_score: float
    health_label: str


class CustomersListResponse(BaseModel):
    items: List[CustomerRead]
    total: int
    page: int = 1
    page_size: int = 50
