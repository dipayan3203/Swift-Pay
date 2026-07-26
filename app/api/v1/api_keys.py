from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_merchant
from app.database.session import get_db
from app.models.merchant import Merchant
from uuid import UUID

from app.schemas.api_key import (
    APIKeyCreateRequest,
    APIKeyResponse,
    APIKeyListItem,
)

from app.services.api_key_service import (
    create_api_key,
    get_api_keys,
    revoke_api_key,
)

router = APIRouter(
    prefix="/merchant/api-keys",
    tags=["API Keys"],
)


@router.post(
    "",
    response_model=APIKeyResponse,
)
def generate_api_key(
    request: APIKeyCreateRequest,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
):
    return create_api_key(
        db=db,
        merchant_id=current_merchant.id,
        environment=request.environment,
    )


@router.get(
    "",
    response_model=List[APIKeyListItem],
)
def list_api_keys(
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
):
    return get_api_keys(
        db=db,
        merchant_id=current_merchant.id,
    )
@router.post("/{api_key_id}/revoke")
def revoke_key(
    api_key_id: UUID,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
):
    return revoke_api_key(
        db=db,
        merchant_id=current_merchant.id,
        api_key_id=api_key_id,
    )