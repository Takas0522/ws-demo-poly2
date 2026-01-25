"""
Authentication and authorization utilities.
"""
from typing import Optional, Dict, Any, Callable
from functools import wraps
from enum import Enum

from fastapi import HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services import auth_client


class Role(str, Enum):
    """User roles for access control."""
    GLOBAL_ADMIN = "全体管理者"  # Global Administrator
    ADMIN = "管理者"  # Administrator
    VIEWER = "閲覧者"  # Viewer


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer authorization credentials.
    
    Returns:
        Dict containing user information from JWT payload.
    
    Raises:
        HTTPException: If token is invalid or missing.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証情報が提供されていません",
        )
    
    token = credentials.credentials
    payload = await auth_client.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効な認証トークンです",
        )
    
    return payload


def require_role(*allowed_roles: Role) -> Callable:
    """
    Decorator to require specific roles for endpoint access.
    
    Args:
        allowed_roles: One or more Role values that are allowed to access the endpoint.
    
    Returns:
        Dependency function that validates user role.
    
    Raises:
        HTTPException: If user doesn't have required role.
    """
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        # Get roles from JWT payload
        # Roles are structured as: {"auth-service": ["全体管理者"], "user-service": ["管理者"]}
        user_roles = current_user.get("roles", {})
        
        # Extract all role names from all services
        all_user_roles = []
        for service_roles in user_roles.values():
            if isinstance(service_roles, list):
                all_user_roles.extend(service_roles)
        
        # Check if user has any of the allowed roles
        allowed_role_values = [role.value for role in allowed_roles]
        if not any(role in allowed_role_values for role in all_user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この操作を実行する権限がありません",
            )
        
        return current_user
    
    return role_checker


async def get_optional_user(
    authorization: Optional[str] = Header(None),
) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, None otherwise.
    Useful for endpoints that work with or without authentication.
    
    Args:
        authorization: Optional Authorization header.
    
    Returns:
        Dict containing user information if authenticated, None otherwise.
    """
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    payload = await auth_client.verify_token(token)
    
    return payload
