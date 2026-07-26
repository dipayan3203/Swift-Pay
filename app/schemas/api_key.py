from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel
from typing import List


class APIKeyListItem(BaseModel):
    id: UUID
    public_key: str
    environment: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None

    class Config:
        from_attributes = True


class APIKeyCreateRequest(BaseModel):
    environment: Literal["TEST", "LIVE"] = "TEST"


class APIKeyResponse(BaseModel):
    id: UUID
    public_key: str
    secret_key: str
    environment: str
    created_at: datetime