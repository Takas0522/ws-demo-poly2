"""Test User Service"""
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.user_service import UserService
from app.schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserStatus,
    UserProfileSchema
)


@pytest.fixture
def user_service():
    """Create user service instance"""
    service = UserService()
    service.user_repo = MagicMock()
    service.audit_repo = MagicMock()
    return service


@pytest.fixture
def sample_user_data():
    """Sample user data"""
    return {
        "id": str(uuid4()),
        "tenantId": "tenant-123",
        "email": "test@example.com",
        "username": "testuser",
        "firstName": "Test",
        "lastName": "User",
        "profile": {},
        "status": "ACTIVE",
        "createdAt": datetime.utcnow().isoformat(),
        "updatedAt": datetime.utcnow().isoformat(),
        "createdBy": "admin",
        "updatedBy": "admin"
    }


@pytest.mark.asyncio
async def test_create_user_success(user_service, sample_user_data):
    """Test successful user creation"""
    # Arrange
    request = CreateUserRequest(
        tenant_id="tenant-123",
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    
    user_service.user_repo.get_by_email = AsyncMock(return_value=None)
    user_service.user_repo.create = AsyncMock(return_value=sample_user_data)
    user_service.audit_repo.create = AsyncMock(return_value={})
    
    # Act
    result = await user_service.create_user(request, "admin")
    
    # Assert
    assert result.email == "test@example.com"
    assert result.username == "testuser"
    assert result.tenant_id == "tenant-123"
    user_service.user_repo.create.assert_called_once()
    user_service.audit_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_duplicate_email(user_service, sample_user_data):
    """Test user creation with duplicate email"""
    from fastapi import HTTPException
    
    # Arrange
    request = CreateUserRequest(
        tenant_id="tenant-123",
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    
    user_service.user_repo.get_by_email = AsyncMock(return_value=sample_user_data)
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await user_service.create_user(request, "admin")
    
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_get_user_success(user_service, sample_user_data):
    """Test successful user retrieval"""
    # Arrange
    user_service.user_repo.get_by_id = AsyncMock(return_value=sample_user_data)
    
    # Act
    result = await user_service.get_user(sample_user_data["id"], "tenant-123")
    
    # Assert
    assert result.id == sample_user_data["id"]
    assert result.email == sample_user_data["email"]


@pytest.mark.asyncio
async def test_get_user_not_found(user_service):
    """Test user retrieval when user not found"""
    from fastapi import HTTPException
    
    # Arrange
    user_service.user_repo.get_by_id = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await user_service.get_user("nonexistent-id", "tenant-123")
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_user_success(user_service, sample_user_data):
    """Test successful user update"""
    # Arrange
    update_request = UpdateUserRequest(
        first_name="Updated",
        last_name="Name"
    )
    
    updated_data = sample_user_data.copy()
    updated_data["firstName"] = "Updated"
    updated_data["lastName"] = "Name"
    
    user_service.user_repo.get_by_id = AsyncMock(return_value=sample_user_data)
    user_service.user_repo.update = AsyncMock(return_value=updated_data)
    user_service.audit_repo.create = AsyncMock(return_value={})
    
    # Act
    result = await user_service.update_user(
        sample_user_data["id"],
        "tenant-123",
        update_request,
        "admin"
    )
    
    # Assert
    assert result.first_name == "Updated"
    assert result.last_name == "Name"
    user_service.user_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_delete_user_success(user_service, sample_user_data):
    """Test successful user deletion"""
    # Arrange
    user_service.user_repo.get_by_id = AsyncMock(return_value=sample_user_data)
    user_service.user_repo.delete = AsyncMock(return_value=True)
    user_service.audit_repo.create = AsyncMock(return_value={})
    
    # Act
    result = await user_service.delete_user(
        sample_user_data["id"],
        "tenant-123",
        "admin"
    )
    
    # Assert
    assert result is True
    user_service.user_repo.delete.assert_called_once()
    user_service.audit_repo.create.assert_called_once()
