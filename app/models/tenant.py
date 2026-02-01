"""テナントモデル"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
import uuid
import re


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

    name: str = Field(..., min_length=3, max_length=100)
    display_name: str = Field(..., alias="displayName", min_length=1, max_length=200)
    plan: Optional[str] = Field("standard", pattern="^(free|standard|premium)$")
    max_users: Optional[int] = Field(100, alias="maxUsers", ge=1, le=10000)
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """テナント名の検証"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Tenant name contains invalid characters. Allowed: alphanumeric, _, -')
        return v


class TenantUpdate(BaseModel):
    """テナント更新リクエスト"""

    model_config = ConfigDict(populate_by_name=True)

    display_name: Optional[str] = Field(None, alias="displayName", min_length=1, max_length=200)
    plan: Optional[str] = Field(None, pattern="^(free|standard|premium)$")
    max_users: Optional[int] = Field(None, alias="maxUsers", ge=1, le=10000)
    metadata: Optional[Dict[str, Any]] = None
