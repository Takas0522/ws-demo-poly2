"""JWT認証関連のユーティリティ"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class TokenData:
    """トークンデータ"""

    def __init__(
        self,
        user_id: str,
        tenant_id: str,
        username: Optional[str] = None,
        roles: Optional[list] = None,
    ):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.username = username
        self.roles = roles or []


def verify_token(token: str) -> TokenData:
    """
    JWTトークンを検証してデコード
    
    Args:
        token: 検証するJWTトークン
    
    Returns:
        TokenData: デコード済みペイロード
    
    Raises:
        HTTPException(401): トークンが無効、期限切れ、または署名検証失敗
    """
    if not token:
        raise HTTPException(status_code=401, detail="Token is required")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        user_id = payload.get("user_id")
        tenant_id = payload.get("tenant_id")

        if not user_id or not tenant_id:
            raise HTTPException(
                status_code=401, detail="Invalid token: missing required fields"
            )

        return TokenData(
            user_id=user_id,
            tenant_id=tenant_id,
            username=payload.get("username"),
            roles=payload.get("roles", []),
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except (jwt.PyJWTError, jwt.DecodeError, jwt.InvalidSignatureError) as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


def is_privileged_tenant(tenant_id: str) -> bool:
    """
    特権テナントかどうかチェック
    
    Args:
        tenant_id: テナントID
    
    Returns:
        bool: 特権テナントの場合True
    """
    return tenant_id in settings.PRIVILEGED_TENANT_IDS
