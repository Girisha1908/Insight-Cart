"""Customer and Order Ingestion Service.

Reads canonical or Olist-formatted CSV files, runs validation,
transforms columns, and loads data into PostgreSQL / database.
"""

import io
from datetime import datetime, timezone
import time
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Set, Union

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.order import Order
from app.schemas.customer import IngestionStats, ValidationReport
from app.services.validation.customer_validator import CustomerOrderValidator


class CustomerOrderIngestionService:
    """Handles parsing, transformation, and database ingestion for customers and orders."""

    def __init__(self, db: Session):
        self.db = db
        self.validator = CustomerOrderValidator()

    @staticmethod
    def load_dataframe_from_source(source: Union[str, Path, bytes, BinaryIO, pd.DataFrame]) -> pd.DataFrame:
        """Convert various input types into a pandas DataFrame."""
        if isinstance(source, pd.DataFrame):
            return source.copy()
        if isinstance(source, bytes):
            return pd.read_csv(io.BytesIO(source))
        if hasattr(source, "read"):
            # File-like object
            return pd.read_csv(source)
        # String or Path
        return pd.read_csv(str(source))

    @staticmethod
    def normalize_customers_df(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and values for Customer entity."""
        df = df.copy()
        col_map = {
            "customerId": "customer_id",
            "customer_id": "customer_id",
            "customerUniqueId": "customer_unique_id",
            "customer_unique_id": "customer_unique_id",
            "customerCity": "customer_city",
            "customer_city": "customer_city",
            "customerState": "customer_state",
            "customer_state": "customer_state",
            "customerCountry": "customer_country",
            "customer_country": "customer_country",
            "createdAt": "created_at",
            "created_at": "created_at",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

        if "customer_id" in df.columns:
            df["customer_id"] = df["customer_id"].astype(str).str.strip()
        if "customer_unique_id" in df.columns:
            df["customer_unique_id"] = df["customer_unique_id"].astype(str).str.strip()
        elif "customer_id" in df.columns:
            df["customer_unique_id"] = df["customer_id"]

        if "customer_country" not in df.columns:
            df["customer_country"] = "BR"
        else:
            df["customer_country"] = df["customer_country"].fillna("BR")

        if "customer_city" in df.columns:
            df["customer_city"] = df["customer_city"].astype(str).str.strip().replace("nan", None)
        else:
            df["customer_city"] = None

        if "customer_state" in df.columns:
            df["customer_state"] = df["customer_state"].astype(str).str.strip().replace("nan", None)
        else:
            df["customer_state"] = None

        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        else:
            df["created_at"] = None

        # Keep only columns belonging to the Customer entity; drop source-only
        # extras (e.g. customer_zip_code_prefix) that are not on the model.
        _entity_cols = {
            "customer_id",
            "customer_unique_id",
            "customer_city",
            "customer_state",
            "customer_country",
            "created_at",
        }
        df = df[[c for c in _entity_cols if c in df.columns]]

        # Deduplicate on customer_id keeping first
        df = df.dropna(subset=["customer_id"])
        df = df[df["customer_id"] != ""]
        df = df.drop_duplicates(subset=["customer_id"], keep="first")
        return df

    @staticmethod
    def normalize_orders_df(
        df: pd.DataFrame, payments_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Normalize column names and calculate order values."""
        df = df.copy()
        col_map = {
            "orderId": "order_id",
            "order_id": "order_id",
            "customerId": "customer_id",
            "customer_id": "customer_id",
            "order_purchase_timestamp": "order_date",
            "purchase_date": "order_date",
            "orderDate": "order_date",
            "order_date": "order_date",
            "order_status": "order_status",
            "orderStatus": "order_status",
            "status": "order_status",
            "order_value": "order_value",
            "orderValue": "order_value",
            "payment_value": "order_value",
            "amount": "order_value",
            "price": "order_value",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

        if "order_id" in df.columns:
            df["order_id"] = df["order_id"].astype(str).str.strip()
        if "customer_id" in df.columns:
            df["customer_id"] = df["customer_id"].astype(str).str.strip()

        # Handle payments aggregation if provided and order_value is missing
        if ("order_value" not in df.columns or df["order_value"].isna().all()) and payments_df is not None:
            pay_norm = payments_df.copy()
            if "order_id" in pay_norm.columns and "payment_value" in pay_norm.columns:
                pay_norm["payment_value"] = pd.to_numeric(pay_norm["payment_value"], errors="coerce").fillna(0)
                order_totals = pay_norm.groupby("order_id")["payment_value"].sum().reset_index()
                order_totals.columns = ["order_id", "order_value"]
                df = df.merge(order_totals, on="order_id", how="left")

        if "order_value" not in df.columns:
            df["order_value"] = 0.0
        else:
            df["order_value"] = pd.to_numeric(df["order_value"], errors="coerce").fillna(0.0)
            df["order_value"] = df["order_value"].clip(lower=0.0)

        if "order_date" in df.columns:
            df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        else:
            df["order_date"] = datetime.now(timezone.utc)

        if "order_status" not in df.columns:
            df["order_status"] = "delivered"
        else:
            df["order_status"] = df["order_status"].astype(str).str.strip().replace("nan", "delivered")

        # Keep only columns belonging to the Order entity; drop source-only
        # extras (e.g. order_approved_at, order_delivered_*) not on the model.
        _entity_cols = {
            "order_id",
            "customer_id",
            "order_date",
            "order_status",
            "order_value",
        }
        df = df[[c for c in _entity_cols if c in df.columns]]

        # Deduplicate on order_id
        df = df.dropna(subset=["order_id", "customer_id"])
        df = df[(df["order_id"] != "") & (df["customer_id"] != "")]
        df = df.drop_duplicates(subset=["order_id"], keep="first")
        return df

    def ingest_customers(
        self,
        source: Union[str, Path, bytes, BinaryIO, pd.DataFrame],
        batch_size: int = 1000,
    ) -> IngestionStats:
        """Validate, normalize, and bulk ingest customers into the database."""
        start_time = time.time()
        raw_df = self.load_dataframe_from_source(source)
        total_raw = len(raw_df)

        validation_report = self.validator.validate_customers_df(raw_df)
        df = self.normalize_customers_df(raw_df)

        inserted_count = 0
        bind_dialect = self.db.bind.dialect.name if self.db.bind else "postgresql"

        records: list[dict[str, Any]] = df.to_dict(orient="records")
        for i in range(0, len(records), batch_size):
            batch: list[dict[str, Any]] = records[i : i + batch_size]
            # Replace NaT / NaN with None
            for row in batch:
                for k, v in list(row.items()):
                    if pd.isna(v):
                        row[k] = None

            if bind_dialect == "postgresql":
                stmt = pg_insert(Customer).values(batch)
                stmt = stmt.on_conflict_do_update(
                    index_elements=[Customer.customer_id],
                    set_={
                        "customer_unique_id": stmt.excluded.customer_unique_id,
                        "customer_city": stmt.excluded.customer_city,
                        "customer_state": stmt.excluded.customer_state,
                        "customer_country": stmt.excluded.customer_country,
                    },
                )
                self.db.execute(stmt)
            elif bind_dialect == "sqlite":
                stmt = sqlite_insert(Customer).values(batch)
                stmt = stmt.on_conflict_do_update(
                    index_elements=[Customer.customer_id],
                    set_={
                        "customer_unique_id": stmt.excluded.customer_unique_id,
                        "customer_city": stmt.excluded.customer_city,
                        "customer_state": stmt.excluded.customer_state,
                        "customer_country": stmt.excluded.customer_country,
                    },
                )
                self.db.execute(stmt)
            else:
                # Fallback for generic dialect
                for row in batch:
                    existing = self.db.get(Customer, row["customer_id"])
                    if existing:
                        existing.customer_unique_id = row["customer_unique_id"]
                        existing.customer_city = row["customer_city"]
                        existing.customer_state = row["customer_state"]
                        existing.customer_country = row["customer_country"]
                    else:
                        self.db.add(Customer(**row))

            self.db.commit()
            inserted_count += len(batch)

        duration = round(time.time() - start_time, 3)
        return IngestionStats(
            dataset="customers",
            rows_processed=total_raw,
            rows_inserted=inserted_count,
            rows_skipped=total_raw - len(df),
            duration_seconds=duration,
            validation_report=validation_report,
        )

    def ingest_orders(
        self,
        orders_source: Union[str, Path, bytes, BinaryIO, pd.DataFrame],
        payments_source: Optional[Union[str, Path, bytes, BinaryIO, pd.DataFrame]] = None,
        batch_size: int = 1000,
    ) -> IngestionStats:
        """Validate, normalize, and bulk ingest orders into the database."""
        start_time = time.time()
        raw_orders_df = self.load_dataframe_from_source(orders_source)
        payments_df = (
            self.load_dataframe_from_source(payments_source)
            if payments_source is not None
            else None
        )
        total_raw = len(raw_orders_df)

        # Get existing customer IDs to validate foreign keys
        known_customers = set(self.db.scalars(select(Customer.customer_id)).all())
        validation_report = self.validator.validate_orders_df(raw_orders_df, known_customers)

        df = self.normalize_orders_df(raw_orders_df, payments_df)

        # Filter orders to only known customers if customers exist in DB
        if len(known_customers) > 0:
            df = df[df["customer_id"].isin(known_customers)]

        inserted_count = 0
        bind_dialect = self.db.bind.dialect.name if self.db.bind else "postgresql"

        records: list[dict[str, Any]] = df.to_dict(orient="records")
        for i in range(0, len(records), batch_size):
            batch: list[dict[str, Any]] = records[i : i + batch_size]
            for row in batch:
                for k, v in list(row.items()):
                    if pd.isna(v):
                        row[k] = None

            if bind_dialect == "postgresql":
                stmt = pg_insert(Order).values(batch)
                stmt = stmt.on_conflict_do_update(
                    index_elements=[Order.order_id],
                    set_={
                        "order_date": stmt.excluded.order_date,
                        "order_status": stmt.excluded.order_status,
                        "order_value": stmt.excluded.order_value,
                    },
                )
                self.db.execute(stmt)
            elif bind_dialect == "sqlite":
                stmt = sqlite_insert(Order).values(batch)
                stmt = stmt.on_conflict_do_update(
                    index_elements=[Order.order_id],
                    set_={
                        "order_date": stmt.excluded.order_date,
                        "order_status": stmt.excluded.order_status,
                        "order_value": stmt.excluded.order_value,
                    },
                )
                self.db.execute(stmt)
            else:
                for row in batch:
                    existing = self.db.get(Order, row["order_id"])
                    if existing:
                        existing.order_date = row["order_date"]
                        existing.order_status = row["order_status"]
                        existing.order_value = row["order_value"]
                    else:
                        self.db.add(Order(**row))

            self.db.commit()
            inserted_count += len(batch)

        # Update customer created_at based on their earliest order date if not set
        self._backfill_customer_created_at()

        duration = round(time.time() - start_time, 3)
        return IngestionStats(
            dataset="orders",
            rows_processed=total_raw,
            rows_inserted=inserted_count,
            rows_skipped=total_raw - len(df),
            duration_seconds=duration,
            validation_report=validation_report,
        )

    def _backfill_customer_created_at(self) -> None:
        """Update customer created_at with their earliest order timestamp where null."""
        try:
            # Query earliest order date per customer
            query = (
                select(Order.customer_id, Order.order_date)
                .where(Order.order_date.isnot(None))
                .order_by(Order.customer_id, Order.order_date.asc())
            )
            order_rows = self.db.execute(query).all()
            earliest_dates: Dict[str, datetime] = {}
            for cust_id, o_date in order_rows:
                if cust_id not in earliest_dates and o_date is not None:
                    earliest_dates[cust_id] = o_date

            if earliest_dates:
                customers_to_update = (
                    self.db.query(Customer)
                    .filter(Customer.customer_id.in_(list(earliest_dates.keys())))
                    .all()
                )
                for cust in customers_to_update:
                    if cust.created_at is None and cust.customer_id in earliest_dates:
                        cust.created_at = earliest_dates[cust.customer_id]
                self.db.commit()
        except Exception:
            self.db.rollback()

    def ingest_olist_bundle(
        self,
        raw_dir: Union[str, Path] = "data/demo/olist/raw",
        limit_rows: Optional[int] = None,
    ) -> Dict[str, IngestionStats]:
        """Ingest the complete Olist customer + order dataset from a directory."""
        raw_path = Path(raw_dir)
        if not raw_path.exists():
            # Fallback to data/raw
            raw_path = Path("data/raw")
            if not raw_path.exists():
                raise FileNotFoundError(f"Data directory not found: {raw_dir} or data/raw")

        # Find customer CSV
        cust_candidates = [
            raw_path / "olist_customers_dataset.csv",
            raw_path / "customers.csv",
        ]
        cust_file = next((p for p in cust_candidates if p.exists()), None)
        if not cust_file:
            raise FileNotFoundError("Customer dataset CSV not found.")

        # Find order CSV
        order_candidates = [
            raw_path / "olist_orders_dataset.csv",
            raw_path / "orders.csv",
        ]
        order_file = next((p for p in order_candidates if p.exists()), None)
        if not order_file:
            raise FileNotFoundError("Orders dataset CSV not found.")

        # Find payments CSV
        pay_candidates = [
            raw_path / "olist_order_payments_dataset.csv",
            raw_path / "payments.csv",
        ]
        pay_file = next((p for p in pay_candidates if p.exists()), None)

        # Read customers
        cust_df = pd.read_csv(cust_file, nrows=limit_rows)
        cust_stats = self.ingest_customers(cust_df)

        # Read orders & payments
        order_df = pd.read_csv(order_file, nrows=limit_rows)
        pay_df = pd.read_csv(pay_file, nrows=limit_rows) if pay_file else None
        order_stats = self.ingest_orders(order_df, pay_df)

        return {
            "customers": cust_stats,
            "orders": order_stats,
        }
