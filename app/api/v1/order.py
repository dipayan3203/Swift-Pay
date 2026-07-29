from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_merchant

from app.models.merchant import Merchant
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderListResponse,
)

from app.services.order_service import (
    create_order,
    list_orders,
    get_order,
)

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)
@router.post("", response_model=OrderResponse)
def create_order_endpoint(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    return create_order(db, merchant, payload)
@router.get("", response_model=OrderListResponse)
def list_orders_endpoint(
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    return {
        "orders": list_orders(db, merchant)
    }
@router.get("/{order_id}", response_model=OrderResponse)
def get_order_endpoint(
    order_id: str,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):

    order = get_order(db, merchant, order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order