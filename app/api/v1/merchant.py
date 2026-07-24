from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_merchant
from app.models.merchant import Merchant

router = APIRouter(
    prefix="/merchant",
    tags=["Merchant"],
)


@router.get("/profile")
def get_profile(
    current_merchant: Merchant = Depends(get_current_merchant),
):
    return {
        "id": str(current_merchant.id),
        "business_name": current_merchant.business_name,
        "email": current_merchant.email,
        "phone": current_merchant.phone,
        "is_active": current_merchant.is_active,
        "created_at": current_merchant.created_at,
    }