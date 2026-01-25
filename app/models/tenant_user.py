"""
TenantUser model for User Management Service.
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TenantUser(BaseModel):
    """
    TenantUser entity representing the association between a tenant and a user.
    
    Attributes:
        id: Record ID (UUID string)
        tenantId: Tenant ID
        userId: User ID (managed by Auth Service)
        addedAt: Timestamp when user was added to tenant
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "tu-001",
                "tenantId": "tenant-001",
                "userId": "user-001",
                "addedAt": "2026-01-15T10:00:00Z",
            }
        }
    )
    
    id: str = Field(..., description="Record ID (UUID)")
    tenantId: str = Field(..., description="Tenant ID")
    userId: str = Field(..., description="User ID")
    addedAt: datetime = Field(..., description="Timestamp when user was added")
