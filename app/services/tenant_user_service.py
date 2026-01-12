"""User Management Service - TenantUser Service"""
from typing import List, Optional
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException
from app.schemas import (
    ErrorCode,
    TenantUserResponse,
    AddUserToTenantRequest,
)
from app.repositories.tenant_repository import tenant_repository, tenant_user_repository
from app.repositories.user_repository import user_repository
from app.utils import redis_client
import logging
import json

logger = logging.getLogger(__name__)

# Cache TTL in seconds
TENANT_USER_CACHE_TTL = 300  # 5 minutes


class TenantUserService:
    """TenantUser service for business logic"""

    def __init__(self):
        self.tenant_user_repo = tenant_user_repository
        self.tenant_repo = tenant_repository
        self.user_repo = user_repository

    async def add_user_to_tenant(
        self,
        tenant_id: str,
        request: AddUserToTenantRequest,
        assigned_by: str = "system",
    ) -> TenantUserResponse:
        """Add user to tenant"""
        # Verify tenant exists
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=404,
                detail={"code": ErrorCode.NOT_FOUND, "message": "テナントが見つかりません"},
            )

        # Verify user exists (check across all tenants)
        # For simplicity, we'll check if user exists in any tenant
        # In production, you might want a dedicated user lookup

        # Check if relationship already exists
        existing = await self.tenant_user_repo.get_by_user_and_tenant(
            request.user_id, tenant_id
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="ユーザーは既にこのテナントに所属しています",
            )

        # Create tenant user relationship
        now = datetime.now(timezone.utc)
        tenant_user = {
            "id": f"tenantuser-{uuid4()}",
            "userId": request.user_id,
            "tenantId": tenant_id,
            "roles": request.roles or ["user"],
            "permissions": request.permissions or [],
            "status": "active",
            "joinedAt": now.isoformat(),
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }

        created = await self.tenant_user_repo.create(tenant_user)

        # Invalidate user tenants cache
        await self._invalidate_user_tenants_cache(request.user_id)
        await self._invalidate_tenant_users_cache(tenant_id)

        return self._map_to_response(created)

    async def get_user_tenants(self, user_id: str) -> List[TenantUserResponse]:
        """Get user's tenants with Redis caching"""
        # Try to get from cache first
        cache_key = f"user:tenants:{user_id}"
        
        if redis_client.is_enabled():
            cached_data = redis_client.get_json(cache_key)
            if cached_data:
                logger.info(f"Cache hit for user tenants: {user_id}")
                return [TenantUserResponse(**item) for item in cached_data]

        # Cache miss, query database
        logger.info(f"Cache miss for user tenants: {user_id}")
        items = await self.tenant_user_repo.get_by_user_id(user_id)

        # Convert to response objects
        responses = [self._map_to_response(item) for item in items]

        # Cache the results
        if redis_client.is_enabled():
            cache_data = [response.model_dump() for response in responses]
            # Convert datetime to ISO format strings for JSON serialization
            for item in cache_data:
                if isinstance(item.get("joined_at"), datetime):
                    item["joined_at"] = item["joined_at"].isoformat()
                if isinstance(item.get("left_at"), datetime):
                    item["left_at"] = item["left_at"].isoformat()
                if isinstance(item.get("created_at"), datetime):
                    item["created_at"] = item["created_at"].isoformat()
                if isinstance(item.get("updated_at"), datetime):
                    item["updated_at"] = item["updated_at"].isoformat()
            
            redis_client.set_json(cache_key, cache_data, TENANT_USER_CACHE_TTL)

        return responses

    async def get_tenant_users(self, tenant_id: str) -> List[TenantUserResponse]:
        """Get tenant's users with Redis caching"""
        # Try to get from cache first
        cache_key = f"tenant:users:{tenant_id}"
        
        if redis_client.is_enabled():
            cached_data = redis_client.get_json(cache_key)
            if cached_data:
                logger.info(f"Cache hit for tenant users: {tenant_id}")
                return [TenantUserResponse(**item) for item in cached_data]

        # Cache miss, query database
        logger.info(f"Cache miss for tenant users: {tenant_id}")
        items = await self.tenant_user_repo.get_by_tenant_id(tenant_id)

        # Convert to response objects
        responses = [self._map_to_response(item) for item in items]

        # Cache the results
        if redis_client.is_enabled():
            cache_data = [response.model_dump() for response in responses]
            # Convert datetime to ISO format strings for JSON serialization
            for item in cache_data:
                if isinstance(item.get("joined_at"), datetime):
                    item["joined_at"] = item["joined_at"].isoformat()
                if isinstance(item.get("left_at"), datetime):
                    item["left_at"] = item["left_at"].isoformat()
                if isinstance(item.get("created_at"), datetime):
                    item["created_at"] = item["created_at"].isoformat()
                if isinstance(item.get("updated_at"), datetime):
                    item["updated_at"] = item["updated_at"].isoformat()
            
            redis_client.set_json(cache_key, cache_data, TENANT_USER_CACHE_TTL)

        return responses

    async def remove_user_from_tenant(
        self, tenant_id: str, user_id: str, removed_by: str = "system"
    ) -> bool:
        """Remove user from tenant (soft delete)"""
        # Get existing relationship
        tenant_user = await self.tenant_user_repo.get_by_user_and_tenant(
            user_id, tenant_id
        )
        if not tenant_user:
            raise HTTPException(
                status_code=404, detail="ユーザーはこのテナントに所属していません"
            )

        # Soft delete
        update_data = {
            "status": "inactive",
            "leftAt": datetime.now(timezone.utc).isoformat(),
        }

        await self.tenant_user_repo.update(tenant_user["id"], update_data)

        # Invalidate caches
        await self._invalidate_user_tenants_cache(user_id)
        await self._invalidate_tenant_users_cache(tenant_id)

        return True

    async def _invalidate_user_tenants_cache(self, user_id: str):
        """Invalidate user tenants cache"""
        if redis_client.is_enabled():
            cache_key = f"user:tenants:{user_id}"
            redis_client.delete(cache_key)
            logger.info(f"Invalidated cache for user tenants: {user_id}")

    async def _invalidate_tenant_users_cache(self, tenant_id: str):
        """Invalidate tenant users cache"""
        if redis_client.is_enabled():
            cache_key = f"tenant:users:{tenant_id}"
            redis_client.delete(cache_key)
            logger.info(f"Invalidated cache for tenant users: {tenant_id}")

    def _map_to_response(self, tenant_user_data: dict) -> TenantUserResponse:
        """Map database tenant user to response schema"""
        return TenantUserResponse(
            id=tenant_user_data["id"],
            user_id=tenant_user_data["userId"],
            tenant_id=tenant_user_data["tenantId"],
            roles=tenant_user_data.get("roles", []),
            permissions=tenant_user_data.get("permissions", []),
            status=tenant_user_data["status"],
            joined_at=datetime.fromisoformat(tenant_user_data["joinedAt"]),
            left_at=datetime.fromisoformat(tenant_user_data["leftAt"])
            if tenant_user_data.get("leftAt")
            else None,
            created_at=datetime.fromisoformat(tenant_user_data["createdAt"]),
            updated_at=datetime.fromisoformat(tenant_user_data["updatedAt"]),
        )


tenant_user_service = TenantUserService()
