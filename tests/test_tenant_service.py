"""Test Tenant Service"""
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.tenant_service import TenantService
from app.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    SubscriptionSchema,
    SubscriptionPlan,
    TenantStatus,
    AssignAdminRequest
)


@pytest.fixture
def tenant_service():
    """Create tenant service instance"""
    service = TenantService()
    service.tenant_repo = MagicMock()
    service.tenant_user_repo = MagicMock()
    return service


@pytest.fixture
def sample_tenant_data():
    """Sample tenant data"""
    return {
        "id": f"tenant-{uuid4()}",
        "tenantId": f"tenant-{uuid4()}",
        "name": "Test Tenant",
        "status": "active",
        "subscription": {
            "plan": "professional",
            "start_date": None,
            "end_date": None,
            "max_users": 100,
            "features": []
        },
        "settings": {
            "timezone": "Asia/Tokyo",
            "locale": "ja-JP",
            "features": {},
            "allowedDomains": []
        },
        "services": [],
        "createdAt": datetime.utcnow().isoformat(),
        "updatedAt": datetime.utcnow().isoformat()
    }


@pytest.mark.asyncio
async def test_create_tenant_success(tenant_service):
    """Test successful tenant creation"""
    # Arrange
    subscription = SubscriptionSchema(
        plan=SubscriptionPlan.PROFESSIONAL,
        max_users=100
    )
    request = TenantCreate(
        name="Test Tenant",
        subscription=subscription,
        allowed_domains=["example.com", "test.com"]
    )
    
    # Mock create to return what was passed in (simulating CosmosDB behavior)
    async def mock_create(data):
        return data
    
    tenant_service.tenant_repo.create = mock_create
    
    # Act
    result = await tenant_service.create_tenant(request, "admin")
    
    # Assert
    assert result.name == "Test Tenant"
    assert result.status == "active"
    assert result.settings.allowed_domains == ["example.com", "test.com"]


@pytest.mark.asyncio
async def test_get_tenant_success(tenant_service, sample_tenant_data):
    """Test successful tenant retrieval"""
    # Arrange
    tenant_service.tenant_repo.get_by_id = AsyncMock(return_value=sample_tenant_data)
    
    # Act
    result = await tenant_service.get_tenant(sample_tenant_data["id"])
    
    # Assert
    assert result.id == sample_tenant_data["id"]
    assert result.name == sample_tenant_data["name"]


@pytest.mark.asyncio
async def test_get_tenant_not_found(tenant_service):
    """Test tenant retrieval when tenant not found"""
    from fastapi import HTTPException
    
    # Arrange
    tenant_service.tenant_repo.get_by_id = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await tenant_service.get_tenant("nonexistent-id")
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_tenant_success(tenant_service, sample_tenant_data):
    """Test successful tenant update"""
    # Arrange
    update_request = TenantUpdate(
        name="Updated Tenant",
        status=TenantStatus.ACTIVE
    )
    
    updated_data = sample_tenant_data.copy()
    updated_data["name"] = "Updated Tenant"
    
    tenant_service.tenant_repo.get_by_id = AsyncMock(return_value=sample_tenant_data)
    tenant_service.tenant_repo.update = AsyncMock(return_value=updated_data)
    
    # Act
    result = await tenant_service.update_tenant(
        sample_tenant_data["id"],
        update_request,
        "admin"
    )
    
    # Assert
    assert result.name == "Updated Tenant"
    tenant_service.tenant_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_delete_tenant_success(tenant_service, sample_tenant_data):
    """Test successful tenant deletion"""
    # Arrange
    tenant_service.tenant_repo.get_by_id = AsyncMock(return_value=sample_tenant_data)
    tenant_service.tenant_repo.delete = AsyncMock(return_value=True)
    
    # Act
    result = await tenant_service.delete_tenant(
        sample_tenant_data["id"],
        "admin"
    )
    
    # Assert
    assert result is True
    tenant_service.tenant_repo.delete.assert_called_once()


@pytest.mark.asyncio
async def test_list_tenants(tenant_service, sample_tenant_data):
    """Test listing tenants"""
    # Arrange
    tenant_service.tenant_repo.list_tenants = AsyncMock(
        return_value=([sample_tenant_data], 1)
    )
    
    # Act
    result = await tenant_service.list_tenants(skip=0, limit=50)
    
    # Assert
    assert len(result) == 1
    assert result[0].name == "Test Tenant"


@pytest.mark.asyncio
async def test_assign_tenant_admin_success(tenant_service, sample_tenant_data):
    """Test successful tenant admin assignment"""
    # Arrange
    request = AssignAdminRequest(user_id="user-123")
    
    tenant_user_data = {
        "id": f"tenantuser-{uuid4()}",
        "userId": "user-123",
        "tenantId": sample_tenant_data["id"],
        "roles": ["tenant-admin"],
        "permissions": ["users.*", "services.*", "tenants.read", "tenants.update"],
        "status": "active",
        "joinedAt": datetime.utcnow().isoformat()
    }
    
    tenant_service.tenant_repo.get_by_id = AsyncMock(return_value=sample_tenant_data)
    tenant_service.tenant_user_repo.get_by_user_and_tenant = AsyncMock(return_value=None)
    tenant_service.tenant_user_repo.create = AsyncMock(return_value=tenant_user_data)
    
    # Act
    result = await tenant_service.assign_tenant_admin(
        sample_tenant_data["id"],
        request,
        "admin"
    )
    
    # Assert
    assert result["userId"] == "user-123"
    assert "tenant-admin" in result["roles"]
    tenant_service.tenant_user_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_assign_tenant_admin_already_exists(tenant_service, sample_tenant_data):
    """Test tenant admin assignment when relationship already exists"""
    from fastapi import HTTPException
    
    # Arrange
    request = AssignAdminRequest(user_id="user-123")
    
    existing_tenant_user = {
        "id": "existing-id",
        "userId": "user-123",
        "tenantId": sample_tenant_data["id"]
    }
    
    tenant_service.tenant_repo.get_by_id = AsyncMock(return_value=sample_tenant_data)
    tenant_service.tenant_user_repo.get_by_user_and_tenant = AsyncMock(
        return_value=existing_tenant_user
    )
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await tenant_service.assign_tenant_admin(
            sample_tenant_data["id"],
            request,
            "admin"
        )
    
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_create_tenant_with_invalid_domains(tenant_service):
    """Test tenant creation with invalid domains"""
    from fastapi import HTTPException
    
    # Arrange
    subscription = SubscriptionSchema(
        plan=SubscriptionPlan.BASIC
    )
    request = TenantCreate(
        name="Test Tenant",
        subscription=subscription,
        allowed_domains=["invalid domain with spaces"]
    )
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await tenant_service.create_tenant(request, "admin")
    
    assert exc_info.value.status_code == 400
