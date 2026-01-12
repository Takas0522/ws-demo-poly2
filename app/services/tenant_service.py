"""Tenant Management Service - Tenant Service"""
from typing import Optional, List
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException
from app.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantSettingsSchema,
    SubscriptionSchema,
    AssignAdminRequest
)
from app.schemas import ErrorCode
from app.repositories.tenant_repository import tenant_repository, tenant_user_repository
from app.utils.validation import validate_domain_list
import logging

logger = logging.getLogger(__name__)


class TenantService:
    """Tenant service for business logic"""
    
    def __init__(self):
        self.tenant_repo = tenant_repository
        self.tenant_user_repo = tenant_user_repository
    
    async def create_tenant(
        self,
        request: TenantCreate,
        created_by: str = "system"
    ) -> TenantResponse:
        """Create a new tenant"""
        # Validate allowed domains if provided
        if request.allowed_domains:
            validate_domain_list(request.allowed_domains)
        
        # Create tenant data
        tenant_id = f"tenant-{uuid4()}"
        now = datetime.now(timezone.utc)
        
        tenant_data = {
            'id': tenant_id,
            'tenantId': tenant_id,
            'name': request.name,
            'status': 'active',
            'subscription': request.subscription.model_dump(),
            'settings': {
                'timezone': request.timezone or 'Asia/Tokyo',
                'locale': request.locale or 'ja-JP',
                'features': {},
                'allowedDomains': request.allowed_domains or []
            },
            'services': [],
            'createdAt': now.isoformat(),
            'updatedAt': now.isoformat()
        }
        
        # Save to database
        created_tenant = await self.tenant_repo.create(tenant_data)
        
        return self._map_to_response(created_tenant)
    
    async def get_tenant(self, tenant_id: str) -> TenantResponse:
        """Get tenant by ID"""
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": ErrorCode.NOT_FOUND,
                    "message": "テナントが見つかりません"
                }
            )
        
        return self._map_to_response(tenant)
    
    async def update_tenant(
        self,
        tenant_id: str,
        request: TenantUpdate,
        updated_by: str = "system"
    ) -> TenantResponse:
        """Update tenant"""
        # Get existing tenant
        existing_tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not existing_tenant:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": ErrorCode.NOT_FOUND,
                    "message": "テナントが見つかりません"
                }
            )
        
        # Prepare update data
        update_data = {}
        
        if request.name is not None:
            update_data['name'] = request.name
        
        if request.status is not None:
            update_data['status'] = request.status.value
        
        if request.subscription is not None:
            update_data['subscription'] = request.subscription.model_dump()
        
        if request.allowed_domains is not None:
            validate_domain_list(request.allowed_domains)
            if 'settings' not in update_data:
                update_data['settings'] = existing_tenant.get('settings', {})
            update_data['settings']['allowedDomains'] = request.allowed_domains
        
        # Update tenant
        updated_tenant = await self.tenant_repo.update(tenant_id, update_data)
        
        return self._map_to_response(updated_tenant)
    
    async def delete_tenant(
        self,
        tenant_id: str,
        deleted_by: str = "system"
    ) -> bool:
        """Delete tenant (soft delete)"""
        # Verify tenant exists
        existing_tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not existing_tenant:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": ErrorCode.NOT_FOUND,
                    "message": "テナントが見つかりません"
                }
            )
        
        # Soft delete
        success = await self.tenant_repo.delete(tenant_id)
        
        return success
    
    async def list_tenants(
        self,
        status: Optional[str] = None,
        plan: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[TenantResponse]:
        """List tenants with filtering and pagination"""
        items, total_count = await self.tenant_repo.list_tenants(
            status=status,
            plan=plan,
            skip=skip,
            limit=limit
        )
        
        return [self._map_to_response(item) for item in items]
    
    async def assign_tenant_admin(
        self,
        tenant_id: str,
        request: AssignAdminRequest,
        assigned_by: str = "system"
    ) -> dict:
        """Assign tenant admin role to a user"""
        # Verify tenant exists
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": ErrorCode.NOT_FOUND,
                    "message": "テナントが見つかりません"
                }
            )
        
        # Check if relationship already exists
        existing = await self.tenant_user_repo.get_by_user_and_tenant(
            request.user_id,
            tenant_id
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": ErrorCode.CONFLICT,
                    "message": "ユーザーは既にこのテナントに関連付けられています"
                }
            )
        
        # Create tenant user relationship
        tenant_user = {
            'id': f"tenantuser-{uuid4()}",
            'userId': request.user_id,
            'tenantId': tenant_id,
            'roles': ['tenant-admin'],
            'permissions': ['users.*', 'services.*', 'tenants.read', 'tenants.update'],
            'status': 'active',
            'joinedAt': datetime.now(timezone.utc).isoformat(),
            'createdAt': datetime.now(timezone.utc).isoformat(),
            'updatedAt': datetime.now(timezone.utc).isoformat()
        }
        
        created = await self.tenant_user_repo.create(tenant_user)
        return created
    
    def _map_to_response(self, tenant_data: dict) -> TenantResponse:
        """Map database tenant to response schema"""
        subscription = SubscriptionSchema(**tenant_data['subscription'])
        settings = TenantSettingsSchema(**tenant_data['settings'])
        
        return TenantResponse(
            id=tenant_data['id'],
            tenant_id=tenant_data['tenantId'],
            name=tenant_data['name'],
            status=tenant_data['status'],
            subscription=subscription,
            settings=settings,
            services=tenant_data.get('services', []),
            created_at=datetime.fromisoformat(tenant_data['createdAt']),
            updated_at=datetime.fromisoformat(tenant_data['updatedAt']),
            deleted_at=datetime.fromisoformat(tenant_data['deletedAt']) if tenant_data.get('deletedAt') else None
        )


tenant_service = TenantService()
