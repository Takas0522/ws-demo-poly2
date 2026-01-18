"""User Management Service - Authentication Middleware"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config import settings
from app.schemas import ErrorCode
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)  # Make auth optional for development


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Extract and validate JWT token"""

    # In development mode, allow requests without authentication
    if settings.environment == "development" and credentials is None:
        logger.warning("Development mode: Using mock user authentication")
        return {
            "user_id": "dev-user-123",
            "tenant_id": "tenant-1",
            "email": "dev@example.com",
            "roles": ["admin"],
            "permissions": ["*"]
        }

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail={
                "code": ErrorCode.UNAUTHORIZED,
                "message": "Authentication required"
            }
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer
        )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": ErrorCode.UNAUTHORIZED,
                    "message": "Invalid authentication credentials"
                }
            )

        return {
            "user_id": user_id,
            "tenant_id": payload.get("tenant_id"),
            "email": payload.get("email"),
            "username": payload.get("username")
        }

    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail={
                "code": ErrorCode.UNAUTHORIZED,
                "message": "Invalid authentication credentials"
            }
        )
