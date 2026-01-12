"""Tenant Management Service - Validation Utilities"""
from typing import Optional, List
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


def validate_email_domain(email: str, tenant: dict) -> bool:
    """
    Validate email domain against tenant's allowed domains.
    
    Args:
        email: Email address to validate
        tenant: Tenant object containing settings with allowedDomains
    
    Returns:
        True if email domain is allowed
    
    Raises:
        HTTPException: If validation fails
    """
    # Get allowed domains from tenant settings
    allowed_domains = tenant.get('settings', {}).get('allowedDomains', [])
    
    # If no allowed domains configured, skip validation
    if not allowed_domains:
        raise HTTPException(
            status_code=400,
            detail="テナントに許可ドメインが設定されていません"
        )
    
    # Extract domain from email
    if '@' not in email:
        raise HTTPException(
            status_code=400,
            detail="無効なメールアドレス"
        )
    
    domain = email.split('@')[1]
    
    # Normalize domains for case-insensitive comparison
    domain_lower = domain.lower()
    allowed_lower = [
        d.lower().lstrip('@') for d in allowed_domains
    ]
    
    # Check if domain is in allowed list
    if domain_lower not in allowed_lower:
        raise HTTPException(
            status_code=400,
            detail=f"許可されたドメイン（{', '.join(allowed_domains)}）のメールアドレスを使用してください"
        )
    
    return True


def normalize_domain(domain: str) -> str:
    """
    Normalize domain string by removing @ prefix and converting to lowercase.
    
    Args:
        domain: Domain string (e.g., "@example.com" or "example.com")
    
    Returns:
        Normalized domain string (e.g., "example.com")
    """
    return domain.lower().lstrip('@')


def validate_domain_list(domains: List[str]) -> bool:
    """
    Validate a list of domain strings.
    
    Args:
        domains: List of domain strings
    
    Returns:
        True if all domains are valid
    
    Raises:
        HTTPException: If any domain is invalid
    """
    if not domains:
        return True
    
    for domain in domains:
        # Remove @ if present
        clean_domain = domain.lstrip('@')
        
        # Basic validation
        if not clean_domain or ' ' in clean_domain:
            raise HTTPException(
                status_code=400,
                detail=f"無効なドメイン形式: {domain}"
            )
        
        # Check for at least one dot
        if '.' not in clean_domain:
            raise HTTPException(
                status_code=400,
                detail=f"無効なドメイン形式: {domain}（ドメインには少なくとも1つのドットが必要です）"
            )
    
    return True
