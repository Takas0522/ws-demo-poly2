"""
API schemas for tenant management.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TenantListItem(BaseModel):
    """Tenant list item in API responses."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "tenant-001",
                "name": "特権管理テナント",
                "isPrivileged": True,
                "userCount": 5,
                "createdAt": "2026-01-01T00:00:00Z",
            }
        }
    )
    
    id: str = Field(..., description="Tenant ID")
    name: str = Field(..., description="Tenant name")
    isPrivileged: bool = Field(..., description="Privileged tenant flag")
    userCount: int = Field(..., description="Number of users in tenant")
    createdAt: datetime = Field(..., description="Creation timestamp")


class TenantDetail(BaseModel):
    """Tenant detail in API responses."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "tenant-001",
                "name": "特権管理テナント",
                "isPrivileged": True,
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
            }
        }
    )
    
    id: str = Field(..., description="Tenant ID")
    name: str = Field(..., description="Tenant name")
    isPrivileged: bool = Field(..., description="Privileged tenant flag")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")


class TenantListResponse(BaseModel):
    """Response for tenant list endpoint."""
    
    data: List[TenantListItem] = Field(..., description="List of tenants")
    pagination: "PaginationInfo" = Field(..., description="Pagination information")


class TenantDetailResponse(BaseModel):
    """Response for tenant detail endpoint."""
    
    data: TenantDetail = Field(..., description="Tenant details")


class TenantUpdateRequest(BaseModel):
    """Request for tenant update endpoint."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Tenant Name",
            }
        }
    )
    
    name: Optional[str] = Field(None, description="Tenant name", min_length=1, max_length=100)


class PaginationInfo(BaseModel):
    """Pagination metadata."""
    
    page: int = Field(..., description="Current page number")
    pageSize: int = Field(..., description="Items per page")
    totalItems: int = Field(..., description="Total number of items")
    totalPages: int = Field(..., description="Total number of pages")


class ErrorResponse(BaseModel):
    """Error response."""
    
    error: "ErrorDetail" = Field(..., description="Error details")


class ErrorDetail(BaseModel):
    """Error detail information."""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")
