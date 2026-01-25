"""
Tenant management API endpoints.
"""
from typing import Dict, Any, Optional
from math import ceil
from enum import Enum

from fastapi import APIRouter, HTTPException, status, Depends, Query

from app.core.auth import get_current_user, require_role, Role
from app.repositories import tenant_repository
from app.api.schemas import (
    TenantListResponse,
    TenantDetailResponse,
    TenantUpdateRequest,
    TenantListItem,
    TenantDetail,
    PaginationInfo,
)


class SortField(str, Enum):
    """Allowed fields for sorting tenants."""
    ID = "id"
    NAME = "name"
    IS_PRIVILEGED = "isPrivileged"
    CREATED_AT = "createdAt"
    UPDATED_AT = "updatedAt"


router = APIRouter(prefix="/api/tenants", tags=["tenants"])


def _get_tenant_or_404(tenant_id: str, tenant: Optional[Any]) -> None:
    """
    Helper function to check if tenant exists and raise 404 if not.
    
    Args:
        tenant_id: Tenant ID for error message.
        tenant: Tenant object or None.
    
    Raises:
        HTTPException: 404 if tenant is None.
    """
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TENANT_NOT_FOUND",
                "message": "指定されたテナントが見つかりません",
                "details": {"tenantId": tenant_id},
            },
        )



@router.get(
    "",
    response_model=TenantListResponse,
    status_code=status.HTTP_200_OK,
    summary="テナント一覧取得",
    description="テナント一覧を取得します。ページネーション、ソートをサポートします。",
)
async def list_tenants(
    page: int = Query(1, ge=1, description="ページ番号（1始まり）"),
    pageSize: int = Query(20, ge=1, le=100, description="1ページあたりの件数（最大100）"),
    sortBy: SortField = Query(SortField.CREATED_AT, description="ソートフィールド"),
    sortOrder: str = Query("desc", pattern="^(asc|desc)$", description="ソート順（asc/desc）"),
    current_user: Dict[str, Any] = Depends(
        require_role(Role.GLOBAL_ADMIN, Role.ADMIN, Role.VIEWER)
    ),
) -> TenantListResponse:
    """
    Get list of tenants with pagination and sorting.
    
    All authenticated users (GlobalAdmin, Admin, Viewer) can access this endpoint.
    
    Args:
        page: Page number (1-indexed).
        pageSize: Number of items per page (max 100).
        sortBy: Field to sort by.
        sortOrder: Sort order (asc/desc).
        current_user: Current authenticated user.
    
    Returns:
        TenantListResponse with list of tenants and pagination info.
    """
    # Get tenants from repository
    tenants, total_count = await tenant_repository.get_all(
        page=page,
        page_size=pageSize,
        sort_by=sortBy.value,
        sort_order=sortOrder,
    )
    
    # Get user count for each tenant
    tenant_items = []
    for tenant in tenants:
        user_count = await tenant_repository.get_user_count(tenant.id)
        tenant_items.append(
            TenantListItem(
                id=tenant.id,
                name=tenant.name,
                isPrivileged=tenant.isPrivileged,
                userCount=user_count,
                createdAt=tenant.createdAt,
            )
        )
    
    # Calculate pagination
    total_pages = ceil(total_count / pageSize) if total_count > 0 else 0
    
    return TenantListResponse(
        data=tenant_items,
        pagination=PaginationInfo(
            page=page,
            pageSize=pageSize,
            totalItems=total_count,
            totalPages=total_pages,
        ),
    )


@router.get(
    "/{tenant_id}",
    response_model=TenantDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="テナント詳細取得",
    description="指定されたIDのテナント詳細を取得します。",
)
async def get_tenant(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(
        require_role(Role.GLOBAL_ADMIN, Role.ADMIN, Role.VIEWER)
    ),
) -> TenantDetailResponse:
    """
    Get tenant details by ID.
    
    All authenticated users (GlobalAdmin, Admin, Viewer) can access this endpoint.
    
    Args:
        tenant_id: Tenant ID.
        current_user: Current authenticated user.
    
    Returns:
        TenantDetailResponse with tenant details.
    
    Raises:
        HTTPException: If tenant not found (404).
    """
    tenant = await tenant_repository.get_by_id(tenant_id)
    _get_tenant_or_404(tenant_id, tenant)
    
    return TenantDetailResponse(
        data=TenantDetail(
            id=tenant.id,
            name=tenant.name,
            isPrivileged=tenant.isPrivileged,
            createdAt=tenant.createdAt,
            updatedAt=tenant.updatedAt,
        )
    )


@router.put(
    "/{tenant_id}",
    response_model=TenantDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="テナント更新",
    description="指定されたIDのテナント情報を更新します。特権テナントは全体管理者のみ編集可能です。",
)
async def update_tenant(
    tenant_id: str,
    request: TenantUpdateRequest,
    current_user: Dict[str, Any] = Depends(
        require_role(Role.GLOBAL_ADMIN, Role.ADMIN)
    ),
) -> TenantDetailResponse:
    """
    Update tenant by ID.
    
    - GlobalAdmin can update all tenants including privileged tenants.
    - Admin can update only regular tenants (not privileged).
    - Viewer cannot update any tenants.
    
    Args:
        tenant_id: Tenant ID.
        request: Update request with fields to update.
        current_user: Current authenticated user.
    
    Returns:
        TenantDetailResponse with updated tenant details.
    
    Raises:
        HTTPException: If tenant not found (404) or privileged tenant protection (403).
    """
    # Get existing tenant
    tenant = await tenant_repository.get_by_id(tenant_id)
    _get_tenant_or_404(tenant_id, tenant)
    
    # Check privileged tenant protection
    user_role = current_user.get("role")
    if tenant.isPrivileged and user_role != Role.GLOBAL_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "TENANT_PRIVILEGED_PROTECTED",
                "message": "特権テナントの編集は全体管理者のみ可能です",
                "details": {"tenantId": tenant_id},
            },
        )
    
    # Prepare updates
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    
    # If no updates, return current tenant
    if not updates:
        return TenantDetailResponse(
            data=TenantDetail(
                id=tenant.id,
                name=tenant.name,
                isPrivileged=tenant.isPrivileged,
                createdAt=tenant.createdAt,
                updatedAt=tenant.updatedAt,
            )
        )
    
    # Update tenant
    updated_tenant = await tenant_repository.update(tenant_id, updates)
    _get_tenant_or_404(tenant_id, updated_tenant)
    
    return TenantDetailResponse(
        data=TenantDetail(
            id=updated_tenant.id,
            name=updated_tenant.name,
            isPrivileged=updated_tenant.isPrivileged,
            createdAt=updated_tenant.createdAt,
            updatedAt=updated_tenant.updatedAt,
        )
    )
