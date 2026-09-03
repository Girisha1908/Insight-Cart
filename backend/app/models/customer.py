"""Customer SQLAlchemy model.

Part of Developer 1 (Customer Intelligence) vertical.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.order import Order


class Customer(Base):
    """Canonical Customer entity."""

    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, index=True, doc="Unique customer identifier"
    )
    customer_unique_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
        doc="Stable customer identity across orders",
    )
    customer_city: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, doc="Customer city"
    )
    customer_state: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, doc="Customer state/province"
    )
    customer_country: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, default="BR", doc="Customer country"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=func.now(),
        doc="First-seen timestamp",
    )

    # Relationships
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="customer",
        cascade="all, delete, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Customer(customer_id='{self.customer_id}', "
            f"customer_unique_id='{self.customer_unique_id}', "
            f"city='{self.customer_city}', state='{self.customer_state}')>"
        )
