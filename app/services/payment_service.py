import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session


from app.models.payment import Payment
from app.models.merchant import Merchant

from app.schemas.payment import PaymentCreate
from datetime import datetime, timezone

from app.core.enums import PaymentStatus, OrderStatus
from app.models.order import Order


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
    payment = (
        db.query(Payment)
        .filter(
            Payment.payment_id == payment_id,
            Payment.merchant_id == merchant.id,
        )
        .first()
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return payment


def capture_payment(
    db: Session,
    merchant: Merchant,
    payment_id: str,
):
    # Find payment
    payment = (
        db.query(Payment)
        .filter(
            Payment.payment_id == payment_id,
            Payment.merchant_id == merchant.id,
        )
        .first()
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    if payment.captured:
        raise HTTPException(
            status_code=400,
            detail="Payment already captured",
        )

    order = (
        db.query(Order)
        .filter(Order.id == payment.order_id)
        .first()
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    # Update payment
    payment.captured = True
    payment.captured_at = datetime.now(timezone.utc)
    payment.status = PaymentStatus.CAPTURED

    # Update order
    order.amount_paid = payment.amount
    order.amount_due = 0
    order.status = OrderStatus.PAID

    db.commit()

    db.refresh(payment)

    return payment


    