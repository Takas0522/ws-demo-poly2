"""User Management Service - User Routes"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.middleware import get_current_user
from app.schemas import (
    AddUserToTenantRequest,
    ApiResponse,
    BulkUserCreateRequest,
    CreateUserRequest,
    PaginatedResponse,
    PaginationParams,
    TenantUserResponse,
    UpdateUserRequest,
    UserResponse,
    UserSearchCriteria,
    UserStatus,
    UserType,
)
from app.services import user_service
from app.services.tenant_user_service import tenant_user_service
from app.utils.permissions import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("", response_model=ApiResponse[UserResponse], status_code=201)
async def create_user(
    request: CreateUserRequest, current_user: dict = Depends(get_current_user)
):
    """Create a new user"""
    try:
        # Validate tenant ID matches authenticated user
        if request.tenant_id != current_user.get("tenant_id"):
            raise HTTPException(status_code=403, detail="Tenant ID mismatch")

        user = await user_service.create_user(
            request=request, created_by=current_user["user_id"]
        )

        return ApiResponse(success=True, data=user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(
    user_id: str, request: Request, current_user: dict = Depends(get_current_user)
):
    """Get user by ID"""
    try:
        tenant_id = request.state.tenant_id

        user = await user_service.get_user(user_id, tenant_id)

        return ApiResponse(success=True, data=user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{user_id}", response_model=ApiResponse[UserResponse])
async def update_user(
    user_id: str,
    update_request: UpdateUserRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Update user"""
    try:
        tenant_id = request.state.tenant_id

        user = await user_service.update_user(
            user_id=user_id,
            tenant_id=tenant_id,
            request=update_request,
            updated_by=current_user["user_id"],
        )

        return ApiResponse(success=True, data=user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{user_id}", response_model=ApiResponse[bool])
async def delete_user(
    user_id: str, request: Request, current_user: dict = Depends(get_current_user)
):
    """Delete user (soft delete)"""
    try:
        tenant_id = request.state.tenant_id

        success = await user_service.delete_user(
            user_id=user_id, tenant_id=tenant_id, deleted_by=current_user["user_id"]
        )

        return ApiResponse(success=True, data=success)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=ApiResponse[PaginatedResponse])
async def search_users(
    request: Request,
    current_user: dict = Depends(get_current_user),
    email: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    status: Optional[UserStatus] = Query(None),
    user_type: Optional[UserType] = Query(None),
    search_term: Optional[str] = Query(None),
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
):
    """Search users with pagination and advanced filters"""
    try:
        tenant_id = request.state.tenant_id

        criteria = UserSearchCriteria(
            tenant_id=tenant_id,
            email=email,
            username=username,
            status=status,
            user_type=user_type,
            search_term=search_term,
        )

        pagination = PaginationParams(
            page_number=page_number,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        result = await user_service.search_users(criteria, pagination)

        return ApiResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/bulk", response_model=ApiResponse[dict])
@require_permission("users.create")
async def bulk_create_users(
    request: BulkUserCreateRequest, current_user: dict = Depends(get_current_user)
):
    """Bulk create users (max 100)"""
    try:
        results = await user_service.bulk_create_users(
            request.users, current_user["user_id"]
        )

        return ApiResponse(success=True, data={"results": results})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk creating users: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{user_id}/tenants", response_model=ApiResponse[List[TenantUserResponse]])
@require_permission("users.read")
async def get_user_tenants(
    user_id: str, current_user: dict = Depends(get_current_user)
):
    """Get user's tenants"""
    try:
        tenants = await tenant_user_service.get_user_tenants(user_id)

        return ApiResponse(success=True, data=tenants)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user tenants: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
