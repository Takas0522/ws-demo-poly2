"""
Tenant model for User Management Service.
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class Tenant(BaseModel):
    """
    Tenant entity representing a tenant in the system.
    
    Attributes:
        id: Tenant ID (UUID string)
        name: Tenant name (must be unique)
        isPrivileged: Flag indicating if tenant is privileged (cannot be deleted/edited)
        createdAt: Timestamp when tenant was created
        updatedAt: Timestamp when tenant was last updated
    """
    
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
    
    id: str = Field(..., description="Tenant ID (UUID)")
    name: str = Field(..., description="Tenant name")
    isPrivileged: bool = Field(default=False, description="Privileged tenant flag")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")
