"""
API routers module.
"""
from fastapi import APIRouter
from app.api import health, tenants

api_router = APIRouter()

# Include health check router (at root level, not under /api)
# This will be included directly in main.py

__all__ = ["health", "tenants", "api_router"]
