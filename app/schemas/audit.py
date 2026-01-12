"""User Management Service - Audit Schemas"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class AuditAction(str, Enum):
    """Audit action enumeration"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    READ = "READ"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"


class AuditChangeSchema(BaseModel):
    """Audit change schema"""
    field: str
    old_value: Any
    new_value: Any


class CreateAuditLogRequest(BaseModel):
    """Create audit log request schema"""
    tenant_id: str
    entity_type: str
    entity_id: str
    action: AuditAction
    performed_by: str
    changes: Optional[List[AuditChangeSchema]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AuditLogResponse(BaseModel):
    """Audit log response schema"""
    id: str
    tenant_id: str
    entity_type: str
    entity_id: str
    action: AuditAction
    performed_by: str
    performed_at: datetime
    changes: List[AuditChangeSchema]
    metadata: Dict[str, Any]
