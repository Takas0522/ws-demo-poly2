"""テナントユーザースキーマ"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class TenantUserCreateRequest(BaseModel):
    """テナントユーザー作成リクエスト"""

    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(..., alias="userId", min_length=1)


class TenantUserResponse(BaseModel):
    """テナントユーザーレスポンス"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    tenant_id: str = Field(..., alias="tenantId")
    user_id: str = Field(..., alias="userId")
    user_details: Optional[Dict[str, Any]] = Field(None, alias="userDetails")
    assigned_at: datetime = Field(..., alias="assignedAt")
    assigned_by: str = Field(..., alias="assignedBy")


class TenantUserListResponse(BaseModel):
    """テナントユーザー一覧レスポンス"""

    model_config = ConfigDict(populate_by_name=True)

    data: list[TenantUserResponse]
    pagination: Dict[str, Any]
