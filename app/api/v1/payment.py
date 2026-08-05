from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_merchant
from app.database.session import get_db

from app.models.merchant import Merchant

from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentListResponse,
)

from app.services.payment_service import (
    create_payment,
    list_payments,
    get_payment,
    capture_payment,
)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "",
    response_model=PaymentResponse,
)
def create_payment_endpoint(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    return create_payment(
        db=db,
        merchant=merchant,
        payload=payload,
    )


@router.get(
    "",
    response_model=PaymentListResponse,
)
def list_payments_endpoint(
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    return {
        "payments": list_payments(
            db=db,
            merchant=merchant,
        )
    }


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
)
def get_payment_endpoint(
    payment_id: str,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    payment = get_payment(
        db=db,
        merchant=merchant,
        payment_id=payment_id,
    )

    if payment is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return payment
@router.post(
    "/{payment_id}/capture",
    response_model=PaymentResponse,
)
def capture_payment_endpoint(
    payment_id: str,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    return capture_payment(
        db=db,
        merchant=merchant,
        payment_id=payment_id,
    )