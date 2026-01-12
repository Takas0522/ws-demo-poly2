"""User Management Service - Routers Package"""
from .user_routes import router as user_router
from .health_routes import router as health_router
from .tenant_routes import router as tenant_router

__all__ = ["user_router", "health_router", "tenant_router"]
