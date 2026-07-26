from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.hashing import hash_password
from app.models.api_key import APIKey
from app.utils.key_generator import (
    generate_public_key,
    generate_secret_key,
)


def create_api_key(
    db: Session,
    merchant_id,
    environment: str = "TEST",
):
    public_key = generate_public_key(environment)
    secret_key = generate_secret_key(environment)

    hashed_secret = hash_password(secret_key)

    api_key = APIKey(
        merchant_id=merchant_id,
        public_key=public_key,
        secret_key_hash=hashed_secret,
        environment=environment,
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return {
        "id": str(api_key.id),
        "public_key": public_key,
        "secret_key": secret_key,  # Returned only once
        "environment": environment,
        "created_at": api_key.created_at,
    }


def get_api_keys(
    db: Session,
    merchant_id,
):
    return (
        db.query(APIKey)
        .filter(APIKey.merchant_id == merchant_id)
        .order_by(APIKey.created_at.desc())
        .all()
    )


def revoke_api_key(
    db: Session,
    merchant_id: UUID,
    api_key_id: UUID,
):
    api_key = (
        db.query(APIKey)
        .filter(
            APIKey.id == api_key_id,
            APIKey.merchant_id == merchant_id,
        )
        .first()
    )

    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found",
        )

    if not api_key.is_active:
        raise HTTPException(
            status_code=400,
            detail="API key is already revoked",
        )

    api_key.is_active = False

    db.commit()

    return {
        "message": "API key revoked successfully"
    }