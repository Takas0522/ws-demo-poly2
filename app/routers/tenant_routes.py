"""Tenant Management Service - Tenant Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse, AssignAdminRequest
from app.schemas import ApiResponse
from app.services.tenant_service import tenant_service
from app.middleware import get_current_user
from app.utils.permissions import require_permission
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenants", tags=["tenants"])


@router.post("", response_model=ApiResponse[TenantResponse], status_code=201)
@require_permission("tenants.create", scope="global")
async def create_tenant(tenant: TenantCreate, current_user: dict = Depends(get_current_user)):
    """
    Create a new tenant (Global admin only).

    Requires:
        - Global admin permission
        - tenants.create permission
    """
    try:
        created_tenant = await tenant_service.create_tenant(
            request=tenant, created_by=current_user.get("user_id", "system")
        )

        return ApiResponse(success=True, data=created_tenant)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tenant: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=ApiResponse[List[TenantResponse]])
@require_permission("tenants.read", scope="global")
async def list_tenants(
    current_user: dict = Depends(get_current_user),
    status: Optional[str] = Query(None, description="Filter by status"),
    plan: Optional[str] = Query(None, description="Filter by subscription plan"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
):
    """
    List all tenants with optional filtering and pagination.

    Requires:
        - Global admin permission
        - tenants.read permission
    """
    try:
        tenants = await tenant_service.list_tenants(
            status=status, plan=plan, skip=skip, limit=limit
        )

        return ApiResponse(success=True, data=tenants)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tenants: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{tenant_id}", response_model=ApiResponse[TenantResponse])
@require_permission("tenants.read")
async def get_tenant(tenant_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get tenant details by ID.

    Requires:
        - tenants.read permission
    """
    try:
        tenant = await tenant_service.get_tenant(tenant_id)

        return ApiResponse(success=True, data=tenant)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tenant: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{tenant_id}", response_model=ApiResponse[TenantResponse])
@require_permission("tenants.update")
async def update_tenant(
    tenant_id: str, update: TenantUpdate, current_user: dict = Depends(get_current_user)
):
    """
    Update tenant information.

    Requires:
        - tenants.update permission
    """
    try:
        updated_tenant = await tenant_service.update_tenant(
            tenant_id=tenant_id, request=update, updated_by=current_user.get("user_id", "system")
        )

        return ApiResponse(success=True, data=updated_tenant)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tenant: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{tenant_id}", status_code=204)
@require_permission("tenants.delete", scope="global")
async def delete_tenant(tenant_id: str, current_user: dict = Depends(get_current_user)):
    """
    Delete tenant (soft delete). Global admin only.

    Requires:
        - Global admin permission
        - tenants.delete permission
    """
    try:
        success = await tenant_service.delete_tenant(
            tenant_id=tenant_id, deleted_by=current_user.get("user_id", "system")
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete tenant")

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tenant: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{tenant_id}/admins", response_model=ApiResponse[dict])
@require_permission("tenants.update")
async def assign_tenant_admin(
    tenant_id: str, request: AssignAdminRequest, current_user: dict = Depends(get_current_user)
):
    """
    Assign tenant admin role to a user.

    Requires:
        - tenants.update permission
    """
    try:
        tenant_user = await tenant_service.assign_tenant_admin(
            tenant_id=tenant_id, request=request, assigned_by=current_user.get("user_id", "system")
        )

        return ApiResponse(success=True, data=tenant_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning tenant admin: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
