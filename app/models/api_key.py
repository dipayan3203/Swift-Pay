import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    merchant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id"),
        nullable=False,
    )

    public_key = Column(String, unique=True, nullable=False)

    secret_key = Column(String, unique=True, nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    merchant = relationship(
    "Merchant",
    back_populates="api_keys",
)