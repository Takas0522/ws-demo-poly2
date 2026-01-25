"""Unit tests for Tenant model."""
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.models.tenant import Tenant


class TestTenant:
    """Test cases for Tenant model."""

    def test_tenant_creation_valid(self) -> None:
        """Test creating a valid Tenant instance."""
        tenant = Tenant(
            id="tenant-001",
            name="Test Tenant",
            isPrivileged=False,
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
        )
        
        assert tenant.id == "tenant-001"
        assert tenant.name == "Test Tenant"
        assert tenant.isPrivileged is False
        assert isinstance(tenant.createdAt, datetime)
        assert isinstance(tenant.updatedAt, datetime)

    def test_tenant_privileged_default(self) -> None:
        """Test that isPrivileged defaults to False."""
        tenant = Tenant(
            id="tenant-002",
            name="Regular Tenant",
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
        )
        
        assert tenant.isPrivileged is False

    def test_tenant_privileged_tenant(self) -> None:
        """Test creating a privileged tenant."""
        tenant = Tenant(
            id="tenant-001",
            name="特権管理テナント",
            isPrivileged=True,
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
        )
        
        assert tenant.isPrivileged is True

    def test_tenant_missing_required_fields(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            Tenant(name="Test Tenant")  # type: ignore

    def test_tenant_model_dump(self) -> None:
        """Test model serialization to dict."""
        now = datetime.now(timezone.utc)
        tenant = Tenant(
            id="tenant-001",
            name="Test Tenant",
            isPrivileged=True,
            createdAt=now,
            updatedAt=now,
        )
        
        data = tenant.model_dump(mode="json")
        
        assert data["id"] == "tenant-001"
        assert data["name"] == "Test Tenant"
        assert data["isPrivileged"] is True
        assert "createdAt" in data
        assert "updatedAt" in data
