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


# ---------------------------------------------------------------------------
# Phase 3 — ML Schemas
# ---------------------------------------------------------------------------

class ChurnPredictionSchema(BaseModel):
    """Churn prediction for a single customer."""
    customer_id: str
    churn_probability: float = Field(..., description="Probability of churn (0-1)")
    churned: bool = Field(..., description="Binary churn prediction")
    risk_level: str = Field(..., description="Human-friendly risk level")
    summary: str = Field(..., description="One-line human-friendly summary")
    recommended_action: str = Field(..., description="Suggested non-causal action")
    model_used: str = Field("", description="Name of the ML model used")
    features_used: List[str] = Field(default_factory=list)


class NextPurchasePredictionSchema(BaseModel):
    """Next-purchase prediction for a single customer."""
    customer_id: str
    last_order_date: Optional[str] = None
    total_orders: int = 0
    predicted_days_to_next_purchase: float = 0.0
    predicted_next_purchase_date: Optional[str] = None
    model_used: str = "statistical_baseline"
    confidence_note: str = ""


class RecommendationItem(BaseModel):
    type: str = Field(..., description="Recommendation category")
    title: str = Field(..., description="Short title")
    action: str = Field(..., description="Human-friendly recommended action")


class Customer360Response(BaseModel):
    """Full 360-degree customer view: analytics + ML predictions + recommendations."""
    customer_id: str
    segment: str
    segment_key: str
    segment_description: str
    rfm_code: str
    recency_days: Optional[int] = None
    total_orders: int
    total_revenue: float
    avg_order_value: float
    historical_clv: float
    clv_formula: str
    health_score: float
    health_label: str
    churn_prediction: Optional[ChurnPredictionSchema] = None
    next_purchase_prediction: Optional[NextPurchasePredictionSchema] = None
    recommendations: List[RecommendationItem] = Field(default_factory=list)


class CustomerChurnResponse(BaseModel):
    """Churn prediction endpoint response."""
    customer_id: str
    status: Optional[str] = None
    churn_probability: Optional[float] = None
    churned: Optional[bool] = None
    risk_level: Optional[str] = None
    summary: Optional[str] = None
    recommended_action: Optional[str] = None
    model_used: Optional[str] = None
    features_used: List[str] = Field(default_factory=list)


class CustomerRecommendationResponse(BaseModel):
    """Recommendation endpoint response."""
    customer_id: str
    segment: str
    health_label: str
    recommendations: List[RecommendationItem]


class NextPurchaseResponse(BaseModel):
    """Next-purchase prediction endpoint response."""
    customer_id: str
    status: Optional[str] = None
    last_order_date: Optional[str] = None
    total_orders: int = 0
    predicted_days_to_next_purchase: Optional[float] = None
    predicted_next_purchase_date: Optional[str] = None
    model_used: Optional[str] = None
    confidence_note: Optional[str] = None
    summary: Optional[str] = None
