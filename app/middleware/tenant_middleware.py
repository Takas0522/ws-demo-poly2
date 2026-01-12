"""User Management Service - Tenant Validation Middleware"""
from fastapi import Request, HTTPException
from app.schemas import ErrorCode
import logging

logger = logging.getLogger(__name__)


async def validate_tenant_id(request: Request, call_next):
    """Middleware to validate tenant ID in requests"""
    # Skip validation for health check and docs endpoints
    if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)
    
    # Skip validation for tenant management endpoints (global admin operations)
    if request.url.path.startswith("/api/tenants"):
        return await call_next(request)
    
    # Get tenant ID from header
    tenant_id = request.headers.get("X-Tenant-ID")
    
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail={
                "code": ErrorCode.INVALID_INPUT,
                "message": "X-Tenant-ID header is required"
            }
        )
    
    # Add tenant ID to request state for easy access
    request.state.tenant_id = tenant_id
    
    return await call_next(request)
