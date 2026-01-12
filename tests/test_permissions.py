"""Test Permission Utilities"""
import pytest
from fastapi import HTTPException

from app.utils.permissions import check_permission


def test_check_permission_exact_match():
    """Test permission check with exact match"""
    user = {
        "permissions": ["tenants.create", "users.read"],
        "roles": []
    }
    
    assert check_permission(user, "tenants.create") is True
    assert check_permission(user, "users.read") is True


def test_check_permission_wildcard():
    """Test permission check with wildcard"""
    user = {
        "permissions": ["tenants.*", "users.*"],
        "roles": []
    }
    
    assert check_permission(user, "tenants.create") is True
    assert check_permission(user, "tenants.update") is True
    assert check_permission(user, "tenants.delete") is True
    assert check_permission(user, "users.read") is True


def test_check_permission_global_admin():
    """Test permission check for global admin"""
    user = {
        "permissions": [],
        "roles": ["global-admin"]
    }
    
    assert check_permission(user, "tenants.create") is True
    assert check_permission(user, "users.delete") is True
    assert check_permission(user, "any.permission") is True


def test_check_permission_no_permission():
    """Test permission check without required permission"""
    user = {
        "permissions": ["users.read"],
        "roles": []
    }
    
    assert check_permission(user, "tenants.create") is False


def test_check_permission_global_scope_requires_global_admin():
    """Test global scope requires global admin role"""
    user = {
        "permissions": ["tenants.create"],
        "roles": ["tenant-admin"]
    }
    
    # Regular permissions don't work for global scope
    assert check_permission(user, "tenants.create", scope="global") is False
    
    # Global admin works for global scope
    global_admin = {
        "permissions": [],
        "roles": ["global-admin"]
    }
    assert check_permission(global_admin, "tenants.create", scope="global") is True


def test_check_permission_tenant_scope():
    """Test tenant scope permission check"""
    user = {
        "permissions": ["tenants.read"],
        "roles": ["tenant-admin"]
    }
    
    assert check_permission(user, "tenants.read", scope="tenant") is True


def test_check_permission_no_user():
    """Test permission check with no user"""
    assert check_permission(None, "any.permission") is False


def test_check_permission_empty_permissions():
    """Test permission check with empty permissions"""
    user = {
        "permissions": [],
        "roles": []
    }
    
    assert check_permission(user, "tenants.create") is False
