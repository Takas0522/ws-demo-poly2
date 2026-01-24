"""Test TenantUser Service"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.services.tenant_user_service import TenantUserService, tenant_user_service
from app.schemas import AddUserToTenantRequest, TenantUserResponse


@pytest.fixture
def tenant_user_service_instance():
    """Create tenant user service instance"""
    service = TenantUserService()
    service.tenant_user_repo = MagicMock()
    service.tenant_repo = MagicMock()
    service.user_repo = MagicMock()
    return service


@pytest.fixture
def sample_tenant_user_data():
    """Sample tenant user data"""
    return {
        "id": f"tenantuser-{uuid4()}",
        "userId": f"user-{uuid4()}",
        "tenantId": "tenant-123",
        "roles": ["user"],
        "permissions": [],
        "status": "active",
        "joinedAt": datetime.now(timezone.utc).isoformat(),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_tenant_data():
    """Sample tenant data"""
    return {
        "id": "tenant-123",
        "tenantId": "tenant-123",
        "name": "Test Tenant",
        "status": "active",
        "subscription": {"plan": "basic"},
        "settings": {},
    }


@pytest.mark.asyncio
async def test_add_user_to_tenant_success(
    tenant_user_service_instance, sample_tenant_data, sample_tenant_user_data
):
    """Test successful add user to tenant"""
    request = AddUserToTenantRequest(
        user_id="user-123",
        roles=["user"],
        permissions=[]
    )

    tenant_user_service_instance.tenant_repo.get_by_id = AsyncMock(return_value=sample_tenant_data)
    tenant_user_service_instance.tenant_user_repo.get_by_user_and_tenant = AsyncMock(return_value=None)
    tenant_user_service_instance.tenant_user_repo.create = AsyncMock(return_value=sample_tenant_user_data)

    result = await tenant_user_service_instance.add_user_to_tenant(
        "tenant-123", request, "admin"
    )

    assert isinstance(result, TenantUserResponse)
    assert result.tenant_id == "tenant-123"
    assert result.status == "active"


@pytest.mark.asyncio
async def test_add_user_to_tenant_not_found(tenant_user_service_instance):
    """Test add user to tenant when tenant not found"""
    request = AddUserToTenantRequest(
        user_id="user-123",
        roles=["user"]
    )

    tenant_user_service_instance.tenant_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await tenant_user_service_instance.add_user_to_tenant(
            "tenant-123", request, "admin"
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_add_user_to_tenant_duplicate(
    tenant_user_service_instance, sample_tenant_data, sample_tenant_user_data
):
    """Test add user to tenant when user already exists"""
    request = AddUserToTenantRequest(
        user_id="user-123",
        roles=["user"]
    )

    tenant_user_service_instance.tenant_repo.get_by_id = AsyncMock(return_value=sample_tenant_data)
    tenant_user_service_instance.tenant_user_repo.get_by_user_and_tenant = AsyncMock(
        return_value=sample_tenant_user_data
    )

    with pytest.raises(HTTPException) as exc_info:
        await tenant_user_service_instance.add_user_to_tenant(
            "tenant-123", request, "admin"
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_user_tenants(tenant_user_service_instance, sample_tenant_user_data):
    """Test get user tenants"""
    user_id = "user-123"

    tenant_user_service_instance.tenant_user_repo.get_by_user_id = AsyncMock(
        return_value=[sample_tenant_user_data]
    )

    result = await tenant_user_service_instance.get_user_tenants(user_id)

    assert len(result) == 1
    assert isinstance(result[0], TenantUserResponse)


@pytest.mark.asyncio
async def test_get_tenant_users(tenant_user_service_instance, sample_tenant_user_data):
    """Test get tenant users"""
    tenant_id = "tenant-123"

    tenant_user_service_instance.tenant_user_repo.get_by_tenant_id = AsyncMock(
        return_value=[sample_tenant_user_data]
    )

        result = await tenant_user_service_instance.get_tenant_users(tenant_id)

        assert len(result) == 1
        assert isinstance(result[0], TenantUserResponse)


@pytest.mark.asyncio
async def test_remove_user_from_tenant_success(
    tenant_user_service_instance, sample_tenant_user_data
):
    """Test successful remove user from tenant"""
    tenant_id = "tenant-123"
    user_id = "user-123"

    tenant_user_service_instance.tenant_user_repo.get_by_user_and_tenant = AsyncMock(
        return_value=sample_tenant_user_data
    )
    tenant_user_service_instance.tenant_user_repo.update = AsyncMock(
        return_value=sample_tenant_user_data
    )

    result = await tenant_user_service_instance.remove_user_from_tenant(
        tenant_id, user_id, "admin"
    )

    assert result is True
    tenant_user_service_instance.tenant_user_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_remove_user_from_tenant_not_found(tenant_user_service_instance):
    """Test remove user from tenant when relationship not found"""
    tenant_id = "tenant-123"
    user_id = "user-123"

    tenant_user_service_instance.tenant_user_repo.get_by_user_and_tenant = AsyncMock(
        return_value=None
    )

    with pytest.raises(HTTPException) as exc_info:
        await tenant_user_service_instance.remove_user_from_tenant(
            tenant_id, user_id, "admin"
        )

    assert exc_info.value.status_code == 404
