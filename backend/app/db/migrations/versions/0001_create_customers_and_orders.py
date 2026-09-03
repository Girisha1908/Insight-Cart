"""create customers and orders tables

Revision ID: 0001_create_customers_and_orders
Revises: 
Create Date: 2026-09-03 21:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_create_customers_and_orders"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create customers table
    op.create_table(
        "customers",
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("customer_unique_id", sa.String(length=64), nullable=False),
        sa.Column("customer_city", sa.String(length=128), nullable=True),
        sa.Column("customer_state", sa.String(length=32), nullable=True),
        sa.Column("customer_country", sa.String(length=64), server_default="BR", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("customer_id"),
    )
    op.create_index(op.f("ix_customers_customer_id"), "customers", ["customer_id"], unique=False)
    op.create_index(op.f("ix_customers_customer_unique_id"), "customers", ["customer_unique_id"], unique=False)

    # 2. Create orders table
    op.create_table(
        "orders",
        sa.Column("order_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("order_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("order_status", sa.String(length=32), nullable=True),
        sa.Column("order_value", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.customer_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("order_id"),
    )
    op.create_index(op.f("ix_orders_order_id"), "orders", ["order_id"], unique=False)
    op.create_index(op.f("ix_orders_customer_id"), "orders", ["customer_id"], unique=False)
    op.create_index(op.f("ix_orders_order_date"), "orders", ["order_date"], unique=False)
    op.create_index(op.f("ix_orders_order_status"), "orders", ["order_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_orders_order_status"), table_name="orders")
    op.drop_index(op.f("ix_orders_order_date"), table_name="orders")
    op.drop_index(op.f("ix_orders_customer_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_order_id"), table_name="orders")
    op.drop_table("orders")

    op.drop_index(op.f("ix_customers_customer_unique_id"), table_name="customers")
    op.drop_index(op.f("ix_customers_customer_id"), table_name="customers")
    op.drop_table("customers")
