"""Order SQLAlchemy model.

Part of Developer 1 (Customer Intelligence) vertical.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.customer import Customer


class Order(Base):
    """Canonical Order entity."""

    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, index=True, doc="Unique order identifier"
    )
    customer_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("customers.customer_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="Reference to customer",
    )
    order_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Timestamp of purchase",
    )
    order_status: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        index=True,
        doc="Order lifecycle status (e.g. delivered, shipped, canceled)",
    )
    order_value: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        doc="Total order value/amount",
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="orders",
    )

    def __repr__(self) -> str:
        return (
            f"<Order(order_id='{self.order_id}', customer_id='{self.customer_id}', "
            f"status='{self.order_status}', value={self.order_value})>"
        )
