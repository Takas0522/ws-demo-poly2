"""Tenant Management Service - Tenant Model"""
from datetime import datetime
from typing import Optional, List, Dict, Any


class Tenant:
    """Tenant model"""
    
    def __init__(
        self,
        id: str,
        tenant_id: str,
        name: str,
        status: str,
        subscription: dict,
        settings: dict,
        services: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        deleted_at: Optional[datetime] = None
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.name = name
        self.status = status
        self.subscription = subscription
        self.settings = settings
        self.services = services or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.deleted_at = deleted_at
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "tenantId": self.tenant_id,
            "name": self.name,
            "status": self.status,
            "subscription": self.subscription,
            "settings": self.settings,
            "services": self.services,
            "createdAt": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updatedAt": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
        
        if self.deleted_at:
            data["deletedAt"] = self.deleted_at.isoformat() if isinstance(self.deleted_at, datetime) else self.deleted_at
        
        return data
    
    @staticmethod
    def from_dict(data: dict) -> 'Tenant':
        """Create from dictionary"""
        return Tenant(
            id=data["id"],
            tenant_id=data["tenantId"],
            name=data["name"],
            status=data["status"],
            subscription=data["subscription"],
            settings=data["settings"],
            services=data.get("services", []),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            deleted_at=data.get("deletedAt")
        )
