from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import RefundStatus
from uuid import UUID


class RefundCreate(BaseModel):
    amount: int
    reason: str | None = None


class RefundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    refund_id: str
    payment_id: UUID
    amount: int
    status: RefundStatus
    reason: str | None
    created_at: datetime
    processed_at: datetime | None


class RefundListResponse(BaseModel):
    refunds: list[RefundResponse]