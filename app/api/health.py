"""
Health check API endpoints.
"""
from typing import Dict, Any
from fastapi import APIRouter, status

from app.db import db_client
from app.services import auth_client

router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, Any],
    tags=["health"],
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns service status and dependencies health.
    
    Returns:
        Dict containing health status information.
    """
    # Check database connection
    db_healthy = await db_client.health_check()
    
    # Check auth service connection
    auth_healthy = await auth_client.health_check()
    
    # Overall status
    overall_status = "healthy" if db_healthy else "degraded"
    
    return {
        "status": overall_status,
        "service": "user-management-service",
        "version": "0.1.0",
        "dependencies": {
            "database": "healthy" if db_healthy else "unhealthy",
            "auth_service": "healthy" if auth_healthy else "unavailable",
        },
    }
