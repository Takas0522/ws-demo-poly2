"""Test User Schemas"""
import pytest
from pydantic import ValidationError
from app.schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserStatus,
    UserProfileSchema
)


def test_create_user_request_valid():
    """Test valid create user request"""
    request = CreateUserRequest(
        tenant_id="tenant-123",
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    
    assert request.tenant_id == "tenant-123"
    assert request.email == "test@example.com"
    assert request.username == "testuser"
    assert request.status == UserStatus.ACTIVE


def test_create_user_request_invalid_email():
    """Test create user request with invalid email"""
    with pytest.raises(ValidationError):
        CreateUserRequest(
            tenant_id="tenant-123",
            email="invalid-email",
            username="testuser",
            first_name="Test",
            last_name="User"
        )


def test_create_user_request_short_username():
    """Test create user request with too short username"""
    with pytest.raises(ValidationError):
        CreateUserRequest(
            tenant_id="tenant-123",
            email="test@example.com",
            username="ab",  # Too short
            first_name="Test",
            last_name="User"
        )


def test_update_user_request_valid():
    """Test valid update user request"""
    request = UpdateUserRequest(
        email="newemail@example.com",
        status=UserStatus.INACTIVE
    )
    
    assert request.email == "newemail@example.com"
    assert request.status == UserStatus.INACTIVE


def test_user_profile_schema():
    """Test user profile schema"""
    profile = UserProfileSchema(
        phone_number="+81-90-1234-5678",
        department="Engineering",
        job_title="Software Engineer"
    )
    
    assert profile.phone_number == "+81-90-1234-5678"
    assert profile.department == "Engineering"
    assert profile.job_title == "Software Engineer"
