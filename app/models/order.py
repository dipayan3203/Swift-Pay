import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    BigInteger,
    DateTime,
    ForeignKey,
)

from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum
from app.core.enums import OrderStatus
from app.database.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
    )

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
    )

    order_id: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        nullable=False,
        index=True,
    )

    amount: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    amount_paid: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
    )

    amount_due: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
        nullable=False,
    )

    status: Mapped[OrderStatus] = mapped_column(
    Enum(OrderStatus, name="order_status"),
    default=OrderStatus.CREATED,
    nullable=False,
)

    receipt: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    notes: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    merchant: Mapped["Merchant"] = relationship(
        back_populates="orders",
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="orders",
    )