"""Test Validation Utilities"""
import pytest
from fastapi import HTTPException

from app.utils.validation import (
    validate_email_domain,
    normalize_domain,
    validate_domain_list
)


def test_normalize_domain():
    """Test domain normalization"""
    assert normalize_domain("@example.com") == "example.com"
    assert normalize_domain("example.com") == "example.com"
    assert normalize_domain("@EXAMPLE.COM") == "example.com"
    assert normalize_domain("EXAMPLE.COM") == "example.com"


def test_validate_domain_list_valid():
    """Test validation of valid domain list"""
    domains = ["example.com", "test.com", "@domain.org"]
    assert validate_domain_list(domains) is True


def test_validate_domain_list_empty():
    """Test validation of empty domain list"""
    assert validate_domain_list([]) is True


def test_validate_domain_list_invalid_no_dot():
    """Test validation of domain without dot"""
    with pytest.raises(HTTPException) as exc_info:
        validate_domain_list(["invaliddomain"])
    
    assert exc_info.value.status_code == 400
    assert "少なくとも1つのドットが必要" in exc_info.value.detail


def test_validate_domain_list_invalid_with_spaces():
    """Test validation of domain with spaces"""
    with pytest.raises(HTTPException) as exc_info:
        validate_domain_list(["invalid domain.com"])
    
    assert exc_info.value.status_code == 400
    assert "無効なドメイン形式" in exc_info.value.detail


def test_validate_email_domain_success():
    """Test successful email domain validation"""
    tenant = {
        "settings": {
            "allowedDomains": ["example.com", "test.com"]
        }
    }
    
    assert validate_email_domain("user@example.com", tenant) is True
    assert validate_email_domain("admin@test.com", tenant) is True


def test_validate_email_domain_case_insensitive():
    """Test email domain validation is case-insensitive"""
    tenant = {
        "settings": {
            "allowedDomains": ["Example.Com"]
        }
    }
    
    assert validate_email_domain("user@example.com", tenant) is True
    assert validate_email_domain("user@EXAMPLE.COM", tenant) is True


def test_validate_email_domain_with_at_prefix():
    """Test email domain validation with @ prefix in allowed domains"""
    tenant = {
        "settings": {
            "allowedDomains": ["@example.com"]
        }
    }
    
    assert validate_email_domain("user@example.com", tenant) is True


def test_validate_email_domain_no_allowed_domains():
    """Test email validation when no allowed domains configured"""
    tenant = {
        "settings": {
            "allowedDomains": []
        }
    }
    
    with pytest.raises(HTTPException) as exc_info:
        validate_email_domain("user@example.com", tenant)
    
    assert exc_info.value.status_code == 400
    assert "許可ドメインが設定されていません" in exc_info.value.detail


def test_validate_email_domain_invalid_email():
    """Test email validation with invalid email format"""
    tenant = {
        "settings": {
            "allowedDomains": ["example.com"]
        }
    }
    
    with pytest.raises(HTTPException) as exc_info:
        validate_email_domain("invalid-email", tenant)
    
    assert exc_info.value.status_code == 400
    assert "無効なメールアドレス" in exc_info.value.detail


def test_validate_email_domain_not_allowed():
    """Test email validation with domain not in allowed list"""
    tenant = {
        "settings": {
            "allowedDomains": ["example.com"]
        }
    }
    
    with pytest.raises(HTTPException) as exc_info:
        validate_email_domain("user@notallowed.com", tenant)
    
    assert exc_info.value.status_code == 400
    assert "許可されたドメイン" in exc_info.value.detail
    assert "example.com" in exc_info.value.detail
