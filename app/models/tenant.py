"""テナントモデル"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import uuid


class Tenant(BaseModel):
    """テナントエンティティ"""

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat() + "Z"},
    )

    id: str
    tenant_id: str = Field(..., alias="tenantId")
    type: str = "tenant"
    name: str
    display_name: str = Field(..., alias="displayName")
    is_privileged: bool = Field(default=False, alias="isPrivileged")
    status: str = "active"
    plan: str = "standard"
    user_count: int = Field(default=0, alias="userCount")
    max_users: int = Field(default=100, alias="maxUsers")
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
    created_by: Optional[str] = Field(None, alias="createdBy")
    updated_by: Optional[str] = Field(None, alias="updatedBy")


class TenantCreate(BaseModel):
    """テナント作成リクエスト"""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    display_name: str = Field(..., alias="displayName")
    plan: Optional[str] = "standard"
    max_users: Optional[int] = Field(100, alias="maxUsers")
    metadata: Optional[Dict[str, Any]] = None


class TenantUpdate(BaseModel):
    """テナント更新リクエスト"""

    model_config = ConfigDict(populate_by_name=True)

    display_name: Optional[str] = Field(None, alias="displayName")
    plan: Optional[str] = None
    max_users: Optional[int] = Field(None, alias="maxUsers")
    metadata: Optional[Dict[str, Any]] = None
