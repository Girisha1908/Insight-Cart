from datetime import datetime, timezone
from decimal import Decimal
import io
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.database import get_db
from app.main import app
from app.models.customer import Customer
from app.models.order import Order
from app.schemas.customer import (
    CustomerCreate,
    CustomerRead,
    CustomerWithOrders,
    OrderCreate,
    OrderRead,
    ValidationReport,
)
from app.services.ingestion.customer_ingestion import CustomerOrderIngestionService
from app.services.validation.customer_validator import CustomerOrderValidator


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Test Fixtures: In-Memory SQLite Database
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    """Create an isolated in-memory SQLite database session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create a FastAPI TestClient with the test database session overridden."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. Models & Relationships Tests
# ---------------------------------------------------------------------------

def test_customer_model_creation_and_repr(db_session):
    customer = Customer(
        customer_id="cust_001",
        customer_unique_id="uniq_001",
        customer_city="Sao Paulo",
        customer_state="SP",
        customer_country="BR",
    )
    db_session.add(customer)
    db_session.commit()

    saved = db_session.get(Customer, "cust_001")
    assert saved is not None
    assert saved.customer_unique_id == "uniq_001"
    assert saved.customer_city == "Sao Paulo"
    assert saved.customer_state == "SP"
    assert "cust_001" in repr(saved)


def test_order_model_and_relationship(db_session):
    customer = Customer(
        customer_id="cust_002",
        customer_unique_id="uniq_002",
        customer_city="Rio de Janeiro",
        customer_state="RJ",
    )
    db_session.add(customer)
    db_session.commit()

    now = datetime.now(timezone.utc)
    order = Order(
        order_id="ord_001",
        customer_id="cust_002",
        order_date=now,
        order_status="delivered",
        order_value=150.75,
    )
    db_session.add(order)
    db_session.commit()

    saved_order = db_session.get(Order, "ord_001")
    assert saved_order is not None
    assert saved_order.customer.customer_id == "cust_002"
    assert float(saved_order.order_value) == 150.75

    # Check relationship from customer side
    saved_cust = db_session.get(Customer, "cust_002")
    assert len(saved_cust.orders) == 1
    assert saved_cust.orders[0].order_id == "ord_001"


def test_customer_cascade_delete(db_session):
    customer = Customer(customer_id="cust_003", customer_unique_id="uniq_003")
    order = Order(order_id="ord_002", customer_id="cust_003", order_value=50.0)
    db_session.add(customer)
    db_session.add(order)
    db_session.commit()

    # Deleting customer should cascade to order
    db_session.delete(customer)
    db_session.commit()

    assert db_session.get(Customer, "cust_003") is None
    assert db_session.get(Order, "ord_002") is None


# ---------------------------------------------------------------------------
# 2. Pydantic Schemas Tests
# ---------------------------------------------------------------------------

def test_customer_pydantic_schemas():
    data = {
        "customer_id": "c1",
        "customer_unique_id": "u1",
        "customer_city": "Campinas",
        "customer_state": "SP",
        "customer_country": "BR",
        "created_at": datetime(2023, 1, 15, 10, 0, 0),
    }
    schema = CustomerCreate(**data)
    assert schema.customer_id == "c1"

    read_schema = CustomerRead.model_validate(data)
    assert read_schema.customer_city == "Campinas"


def test_order_pydantic_schemas():
    data = {
        "order_id": "o1",
        "customer_id": "c1",
        "order_date": datetime(2023, 1, 15, 12, 0, 0),
        "order_status": "delivered",
        "order_value": Decimal("99.99"),
    }
    order_create = OrderCreate(**data)
    assert order_create.order_id == "o1"
    assert order_create.order_value == Decimal("99.99")


# ---------------------------------------------------------------------------
# 3. Validation Service Tests
# ---------------------------------------------------------------------------

def test_customer_validator_valid_data():
    df = pd.DataFrame([
        {"customer_id": "c1", "customer_unique_id": "u1", "customer_city": "City A", "customer_state": "SP"},
        {"customer_id": "c2", "customer_unique_id": "u2", "customer_city": "City B", "customer_state": "RJ"},
    ])
    report = CustomerOrderValidator.validate_customers_df(df)
    assert report.is_valid is True
    assert report.total_records == 2
    assert report.valid_records == 2
    assert report.invalid_records == 0


def test_customer_validator_missing_and_duplicate_ids():
    df = pd.DataFrame([
        {"customer_id": "c1", "customer_unique_id": "u1"},
        {"customer_id": "c1", "customer_unique_id": "u1"},  # Duplicate
        {"customer_id": "", "customer_unique_id": "u3"},    # Empty ID
        {"customer_id": "c4", "customer_unique_id": ""},    # Empty unique ID
    ])
    report = CustomerOrderValidator.validate_customers_df(df)
    assert report.is_valid is False
    assert report.total_records == 4
    issue_types = [issue.issue_type for issue in report.issues]
    assert "duplicate" in issue_types
    assert "null_or_empty" in issue_types


def test_order_validator_valid_and_invalid():
    df = pd.DataFrame([
        {"order_id": "o1", "customer_id": "c1", "order_date": "2023-01-01", "order_value": 100.0},
        {"order_id": "o2", "customer_id": "c1", "order_date": "invalid-date", "order_value": 50.0}, # Invalid date
        {"order_id": "o3", "customer_id": "c2", "order_date": "2023-01-02", "order_value": -20.0},  # Negative value
        {"order_id": "o4", "customer_id": "c_unknown", "order_date": "2023-01-03", "order_value": 10.0}, # Unknown FK
    ])
    known_customers = {"c1", "c2"}
    report = CustomerOrderValidator.validate_orders_df(df, known_customer_ids=known_customers)
    assert report.is_valid is False
    assert report.total_records == 4
    issue_types = [i.issue_type for i in report.issues]
    assert "invalid_date_format" in issue_types
    assert "negative_value" in issue_types
    assert "foreign_key_violation" in issue_types


# ---------------------------------------------------------------------------
# 4. Ingestion Service Tests
# ---------------------------------------------------------------------------

def test_ingestion_service_customers_and_orders(db_session):
    service = CustomerOrderIngestionService(db_session)

    # Ingest Customers
    cust_df = pd.DataFrame([
        {"customer_id": "cust_101", "customer_unique_id": "uniq_101", "customer_city": "Sao Paulo", "customer_state": "SP"},
        {"customer_id": "cust_102", "customer_unique_id": "uniq_102", "customer_city": "Curitiba", "customer_state": "PR"},
    ])
    cust_stats = service.ingest_customers(cust_df)
    assert cust_stats.rows_inserted == 2

    # Verify in DB
    assert db_session.get(Customer, "cust_101") is not None
    assert db_session.get(Customer, "cust_102") is not None

    # Ingest Orders with Payments
    orders_df = pd.DataFrame([
        {"order_id": "ord_101", "customer_id": "cust_101", "order_purchase_timestamp": "2023-05-10 14:30:00", "order_status": "delivered"},
        {"order_id": "ord_102", "customer_id": "cust_102", "order_purchase_timestamp": "2023-05-12 16:00:00", "order_status": "shipped"},
    ])
    payments_df = pd.DataFrame([
        {"order_id": "ord_101", "payment_value": 75.50},
        {"order_id": "ord_101", "payment_value": 24.50},  # Total 100.00
        {"order_id": "ord_102", "payment_value": 250.00},
    ])

    order_stats = service.ingest_orders(orders_df, payments_df)
    assert order_stats.rows_inserted == 2

    saved_ord101 = db_session.get(Order, "ord_101")
    assert saved_ord101 is not None
    assert float(saved_ord101.order_value) == 100.00

    # Check backfilled created_at on Customer
    saved_cust101 = db_session.get(Customer, "cust_101")
    assert saved_cust101.created_at is not None
    assert saved_cust101.created_at.year == 2023


def test_ingestion_service_from_csv_bytes(db_session):
    service = CustomerOrderIngestionService(db_session)
    csv_data = "customer_id,customer_unique_id,customer_city,customer_state\ncust_201,uniq_201,Santos,SP\n"
    stats = service.ingest_customers(csv_data.encode("utf-8"))
    assert stats.rows_inserted == 1
    assert db_session.get(Customer, "cust_201").customer_city == "Santos"


# ---------------------------------------------------------------------------
# 5. Upload API Endpoints Tests
# ---------------------------------------------------------------------------

def test_api_upload_customers(client):
    csv_content = (
        "customer_id,customer_unique_id,customer_city,customer_state\n"
        "c_api_1,u_api_1,Brasilia,DF\n"
        "c_api_2,u_api_2,Salvador,BA\n"
    )
    files = {"file": ("customers.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    data = {"dataset_type": "customers"}

    response = client.post("/api/data/upload", data=data, files=files)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "ok"
    assert "customers" in res_json["stats"]
    assert res_json["stats"]["customers"]["rows_inserted"] == 2


def test_api_upload_orders(client):
    # First upload customer
    cust_csv = "customer_id,customer_unique_id\nc_api_3,u_api_3\n"
    client.post(
        "/api/data/upload",
        data={"dataset_type": "customers"},
        files={"file": ("customers.csv", io.BytesIO(cust_csv.encode("utf-8")), "text/csv")},
    )

    # Then upload order
    ord_csv = "order_id,customer_id,order_date,order_status,order_value\no_api_1,c_api_3,2023-06-01,delivered,120.00\n"
    response = client.post(
        "/api/data/upload",
        data={"dataset_type": "orders"},
        files={"file": ("orders.csv", io.BytesIO(ord_csv.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 200
    assert response.json()["stats"]["orders"]["rows_inserted"] == 1


def test_api_upload_bundle(client):
    cust_csv = "customer_id,customer_unique_id\nc_b1,u_b1\n"
    ord_csv = "order_id,customer_id,order_date,order_status,order_value\no_b1,c_b1,2023-07-01,delivered,85.50\n"

    files = {
        "customers_file": ("customers.csv", io.BytesIO(cust_csv.encode("utf-8")), "text/csv"),
        "orders_file": ("orders.csv", io.BytesIO(ord_csv.encode("utf-8")), "text/csv"),
    }
    response = client.post("/api/data/upload/bundle", files=files)
    assert response.status_code == 200
    res_json = response.json()
    assert "customers" in res_json["stats"]
    assert "orders" in res_json["stats"]


def test_api_data_summary(client):
    # Seed data
    cust_csv = "customer_id,customer_unique_id\nc_s1,u_s1\nc_s2,u_s2\n"
    client.post(
        "/api/data/upload",
        data={"dataset_type": "customers"},
        files={"file": ("customers.csv", io.BytesIO(cust_csv.encode("utf-8")), "text/csv")},
    )
    ord_csv = "order_id,customer_id,order_date,order_status,order_value\no_s1,c_s1,2023-01-01,delivered,100.0\no_s2,c_s2,2023-02-01,delivered,200.0\n"
    client.post(
        "/api/data/upload",
        data={"dataset_type": "orders"},
        files={"file": ("orders.csv", io.BytesIO(ord_csv.encode("utf-8")), "text/csv")},
    )

    response = client.get("/api/data/summary")
    assert response.status_code == 200
    summary = response.json()
    assert summary["total_customers"] == 2
    assert summary["total_orders"] == 2
    assert summary["total_revenue"] == 300.0


def test_api_upload_health(client):
    response = client.get("/api/data/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "data-pipeline"


def test_api_system_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
