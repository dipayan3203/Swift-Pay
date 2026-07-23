from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.auth import MerchantRegister, MerchantLogin
from app.services.auth_service import (
    register_merchant,
    authenticate_merchant,
)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
def register(
    merchant: MerchantRegister,
    db: Session = Depends(get_db),
):
    try:
        new_merchant = register_merchant(db, merchant)

        return {
            "message": "Merchant registered successfully",
            "merchant_id": str(new_merchant.id),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
@router.post("/login")
def login(
    credentials: MerchantLogin,
    db: Session = Depends(get_db),
):
    try:
        return authenticate_merchant(
            db,
            credentials.email,
            credentials.password,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
        )    