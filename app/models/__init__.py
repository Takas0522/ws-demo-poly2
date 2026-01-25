"""
Data models for User Management Service.
"""
from app.models.tenant import Tenant
from app.models.tenant_user import TenantUser
from app.models.allowed_domain import AllowedDomain

__all__ = ["Tenant", "TenantUser", "AllowedDomain"]
