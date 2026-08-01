from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PaymentCreate(BaseModel):
    order_id: str
    payment_method: str
    notes: Optional[dict] = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payment_id: str

    merchant_id: UUID
    order_id: UUID

    amount: int
    currency: str

    status: str
    payment_method: Optional[str]
    captured: bool

    notes: Optional[dict]

    created_at: datetime
    updated_at: datetime


class PaymentListResponse(BaseModel):
    payments: list[PaymentResponse]