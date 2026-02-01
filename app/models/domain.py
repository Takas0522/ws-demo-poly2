"""ドメインモデル"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Domain(BaseModel):
    """ドメインエンティティ"""

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() + "Z"},
    )

    id: str
    tenant_id: str = Field(..., alias="tenantId")
    type: str = "domain"
    domain: str
    verified: bool = False
    verification_token: str = Field(..., alias="verificationToken")
    verified_at: Optional[datetime] = Field(None, alias="verifiedAt")
    verified_by: Optional[str] = Field(None, alias="verifiedBy")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    created_by: str = Field(..., alias="createdBy")
