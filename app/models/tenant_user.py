"""テナントユーザーモデル"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TenantUser(BaseModel):
    """テナントユーザーエンティティ"""

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() + "Z"},
    )

    id: str
    tenant_id: str = Field(..., alias="tenantId")
    type: str = "tenant_user"
    user_id: str = Field(..., alias="userId")
    assigned_at: datetime = Field(default_factory=datetime.utcnow, alias="assignedAt")
    assigned_by: str = Field(..., alias="assignedBy")
