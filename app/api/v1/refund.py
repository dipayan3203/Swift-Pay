from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_merchant
from app.database.session import get_db

from app.models.merchant import Merchant

from app.schemas.refund import (
    RefundCreate,
    RefundResponse,
    RefundListResponse,
)

from app.services.refund_service import (
    create_refund,
    list_refunds,
    get_refund,
)

router = APIRouter(
    prefix="/refunds",
    tags=["Refunds"],
)


@router.post(
    "/{payment_id}",
    response_model=RefundResponse,
)
def create_refund_endpoint(
    payment_id: str,
    payload: RefundCreate,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    return create_refund(
        db=db,
        merchant=merchant,
        payment_id=payment_id,
        payload=payload,
    )


@router.get(
    "",
    response_model=RefundListResponse,
)
def list_refunds_endpoint(
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    return {
        "refunds": list_refunds(
            db=db,
            merchant=merchant,
        )
    }


@router.get(
    "/{refund_id}",
    response_model=RefundResponse,
)
def get_refund_endpoint(
    refund_id: str,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
):
    return get_refund(
        db=db,
        merchant=merchant,
        refund_id=refund_id,
    )