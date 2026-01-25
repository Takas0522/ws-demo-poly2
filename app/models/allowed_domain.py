"""
AllowedDomain model for User Management Service.
"""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class AllowedDomain(BaseModel):
    """
    AllowedDomain entity representing allowed email domains for a tenant.
    
    Attributes:
        id: Record ID (UUID string)
        tenantId: Tenant ID
        domain: Allowed domain (e.g., "example.com")
        createdAt: Timestamp when domain was added
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "ad-001",
                "tenantId": "tenant-002",
                "domain": "example.com",
                "createdAt": "2026-01-10T09:00:00Z",
            }
        }
    )
    
    id: str = Field(..., description="Record ID (UUID)")
    tenantId: str = Field(..., description="Tenant ID")
    domain: str = Field(..., description="Allowed domain")
    createdAt: datetime = Field(..., description="Creation timestamp")
    
    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """
        Validate domain format.
        
        Validates that the domain is a valid domain name format, allowing:
        - Simple domains: example.com
        - Subdomains: sub.example.com
        - Hyphenated domains: my-domain.com
        - Multi-level subdomains: a.b.c.example.com
        
        Args:
            v: Domain string to validate
            
        Returns:
            Validated domain string
            
        Raises:
            ValueError: If domain format is invalid
        """
        # Pattern allows for domains and subdomains with proper structure
        # Domain parts must start/end with alphanumeric, can contain hyphens in between
        # Must have at least one dot and a valid TLD (2+ letters)
        pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError(
                f"Invalid domain format: {v}. "
                r"Domain must be a valid domain name (e.g., example.com, sub.example.com)"
            )
        return v
