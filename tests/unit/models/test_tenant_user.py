"""Unit tests for TenantUser model."""
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.models.tenant_user import TenantUser


class TestTenantUser:
    """Test cases for TenantUser model."""

    def test_tenant_user_creation_valid(self) -> None:
        """Test creating a valid TenantUser instance."""
        tenant_user = TenantUser(
            id="tu-001",
            tenantId="tenant-001",
            userId="user-001",
            addedAt=datetime.now(timezone.utc),
        )
        
        assert tenant_user.id == "tu-001"
        assert tenant_user.tenantId == "tenant-001"
        assert tenant_user.userId == "user-001"
        assert isinstance(tenant_user.addedAt, datetime)

    def test_tenant_user_missing_required_fields(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            TenantUser(tenantId="tenant-001", userId="user-001")  # type: ignore

    def test_tenant_user_model_dump(self) -> None:
        """Test model serialization to dict."""
        now = datetime.now(timezone.utc)
        tenant_user = TenantUser(
            id="tu-001",
            tenantId="tenant-001",
            userId="user-001",
            addedAt=now,
        )
        
        data = tenant_user.model_dump(mode="json")
        
        assert data["id"] == "tu-001"
        assert data["tenantId"] == "tenant-001"
        assert data["userId"] == "user-001"
        assert "addedAt" in data
