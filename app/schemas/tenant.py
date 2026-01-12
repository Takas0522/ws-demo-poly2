"""Tenant Management Service - Tenant Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class TenantStatus(str, Enum):
    """Tenant status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class SubscriptionPlan(str, Enum):
    """Subscription plan enumeration"""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionSchema(BaseModel):
    """Subscription schema"""
    plan: SubscriptionPlan
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_users: Optional[int] = None
    features: Optional[List[str]] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class TenantSettingsSchema(BaseModel):
    """Tenant settings schema"""
    timezone: str = "Asia/Tokyo"
    locale: str = "ja-JP"
    features: Optional[Dict[str, Any]] = Field(default_factory=dict)
    allowed_domains: Optional[List[str]] = Field(default_factory=list, alias="allowedDomains")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TenantCreate(BaseModel):
    """Create tenant request schema"""
    name: str = Field(..., min_length=1, max_length=200)
    subscription: SubscriptionSchema
    timezone: Optional[str] = "Asia/Tokyo"
    locale: Optional[str] = "ja-JP"
    allowed_domains: Optional[List[str]] = Field(default_factory=list)


class TenantUpdate(BaseModel):
    """Update tenant request schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[TenantStatus] = None
    subscription: Optional[SubscriptionSchema] = None
    allowed_domains: Optional[List[str]] = None


class TenantResponse(BaseModel):
    """Tenant response schema"""
    id: str
    tenant_id: str
    name: str
    status: str
    subscription: SubscriptionSchema
    settings: TenantSettingsSchema
    services: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class AssignAdminRequest(BaseModel):
    """Assign tenant admin request schema"""
    user_id: str = Field(..., min_length=1)
