"""Tenant Management Service - Permission Decorators"""
from functools import wraps
from typing import Callable
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


def require_permission(permission: str, scope: str = "tenant"):
    """
    Decorator to require specific permission for an endpoint.

    Args:
        permission: Permission string (e.g., "tenants.create", "users.read")
        scope: Permission scope - "global" for global permissions, "tenant" for tenant-scoped
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs if it exists
            current_user = kwargs.get("current_user")

            if not current_user:
                # If not in kwargs, try to get from request dependencies
                request = kwargs.get("request")
                if request and hasattr(request.state, "current_user"):
                    current_user = request.state.current_user

            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            # Get user permissions from token/user object
            user_permissions = current_user.get("permissions", [])
            user_roles = current_user.get("roles", [])

            # Check for global admin role (bypasses permission checks)
            if "global-admin" in user_roles:
                return await func(*args, **kwargs)

            # Check scope-specific permissions
            if scope == "global":
                # For global scope, user must have global admin role
                if "global-admin" not in user_roles:
                    raise HTTPException(
                        status_code=403, detail=f"Global admin permission required for {permission}"
                    )

            # Check if user has the specific permission
            has_permission = False

            # Check exact permission match
            if permission in user_permissions:
                has_permission = True

            # Check wildcard permissions (e.g., "tenants.*" covers "tenants.create")
            permission_parts = permission.split(".")
            if len(permission_parts) >= 2:
                wildcard_permission = f"{permission_parts[0]}.*"
                if wildcard_permission in user_permissions:
                    has_permission = True

            if not has_permission:
                raise HTTPException(
                    status_code=403, detail=f"Insufficient permissions. Required: {permission}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def check_permission(user: dict, permission: str, scope: str = "tenant") -> bool:
    """
    Check if user has specific permission.

    Args:
        user: User object/dict with permissions and roles
        permission: Permission string to check
        scope: Permission scope

    Returns:
        True if user has permission, False otherwise
    """
    if not user:
        return False

    user_permissions = user.get("permissions", [])
    user_roles = user.get("roles", [])

    # Global admins have all permissions
    if "global-admin" in user_roles:
        return True

    # For global scope, require global-admin role
    if scope == "global" and "global-admin" not in user_roles:
        return False

    # Check exact permission
    if permission in user_permissions:
        return True

    # Check wildcard permissions
    permission_parts = permission.split(".")
    if len(permission_parts) >= 2:
        wildcard_permission = f"{permission_parts[0]}.*"
        if wildcard_permission in user_permissions:
            return True

    return False
