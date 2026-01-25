"""Unit tests for AllowedDomain model."""
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.models.allowed_domain import AllowedDomain


class TestAllowedDomain:
    """Test cases for AllowedDomain model."""

    def test_allowed_domain_creation_valid(self) -> None:
        """Test creating a valid AllowedDomain instance."""
        domain = AllowedDomain(
            id="ad-001",
            tenantId="tenant-001",
            domain="example.com",
            createdAt=datetime.now(timezone.utc),
        )
        
        assert domain.id == "ad-001"
        assert domain.tenantId == "tenant-001"
        assert domain.domain == "example.com"
        assert isinstance(domain.createdAt, datetime)

    def test_allowed_domain_valid_formats(self) -> None:
        """Test various valid domain formats."""
        valid_domains = [
            "example.com",
            "sub.example.com",
            "example.co.jp",
            "my-domain.com",
            "123domain.com",
            "a1-b2.example.org",
            "a.com",  # Single letter domain part
            "x.y.com",  # Single letter subdomain
        ]
        
        for domain_str in valid_domains:
            domain = AllowedDomain(
                id="ad-001",
                tenantId="tenant-001",
                domain=domain_str,
                createdAt=datetime.now(timezone.utc),
            )
            assert domain.domain == domain_str

    def test_allowed_domain_invalid_formats(self) -> None:
        """Test that invalid domain formats raise ValidationError."""
        invalid_domains = [
            "-example.com",  # Cannot start with hyphen
            "example",  # Missing TLD
            "example.",  # Missing TLD name
            "example.c",  # TLD too short
            ".example.com",  # Cannot start with dot
            "example..com",  # Double dot
            "",  # Empty string
        ]
        
        for domain_str in invalid_domains:
            with pytest.raises(ValidationError) as exc_info:
                AllowedDomain(
                    id="ad-001",
                    tenantId="tenant-001",
                    domain=domain_str,
                    createdAt=datetime.now(timezone.utc),
                )
            assert "Invalid domain format" in str(exc_info.value)

    def test_allowed_domain_missing_required_fields(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            AllowedDomain(tenantId="tenant-001", domain="example.com")  # type: ignore

    def test_allowed_domain_model_dump(self) -> None:
        """Test model serialization to dict."""
        now = datetime.now(timezone.utc)
        domain = AllowedDomain(
            id="ad-001",
            tenantId="tenant-001",
            domain="example.com",
            createdAt=now,
        )
        
        data = domain.model_dump(mode="json")
        
        assert data["id"] == "ad-001"
        assert data["tenantId"] == "tenant-001"
        assert data["domain"] == "example.com"
        assert "createdAt" in data
