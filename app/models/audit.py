"""User Management Service - Audit Models"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class AuditAction(str, Enum):
    """Audit action enumeration"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    READ = "READ"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"


class AuditChange:
    """Audit change detail"""
    def __init__(self, field: str, old_value: Any, new_value: Any):
        self.field = field
        self.old_value = old_value
        self.new_value = new_value


class AuditLog:
    """Audit log entity model"""
    def __init__(
        self,
        id: str,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        action: AuditAction,
        performed_by: str,
        performed_at: datetime,
        changes: Optional[List[AuditChange]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.action = action
        self.performed_by = performed_by
        self.performed_at = performed_at
        self.changes = changes or []
        self.metadata = metadata or {}
