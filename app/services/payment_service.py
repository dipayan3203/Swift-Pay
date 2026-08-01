import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.payment import Payment
from app.models.merchant import Merchant

from app.schemas.payment import PaymentCreate


def generate_payment_id() -> str:
    return f"pay_{secrets.token_hex(8)}"


def create_payment(
    db: Session,
    merchant: Merchant,
    payload: PaymentCreate,
):

    order = (
        db.query(Order)
        .filter(
            Order.order_id == payload.order_id,
            Order.merchant_id == merchant.id,
        )
        .first()
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    if order.amount_due == 0:
        raise HTTPException(
            status_code=400,
            detail="Order is already paid",
        )

    payment = Payment(
        payment_id=generate_payment_id(),
        merchant_id=merchant.id,
        order_id=order.id,
        amount=order.amount_due,
        currency=order.currency,
        payment_method=payload.payment_method,
        notes=payload.notes,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


def list_payments(
    db: Session,
    merchant: Merchant,
):
    return (
        db.query(Payment)
        .filter(Payment.merchant_id == merchant.id)
        .order_by(Payment.created_at.desc())
        .all()
    )


def get_payment(
    db: Session,
    merchant: Merchant,
    payment_id: str,
):

    return (
        db.query(Payment)
        .filter(
            Payment.payment_id == payment_id,
            Payment.merchant_id == merchant.id,
        )
        .first()
    )