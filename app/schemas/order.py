from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import OrderStatus


class OrderCreate(BaseModel):
    customer_id: Optional[UUID] = None
    amount: int = Field(..., gt=0)
    currency: str = "INR"
    receipt: Optional[str] = None
    notes: Optional[dict] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: str
    merchant_id: UUID
    customer_id: Optional[UUID]

    amount: int
    amount_paid: int
    amount_due: int

    currency: str
    status: OrderStatus

    receipt: Optional[str]
    notes: Optional[dict]

    created_at: datetime
    updated_at: datetime


class OrderListResponse(BaseModel):
    orders: list[OrderResponse]