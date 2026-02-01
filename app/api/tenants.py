"""テナント管理API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
import logging

from app.schemas.tenant import (
    TenantResponse,
    TenantListResponse,
    TenantCreateRequest,
    TenantUpdateRequest,
)
from app.services.tenant_service import TenantService
from app.dependencies import get_tenant_service, get_current_user
from app.utils.jwt import TokenData, is_privileged_tenant

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=dict)
async def list_tenants(
    status: Optional[str] = Query(
        None, pattern="^(active|suspended|deleted)$", description="ステータスフィルタ"
    ),
    skip: int = Query(0, ge=0, description="スキップ件数"),
    limit: int = Query(20, ge=1, le=100, description="取得件数"),
    current_user: TokenData = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> dict:
    """
    テナント一覧取得
    
    特権テナントは全テナントを取得可能。
    一般テナントは自テナントのみ取得可能。
    
    Args:
        status: ステータスフィルタ
        skip: スキップ件数
        limit: 取得件数
        current_user: 現在のユーザー情報（インジェクション）
        tenant_service: TenantService（インジェクション）
    
    Returns:
        テナント一覧とページネーション情報
    """
    # 特権テナントかどうかチェック
    privileged = is_privileged_tenant(current_user.tenant_id)

    # テナント一覧取得
    tenants = await tenant_service.list_tenants(
        current_tenant_id=current_user.tenant_id,
        is_privileged=privileged,
        status=status,
        skip=skip,
        limit=limit,
    )

    # レスポンス変換
    tenant_list = [
        TenantListResponse(
            id=tenant.id,
            name=tenant.name,
            displayName=tenant.display_name,
            isPrivileged=tenant.is_privileged,
            status=tenant.status,
            plan=tenant.plan,
            userCount=tenant.user_count,
            maxUsers=tenant.max_users,
            createdAt=tenant.created_at,
            updatedAt=tenant.updated_at,
        )
        for tenant in tenants
    ]

    return {
        "data": tenant_list,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": len(tenant_list),
        },
    }


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: TokenData = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    """
    テナント詳細取得
    
    Args:
        tenant_id: テナントID
        current_user: 現在のユーザー情報（インジェクション）
        tenant_service: TenantService（インジェクション）
    
    Returns:
        テナント詳細情報
    
    Raises:
        HTTPException: 403 if テナント分離違反、404 if テナント不在
    """
    # テナント分離チェック
    privileged = is_privileged_tenant(current_user.tenant_id)
    if not privileged and current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=403, detail="Cannot access data from other tenants"
        )

    # テナント取得
    tenant = await tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        displayName=tenant.display_name,
        isPrivileged=tenant.is_privileged,
        status=tenant.status,
        plan=tenant.plan,
        userCount=tenant.user_count,
        maxUsers=tenant.max_users,
        metadata=tenant.metadata,
        createdAt=tenant.created_at,
        updatedAt=tenant.updated_at,
        createdBy=tenant.created_by,
        updatedBy=tenant.updated_by,
    )


@router.post("/", response_model=TenantResponse, status_code=201)
async def create_tenant(
    tenant_data: TenantCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    """
    テナント新規作成
    
    管理者ロール必要（Phase 1ではロール未実装のため、認証済みユーザーは全員可能）
    
    Args:
        tenant_data: テナント作成データ
        current_user: 現在のユーザー情報（インジェクション）
        tenant_service: TenantService（インジェクション）
    
    Returns:
        作成されたテナント情報
    
    Raises:
        HTTPException: 422 if バリデーションエラー、409 if 名前重複
    """
    try:
        # テナント作成
        tenant = await tenant_service.create_tenant(tenant_data, current_user.user_id)

        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            displayName=tenant.display_name,
            isPrivileged=tenant.is_privileged,
            status=tenant.status,
            plan=tenant.plan,
            userCount=tenant.user_count,
            maxUsers=tenant.max_users,
            metadata=tenant.metadata,
            createdAt=tenant.created_at,
            updatedAt=tenant.updated_at,
            createdBy=tenant.created_by,
            updatedBy=tenant.updated_by,
        )
    except ValueError as e:
        error_message = str(e)
        if "already exists" in error_message:
            raise HTTPException(status_code=409, detail=error_message)
        else:
            raise HTTPException(status_code=422, detail=error_message)


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    """
    テナント更新
    
    管理者ロール必要（Phase 1ではロール未実装のため、認証済みユーザーは全員可能）
    特権テナントは更新不可
    
    Args:
        tenant_id: テナントID
        tenant_data: テナント更新データ
        current_user: 現在のユーザー情報（インジェクション）
        tenant_service: TenantService（インジェクション）
    
    Returns:
        更新されたテナント情報
    
    Raises:
        HTTPException: 403 if 特権テナント、404 if テナント不在、422 if バリデーションエラー
    """
    try:
        # テナント更新
        tenant = await tenant_service.update_tenant(
            tenant_id, tenant_data, current_user.user_id
        )

        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            displayName=tenant.display_name,
            isPrivileged=tenant.is_privileged,
            status=tenant.status,
            plan=tenant.plan,
            userCount=tenant.user_count,
            maxUsers=tenant.max_users,
            metadata=tenant.metadata,
            createdAt=tenant.created_at,
            updatedAt=tenant.updated_at,
            createdBy=tenant.created_by,
            updatedBy=tenant.updated_by,
        )
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message:
            raise HTTPException(status_code=404, detail=error_message)
        elif "Privileged tenant" in error_message:
            raise HTTPException(status_code=403, detail=error_message)
        else:
            raise HTTPException(status_code=422, detail=error_message)


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(
    tenant_id: str,
    current_user: TokenData = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> None:
    """
    テナント削除
    
    管理者ロール必要（Phase 1ではロール未実装のため、認証済みユーザーは全員可能）
    特権テナントは削除不可
    ユーザーが存在する場合は削除不可
    
    Phase 1: 物理削除
    
    Args:
        tenant_id: テナントID
        current_user: 現在のユーザー情報（インジェクション）
        tenant_service: TenantService（インジェクション）
    
    Raises:
        HTTPException: 403 if 特権テナント、404 if テナント不在、400 if ユーザー存在
    """
    try:
        # テナント削除
        await tenant_service.delete_tenant(tenant_id, current_user.user_id)

        return None
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message:
            raise HTTPException(status_code=404, detail=error_message)
        elif "Privileged tenant" in error_message:
            raise HTTPException(status_code=403, detail=error_message)
        elif "existing users" in error_message:
            raise HTTPException(status_code=400, detail=error_message)
        else:
            raise HTTPException(status_code=422, detail=error_message)
