from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.schemas.auth import MerchantRegister
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token


def register_merchant(db: Session, merchant: MerchantRegister):

    existing = (
        db.query(Merchant)
        .filter(Merchant.email == merchant.email)
        .first()
    )

    if existing:
        raise ValueError("Email already registered")

    new_merchant = Merchant(
        business_name=merchant.business_name,
        email=merchant.email,
        password_hash=hash_password(merchant.password),
        phone=merchant.phone,
    )

    db.add(new_merchant)
    db.commit()
    db.refresh(new_merchant)

    return new_merchant


def authenticate_merchant(db: Session, email: str, password: str):

    merchant = (
        db.query(Merchant)
        .filter(Merchant.email == email)
        .first()
    )

    if not merchant:
        raise ValueError("Invalid email or password")

    if not verify_password(password, merchant.password_hash):
        raise ValueError("Invalid email or password")

    access_token = create_access_token(
        {
            "sub": str(merchant.id),
            "email": merchant.email,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "merchant_id": str(merchant.id),
        "business_name": merchant.business_name,
    }