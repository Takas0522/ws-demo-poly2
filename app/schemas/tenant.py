"""テナントスキーマ"""
from datetime import datetime
from typing import Optional, Dict, Any
import re
from pydantic import BaseModel, Field, ConfigDict, field_validator


class TenantResponse(BaseModel):
    """テナントレスポンス"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    display_name: str = Field(..., alias="displayName")
    is_privileged: bool = Field(..., alias="isPrivileged")
    status: str
    plan: str
    user_count: int = Field(..., alias="userCount")
    max_users: int = Field(..., alias="maxUsers")
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    created_by: Optional[str] = Field(None, alias="createdBy")
    updated_by: Optional[str] = Field(None, alias="updatedBy")


class TenantListResponse(BaseModel):
    """テナント一覧レスポンス（簡略版）"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    display_name: str = Field(..., alias="displayName")
    is_privileged: bool = Field(..., alias="isPrivileged")
    status: str
    plan: str
    user_count: int = Field(..., alias="userCount")
    max_users: int = Field(..., alias="maxUsers")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class TenantCreateRequest(BaseModel):
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


class TenantUpdateRequest(BaseModel):
    """テナント更新リクエスト"""

    model_config = ConfigDict(populate_by_name=True)

    display_name: Optional[str] = Field(None, alias="displayName", min_length=1, max_length=200)
    plan: Optional[str] = Field(None, pattern="^(free|standard|premium)$")
    max_users: Optional[int] = Field(None, alias="maxUsers", ge=1, le=10000)
    metadata: Optional[Dict[str, Any]] = None
