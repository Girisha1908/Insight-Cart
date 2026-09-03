"""Customer and Order Data Validation Service.

Validates data quality, missing values, duplicates, bad foreign keys,
and invalid dates/amounts before database insertion.
"""

from datetime import datetime, timezone
from typing import Optional, Set
import numpy as np
import pandas as pd

from app.schemas.customer import ValidationIssue, ValidationReport


class CustomerOrderValidator:
    """Performs validation checks on customer and order dataframes."""

    @staticmethod
    def validate_customers_df(df: pd.DataFrame) -> ValidationReport:
        """Validate customers DataFrame and generate a detailed report."""
        issues = []
        total_records = len(df)
        invalid_mask = pd.Series(False, index=df.index)

        # 1. Missing customer_id
        if "customer_id" not in df.columns:
            issues.append(
                ValidationIssue(
                    field="customer_id",
                    issue_type="missing_column",
                    severity="error",
                    count=total_records,
                    sample_ids=[],
                    message="Missing required column 'customer_id'",
                )
            )
            return ValidationReport(
                dataset_name="customers",
                total_records=total_records,
                valid_records=0,
                invalid_records=total_records,
                is_valid=False,
                issues=issues,
            )

        missing_cust_id = df["customer_id"].isna() | (df["customer_id"].astype(str).str.strip() == "")
        count_missing_id = int(missing_cust_id.sum())
        if count_missing_id > 0:
            invalid_mask |= missing_cust_id
            issues.append(
                ValidationIssue(
                    field="customer_id",
                    issue_type="null_or_empty",
                    severity="error",
                    count=count_missing_id,
                    sample_ids=[],
                    message=f"{count_missing_id} customer records have missing or empty customer_id",
                )
            )

        # 2. Missing customer_unique_id
        if "customer_unique_id" in df.columns:
            missing_uniq = df["customer_unique_id"].isna() | (df["customer_unique_id"].astype(str).str.strip() == "")
            count_missing_uniq = int(missing_uniq.sum())
            if count_missing_uniq > 0:
                invalid_mask |= missing_uniq
                sample = df[missing_uniq]["customer_id"].dropna().astype(str).head(5).tolist()
                issues.append(
                    ValidationIssue(
                        field="customer_unique_id",
                        issue_type="null_or_empty",
                        severity="error",
                        count=count_missing_uniq,
                        sample_ids=sample,
                        message=f"{count_missing_uniq} records missing stable customer_unique_id",
                    )
                )

        # 3. Duplicate customer_id
        dup_cust_mask = df.duplicated(subset=["customer_id"], keep=False) & ~missing_cust_id
        count_dup = int(dup_cust_mask.sum())
        if count_dup > 0:
            invalid_mask |= dup_cust_mask
            sample = df[dup_cust_mask]["customer_id"].astype(str).head(5).tolist()
            issues.append(
                ValidationIssue(
                    field="customer_id",
                    issue_type="duplicate",
                    severity="error",
                    count=count_dup,
                    sample_ids=sample,
                    message=f"{count_dup} duplicate customer_id records detected",
                )
            )

        # 4. Missing Geographic Information (Warning level)
        for col in ["customer_city", "customer_state"]:
            if col in df.columns:
                missing_geo = df[col].isna() | (df[col].astype(str).str.strip() == "")
                count_missing_geo = int(missing_geo.sum())
                if count_missing_geo > 0:
                    sample = df[missing_geo]["customer_id"].dropna().astype(str).head(5).tolist()
                    issues.append(
                        ValidationIssue(
                            field=col,
                            issue_type="missing_optional_field",
                            severity="warning",
                            count=count_missing_geo,
                            sample_ids=sample,
                            message=f"{count_missing_geo} records have missing {col}",
                        )
                    )

        invalid_records = int(invalid_mask.sum())
        valid_records = total_records - invalid_records
        has_errors = any(issue.severity == "error" for issue in issues)

        return ValidationReport(
            dataset_name="customers",
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=invalid_records,
            is_valid=not has_errors,
            issues=issues,
        )

    @staticmethod
    def validate_orders_df(
        df: pd.DataFrame, known_customer_ids: Optional[Set[str]] = None
    ) -> ValidationReport:
        """Validate orders DataFrame and generate a detailed report."""
        issues = []
        total_records = len(df)
        invalid_mask = pd.Series(False, index=df.index)

        # 1. Required columns
        if "order_id" not in df.columns or "customer_id" not in df.columns:
            issues.append(
                ValidationIssue(
                    field="order_id/customer_id",
                    issue_type="missing_columns",
                    severity="error",
                    count=total_records,
                    sample_ids=[],
                    message="Missing required columns 'order_id' or 'customer_id'",
                )
            )
            return ValidationReport(
                dataset_name="orders",
                total_records=total_records,
                valid_records=0,
                invalid_records=total_records,
                is_valid=False,
                issues=issues,
            )

        # 2. Null or empty order_id
        missing_order_id = df["order_id"].isna() | (df["order_id"].astype(str).str.strip() == "")
        count_missing_order_id = int(missing_order_id.sum())
        if count_missing_order_id > 0:
            invalid_mask |= missing_order_id
            issues.append(
                ValidationIssue(
                    field="order_id",
                    issue_type="null_or_empty",
                    severity="error",
                    count=count_missing_order_id,
                    sample_ids=[],
                    message=f"{count_missing_order_id} records missing order_id",
                )
            )

        # 3. Null or empty customer_id
        missing_cust_ref = df["customer_id"].isna() | (df["customer_id"].astype(str).str.strip() == "")
        count_missing_cust = int(missing_cust_ref.sum())
        if count_missing_cust > 0:
            invalid_mask |= missing_cust_ref
            sample = df[missing_cust_ref]["order_id"].dropna().astype(str).head(5).tolist()
            issues.append(
                ValidationIssue(
                    field="customer_id",
                    issue_type="null_or_empty",
                    severity="error",
                    count=count_missing_cust,
                    sample_ids=sample,
                    message=f"{count_missing_cust} orders have no associated customer_id",
                )
            )

        # 4. Duplicate order_id
        dup_orders = df.duplicated(subset=["order_id"], keep=False) & ~missing_order_id
        count_dup_orders = int(dup_orders.sum())
        if count_dup_orders > 0:
            invalid_mask |= dup_orders
            sample = df[dup_orders]["order_id"].astype(str).head(5).tolist()
            issues.append(
                ValidationIssue(
                    field="order_id",
                    issue_type="duplicate",
                    severity="error",
                    count=count_dup_orders,
                    sample_ids=sample,
                    message=f"{count_dup_orders} duplicate order_id records found",
                )
            )

        # 5. Invalid/Negative Order Values
        if "order_value" in df.columns:
            numeric_vals = pd.to_numeric(df["order_value"], errors="coerce")
            negative_vals = numeric_vals < 0
            count_neg = int(negative_vals.sum())
            if count_neg > 0:
                invalid_mask |= negative_vals
                sample = df[negative_vals]["order_id"].dropna().astype(str).head(5).tolist()
                issues.append(
                    ValidationIssue(
                        field="order_value",
                        issue_type="negative_value",
                        severity="error",
                        count=count_neg,
                        sample_ids=sample,
                        message=f"{count_neg} orders have negative order_value",
                    )
                )

        # 6. Invalid Dates
        date_col = "order_date" if "order_date" in df.columns else (
            "order_purchase_timestamp" if "order_purchase_timestamp" in df.columns else None
        )
        if date_col:
            parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
            nat_dates = parsed_dates.isna() & df[date_col].notna()
            count_unparseable = int(nat_dates.sum())
            if count_unparseable > 0:
                invalid_mask |= nat_dates
                sample = df[nat_dates]["order_id"].dropna().astype(str).head(5).tolist()
                issues.append(
                    ValidationIssue(
                        field=date_col,
                        issue_type="invalid_date_format",
                        severity="error",
                        count=count_unparseable,
                        sample_ids=sample,
                        message=f"{count_unparseable} orders have unparseable dates in {date_col}",
                    )
                )

            # Check future dates (> next year) or pre-2000
            current_year = datetime.now(timezone.utc).year + 1
            out_of_bounds = (parsed_dates.dt.year > current_year) | (parsed_dates.dt.year < 2000)
            count_oob = int(out_of_bounds.sum())
            if count_oob > 0:
                sample = df[out_of_bounds]["order_id"].dropna().astype(str).head(5).tolist()
                issues.append(
                    ValidationIssue(
                        field=date_col,
                        issue_type="date_out_of_range",
                        severity="warning",
                        count=count_oob,
                        sample_ids=sample,
                        message=f"{count_oob} orders have dates outside standard range (2000-{current_year})",
                    )
                )

        # 7. Orphan Orders (customer_id not in known customers)
        if known_customer_ids is not None and len(known_customer_ids) > 0:
            valid_cust = df["customer_id"].isin(known_customer_ids) | missing_cust_ref
            orphan_mask = ~valid_cust
            count_orphans = int(orphan_mask.sum())
            if count_orphans > 0:
                invalid_mask |= orphan_mask
                sample = df[orphan_mask]["order_id"].dropna().astype(str).head(5).tolist()
                issues.append(
                    ValidationIssue(
                        field="customer_id",
                        issue_type="foreign_key_violation",
                        severity="error",
                        count=count_orphans,
                        sample_ids=sample,
                        message=f"{count_orphans} orders reference unknown customer_id values",
                    )
                )

        invalid_records = int(invalid_mask.sum())
        valid_records = total_records - invalid_records
        has_errors = any(issue.severity == "error" for issue in issues)

        return ValidationReport(
            dataset_name="orders",
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=invalid_records,
            is_valid=not has_errors,
            issues=issues,
        )
