import secrets
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.enums import PaymentStatus, RefundStatus
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.refund import Refund
from app.schemas.refund import RefundCreate

from app.services.payment_service import get_payment


def generate_refund_id() -> str:
    return f"rfnd_{secrets.token_hex(8)}"


def create_refund(
    db: Session,
    merchant: Merchant,
    payment_id: str,
    payload: RefundCreate,
):
    payment = get_payment(
        db=db,
        merchant=merchant,
        payment_id=payment_id,
    )

    if payment.status not in (
        PaymentStatus.CAPTURED,
        PaymentStatus.PARTIALLY_REFUNDED,
    ):
        raise HTTPException(
            status_code=400,
            detail="Only captured payments can be refunded",
        )

    if payload.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Refund amount must be greater than zero",
        )

    already_refunded = (
        db.query(func.coalesce(func.sum(Refund.amount), 0))
        .filter(Refund.payment_id == payment.id)
        .scalar()
    )

    if already_refunded + payload.amount > payment.amount:
        raise HTTPException(
            status_code=400,
            detail="Refund amount exceeds captured payment amount",
        )

    refund = Refund(
        refund_id=generate_refund_id(),
        payment_id=payment.id,
        amount=payload.amount,
        reason=payload.reason,
        status=RefundStatus.PROCESSED,
        processed_at=datetime.now(timezone.utc),
    )

    db.add(refund)

    total_refunded = already_refunded + payload.amount

    if total_refunded == payment.amount:
        payment.status = PaymentStatus.REFUNDED
    else:
        payment.status = PaymentStatus.PARTIALLY_REFUNDED

    db.commit()
    db.refresh(refund)

    return refund


def list_refunds(
    db: Session,
    merchant: Merchant,
):
    return (
        db.query(Refund)
        .join(Refund.payment)
        .filter(
            Payment.merchant_id == merchant.id,
        )
        .order_by(Refund.created_at.desc())
        .all()
    )

def get_refund(
    db: Session,
    merchant: Merchant,
    refund_id: str,
):
    refund = (
        db.query(Refund)
        .join(Refund.payment)
        .filter(
            Refund.refund_id == refund_id,
            Payment.merchant_id == merchant.id,
        )
        .first()
    )

    if refund is None:
        raise HTTPException(
            status_code=404,
            detail="Refund not found",
        )

    return refund