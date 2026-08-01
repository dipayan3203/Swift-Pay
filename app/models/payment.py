import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    BigInteger,
    DateTime,
    ForeignKey,
    Boolean,
)

from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Payment(Base):
    __tablename__ = "payments"

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

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    payment_id: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        index=True,
        nullable=False,
    )

    amount: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="CREATED",
        nullable=False,
    )

    payment_method: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    captured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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

    merchant = relationship(
        "Merchant",
        back_populates="payments",
    )

    order = relationship(
        "Order",
        back_populates="payments",
    )