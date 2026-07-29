import secrets

from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.merchant import Merchant
from app.schemas.order import OrderCreate


def generate_order_id() -> str:
    return f"order_{secrets.token_hex(8)}"


def create_order(
    db: Session,
    merchant: Merchant,
    payload: OrderCreate,
) -> Order:

    order = Order(
        merchant_id=merchant.id,
        customer_id=payload.customer_id,
        order_id=generate_order_id(),
        amount=payload.amount,
        amount_paid=0,
        amount_due=payload.amount,
        currency=payload.currency,
        receipt=payload.receipt,
        notes=payload.notes,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def list_orders(
    db: Session,
    merchant: Merchant,
):
    return (
        db.query(Order)
        .filter(Order.merchant_id == merchant.id)
        .order_by(Order.created_at.desc())
        .all()
    )


def get_order(
    db: Session,
    merchant: Merchant,
    order_id: str,
):

    return (
        db.query(Order)
        .filter(
            Order.order_id == order_id,
            Order.merchant_id == merchant.id,
        )
        .first()
    )