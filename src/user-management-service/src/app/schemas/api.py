"""User Management Service - API Response Schemas"""
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


T = TypeVar('T')


class ErrorCode(str, Enum):
    """Error code enumeration"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TENANT_MISMATCH = "TENANT_MISMATCH"
    INVALID_INPUT = "INVALID_INPUT"


class ApiError(BaseModel):
    """API error schema"""
    code: ErrorCode
    message: str
    details: Optional[dict] = None


class ApiResponse(BaseModel, Generic[T]):
    """API response wrapper schema"""
    success: bool
    data: Optional[T] = None
    error: Optional[ApiError] = None
    timestamp: datetime = datetime.utcnow()
