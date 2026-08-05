import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    BigInteger,
    DateTime,
    ForeignKey,
    Boolean,
    Enum,
)

from app.core.enums import PaymentStatus, PaymentMethod
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

    status: Mapped[PaymentStatus] = mapped_column(
    Enum(PaymentStatus, name="payment_status"),
    default=PaymentStatus.CREATED,
    nullable=False,
    )

    payment_method: Mapped[PaymentMethod | None] = mapped_column(
    Enum(PaymentMethod, name="payment_method"),
    nullable=True,
    )

    captured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    captured_at: Mapped[datetime | None] = mapped_column(
      DateTime(timezone=True),
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
        back_populates="payments",
    )

    order: Mapped["Order"] = relationship(
        back_populates="payments",
    )

    refunds: Mapped[list["Refund"]] = relationship(
    back_populates="payment",
    cascade="all, delete-orphan",
    )