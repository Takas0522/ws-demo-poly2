"""依存注入の一元管理"""
from fastapi import Depends, Header, HTTPException, Request
from typing import Optional
import logging

from app.repositories.tenant_repository import TenantRepository
from app.services.tenant_service import TenantService
from app.utils.jwt import verify_token, TokenData

logger = logging.getLogger(__name__)


def get_cosmos_container(request: Request):
    """
    Cosmos DBコンテナを取得
    
    Args:
        request: FastAPIリクエストオブジェクト
    
    Returns:
        Cosmos DBコンテナクライアント
    
    Raises:
        RuntimeError: Cosmos DBが初期化されていない場合
    """
    if not hasattr(request.app.state, "cosmos_container"):
        raise RuntimeError("Cosmos DB not initialized")
    return request.app.state.cosmos_container


def get_tenant_repository(
    container=Depends(get_cosmos_container),
) -> TenantRepository:
    """
    TenantRepositoryの依存注入
    
    Args:
        container: Cosmos DBコンテナ
    
    Returns:
        TenantRepositoryインスタンス
    """
    return TenantRepository(container)


def get_tenant_service(
    tenant_repository: TenantRepository = Depends(get_tenant_repository),
) -> TenantService:
    """
    TenantServiceの依存注入
    
    Args:
        tenant_repository: TenantRepositoryインスタンス
    
    Returns:
        TenantServiceインスタンス
    """
    return TenantService(tenant_repository)


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> TokenData:
    """
    トークンから現在のユーザー情報を取得
    
    Args:
        authorization: Authorizationヘッダー
    
    Returns:
        認証済みユーザー情報
    
    Raises:
        HTTPException: トークンが無効
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )

    # "Bearer " プレフィックスを削除
    BEARER_PREFIX = "Bearer "
    token = authorization[len(BEARER_PREFIX) :]

    # トークン検証
    token_data = verify_token(token)

    return token_data
