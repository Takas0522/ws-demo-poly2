"""User Management Service - Pydantic Schemas"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from enum import Enum


class UserStatus(str, Enum):
    """User status enumeration"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class UserType(str, Enum):
    """User type enumeration"""
    INTERNAL = "internal"  # 管理会社内ユーザー
    EXTERNAL = "external"  # テナントユーザー


class UserProfileSchema(BaseModel):
    """User profile schema"""
    phone_number: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class UserBaseSchema(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    profile: Optional[UserProfileSchema] = Field(default_factory=UserProfileSchema)
    status: Optional[UserStatus] = UserStatus.ACTIVE


class CreateUserRequest(UserBaseSchema):
    """Create user request schema"""
    tenant_id: str = Field(..., min_length=1)
    password: Optional[str] = Field(None, min_length=8, max_length=128)  # Plain password
    user_type: Optional[UserType] = UserType.EXTERNAL
    primary_tenant_id: Optional[str] = None
    roles: Optional[List[str]] = Field(default_factory=list)
    permissions: Optional[List[str]] = Field(default_factory=list)


class UpdateUserRequest(BaseModel):
    """Update user request schema"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    profile: Optional[UserProfileSchema] = None
    status: Optional[UserStatus] = None


class UserResponse(UserBaseSchema):
    """User response schema"""
    id: str
    tenant_id: str
    user_type: Optional[str] = None
    primary_tenant_id: Optional[str] = None
    roles: Optional[List[str]] = Field(default_factory=list)
    permissions: Optional[List[str]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    
    model_config = ConfigDict(from_attributes=True)


class UserSearchCriteria(BaseModel):
    """User search criteria schema"""
    tenant_id: str
    email: Optional[str] = None
    username: Optional[str] = None
    status: Optional[UserStatus] = None
    user_type: Optional[UserType] = None
    search_term: Optional[str] = None  # Search across email, username, firstName, lastName


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page_number: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Paginated response schema"""
    items: list[UserResponse]
    total_count: int
    page_number: int
    page_size: int
    total_pages: int
    has_next_page: bool
    has_previous_page: bool


# TenantUser schemas
class TenantUserResponse(BaseModel):
    """TenantUser response schema"""
    id: str
    user_id: str
    tenant_id: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    status: str
    joined_at: datetime
    left_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AddUserToTenantRequest(BaseModel):
    """Add user to tenant request schema"""
    user_id: str = Field(..., min_length=1)
    roles: Optional[List[str]] = Field(default_factory=lambda: ["user"])
    permissions: Optional[List[str]] = Field(default_factory=list)


class BulkUserCreateRequest(BaseModel):
    """Bulk user create request schema"""
    users: List[CreateUserRequest] = Field(..., max_length=100)
