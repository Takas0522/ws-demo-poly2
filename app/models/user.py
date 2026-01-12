"""User Management Service - Models"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class UserStatus(str, Enum):
    """User status enumeration"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class UserProfile:
    """User profile information"""
    def __init__(
        self,
        phone_number: Optional[str] = None,
        department: Optional[str] = None,
        job_title: Optional[str] = None,
        avatar_url: Optional[str] = None,
        bio: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ):
        self.phone_number = phone_number
        self.department = department
        self.job_title = job_title
        self.avatar_url = avatar_url
        self.bio = bio
        self.preferences = preferences or {}


class User:
    """User entity model"""
    def __init__(
        self,
        id: str,
        tenant_id: str,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        profile: UserProfile,
        status: UserStatus,
        created_at: datetime,
        updated_at: datetime,
        created_by: str,
        updated_by: str
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.email = email
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.profile = profile
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.created_by = created_by
        self.updated_by = updated_by
