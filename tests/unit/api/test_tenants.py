"""
Unit tests for tenant API endpoints.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.models.tenant import Tenant

client = TestClient(app)


# Mock data
MOCK_TENANT_1 = Tenant(
    id="tenant-001",
    name="特権管理テナント",
    isPrivileged=True,
    createdAt=datetime(2026, 1, 1, 0, 0, 0),
    updatedAt=datetime(2026, 1, 1, 0, 0, 0),
)

MOCK_TENANT_2 = Tenant(
    id="tenant-002",
    name="通常テナント",
    isPrivileged=False,
    createdAt=datetime(2026, 1, 2, 0, 0, 0),
    updatedAt=datetime(2026, 1, 2, 0, 0, 0),
)

MOCK_USER_GLOBAL_ADMIN = {
    "sub": "user-001",
    "email": "admin@example.com",
    "role": "全体管理者",
}

MOCK_USER_ADMIN = {
    "sub": "user-002",
    "email": "manager@example.com",
    "role": "管理者",
}

MOCK_USER_VIEWER = {
    "sub": "user-003",
    "email": "viewer@example.com",
    "role": "閲覧者",
}


class TestListTenants:
    """Tests for GET /api/tenants endpoint."""

    @pytest.mark.asyncio
    async def test_list_tenants_success(self) -> None:
        """Test successful tenant list retrieval."""
        with patch("app.services.auth_client.auth_client.verify_token", new_callable=AsyncMock) as mock_verify:
            with patch("app.repositories.tenant_repository.tenant_repository.get_all", new_callable=AsyncMock) as mock_get_all:
                with patch("app.repositories.tenant_repository.tenant_repository.get_user_count", new_callable=AsyncMock) as mock_user_count:
                    mock_verify.return_value = MOCK_USER_VIEWER
                    mock_get_all.return_value = ([MOCK_TENANT_1, MOCK_TENANT_2], 2)
                    mock_user_count.side_effect = [5, 3]
                    
                    response = client.get(
                        "/api/tenants",
                        headers={"Authorization": "Bearer mock-token"},
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert len(data["data"]) == 2
                    assert data["data"][0]["id"] == "tenant-001"
                    assert data["data"][0]["userCount"] == 5
                    assert data["data"][1]["id"] == "tenant-002"
                    assert data["data"][1]["userCount"] == 3
                    assert data["pagination"]["totalItems"] == 2
                    assert data["pagination"]["totalPages"] == 1

    @pytest.mark.asyncio
    async def test_list_tenants_pagination(self) -> None:
        """Test tenant list with pagination."""
        with patch("app.services.auth_client.auth_client.verify_token", new_callable=AsyncMock) as mock_verify:
            with patch("app.repositories.tenant_repository.tenant_repository.get_all", new_callable=AsyncMock) as mock_get_all:
                with patch("app.repositories.tenant_repository.tenant_repository.get_user_count", new_callable=AsyncMock) as mock_user_count:
                    mock_verify.return_value = MOCK_USER_ADMIN
                    mock_get_all.return_value = ([MOCK_TENANT_1], 5)
                    mock_user_count.return_value = 2
                    
                    response = client.get(
                        "/api/tenants?page=1&pageSize=1",
                        headers={"Authorization": "Bearer mock-token"},
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["pagination"]["page"] == 1
                    assert data["pagination"]["pageSize"] == 1
                    assert data["pagination"]["totalItems"] == 5
                    assert data["pagination"]["totalPages"] == 5

    @pytest.mark.asyncio
    async def test_list_tenants_unauthorized(self) -> None:
        """Test tenant list without authentication."""
        response = client.get("/api/tenants")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_list_tenants_invalid_token(self) -> None:
        """Test tenant list with invalid token."""
        with patch("app.services.auth_client.auth_client.verify_token", new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = None
            
            response = client.get(
                "/api/tenants",
                headers={"Authorization": "Bearer invalid-token"},
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetTenant:
    """Tests for GET /api/tenants/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_tenant_success(self) -> None:
        """Test successful tenant detail retrieval."""
        with patch("app.services.auth_client.auth_client.verify_token", new_callable=AsyncMock) as mock_verify:
            with patch("app.repositories.tenant_repository.tenant_repository.get_by_id", new_callable=AsyncMock) as mock_get_by_id:
                mock_verify.return_value = MOCK_USER_VIEWER
                mock_get_by_id.return_value = MOCK_TENANT_1
                
                response = client.get(
                    "/api/tenants/tenant-001",
                    headers={"Authorization": "Bearer mock-token"},
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["data"]["id"] == "tenant-001"
                assert data["data"]["name"] == "特権管理テナント"
                assert data["data"]["isPrivileged"] is True

    @pytest.mark.asyncio
    async def test_get_tenant_not_found(self) -> None:
        """Test tenant detail with non-existent ID."""
        with patch("app.services.auth_client.auth_client.verify_token", new_callable=AsyncMock) as mock_verify:
            with patch("app.repositories.tenant_repository.tenant_repository.get_by_id", new_callable=AsyncMock) as mock_get_by_id:
                mock_verify.return_value = MOCK_USER_VIEWER
                mock_get_by_id.return_value = None
                
                response = client.get(
                    "/api/tenants/non-existent",
                    headers={"Authorization": "Bearer mock-token"},
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_tenant_unauthorized(self) -> None:
        """Test tenant detail without authentication."""
        response = client.get("/api/tenants/tenant-001")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateTenant:
    """Tests for PUT /api/tenants/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_tenant_by_admin_regular_tenant(self) -> None:
        """Test regular tenant update by admin."""
        updated_tenant = Tenant(
            id="tenant-002",
            name="更新されたテナント",
            isPrivileged=False,
            createdAt=datetime(2026, 1, 2, 0, 0, 0),
            updatedAt=datetime(2026, 1, 3, 0, 0, 0),
        )
        
        with patch("app.services.auth_client.auth_client.verify_token", new_callable=AsyncMock) as mock_verify:
            with patch("app.repositories.tenant_repository.tenant_repository.get_by_id", new_callable=AsyncMock) as mock_get_by_id:
                with patch("app.repositories.tenant_repository.tenant_repository.update", new_callable=AsyncMock) as mock_update:
                    mock_verify.return_value = MOCK_USER_ADMIN
                    mock_get_by_id.return_value = MOCK_TENANT_2
                    mock_update.return_value = updated_tenant
                    
                    response = client.put(
                        "/api/tenants/tenant-002",
                        headers={"Authorization": "Bearer mock-token"},
                        json={"name": "更新されたテナント"},
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["data"]["name"] == "更新されたテナント"

    @pytest.mark.asyncio
    async def test_update_privileged_tenant_by_admin_forbidden(self) -> None:
        """Test privileged tenant update by regular admin (should fail)."""
        with patch("app.services.auth_client.auth_client.verify_token", new_callable=AsyncMock) as mock_verify:
            with patch("app.repositories.tenant_repository.tenant_repository.get_by_id", new_callable=AsyncMock) as mock_get_by_id:
                mock_verify.return_value = MOCK_USER_ADMIN
                mock_get_by_id.return_value = MOCK_TENANT_1
                
                response = client.put(
                    "/api/tenants/tenant-001",
                    headers={"Authorization": "Bearer mock-token"},
                    json={"name": "更新しようとした名前"},
                )
                
                assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_update_privileged_tenant_by_global_admin_success(self) -> None:
        """Test privileged tenant update by global admin (should succeed)."""
        updated_tenant = Tenant(
            id="tenant-001",
            name="更新された特権テナント",
            isPrivileged=True,
            createdAt=datetime(2026, 1, 1, 0, 0, 0),
            updatedAt=datetime(2026, 1, 3, 0, 0, 0),
        )
        
        with patch("app.services.auth_client.auth_client.verify_token", new_callable=AsyncMock) as mock_verify:
            with patch("app.repositories.tenant_repository.tenant_repository.get_by_id", new_callable=AsyncMock) as mock_get_by_id:
                with patch("app.repositories.tenant_repository.tenant_repository.update", new_callable=AsyncMock) as mock_update:
                    mock_verify.return_value = MOCK_USER_GLOBAL_ADMIN
                    mock_get_by_id.return_value = MOCK_TENANT_1
                    mock_update.return_value = updated_tenant
                    
                    response = client.put(
                        "/api/tenants/tenant-001",
                        headers={"Authorization": "Bearer mock-token"},
                        json={"name": "更新された特権テナント"},
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["data"]["name"] == "更新された特権テナント"

    @pytest.mark.asyncio
    async def test_update_tenant_by_viewer_forbidden(self) -> None:
        """Test tenant update by viewer (should fail)."""
        with patch("app.services.auth_client.auth_client.verify_token", new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = MOCK_USER_VIEWER
            
            response = client.put(
                "/api/tenants/tenant-002",
                headers={"Authorization": "Bearer mock-token"},
                json={"name": "更新しようとした名前"},
            )
            
            assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_update_tenant_not_found(self) -> None:
        """Test tenant update with non-existent ID."""
        with patch("app.services.auth_client.auth_client.verify_token", new_callable=AsyncMock) as mock_verify:
            with patch("app.repositories.tenant_repository.tenant_repository.get_by_id", new_callable=AsyncMock) as mock_get_by_id:
                mock_verify.return_value = MOCK_USER_ADMIN
                mock_get_by_id.return_value = None
                
                response = client.put(
                    "/api/tenants/non-existent",
                    headers={"Authorization": "Bearer mock-token"},
                    json={"name": "更新しようとした名前"},
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_tenant_unauthorized(self) -> None:
        """Test tenant update without authentication."""
        response = client.put(
            "/api/tenants/tenant-001",
            json={"name": "更新しようとした名前"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_update_tenant_empty_request(self) -> None:
        """Test tenant update with no changes."""
        with patch("app.services.auth_client.auth_client.verify_token", new_callable=AsyncMock) as mock_verify:
            with patch("app.repositories.tenant_repository.tenant_repository.get_by_id", new_callable=AsyncMock) as mock_get_by_id:
                mock_verify.return_value = MOCK_USER_ADMIN
                mock_get_by_id.return_value = MOCK_TENANT_2
                
                response = client.put(
                    "/api/tenants/tenant-002",
                    headers={"Authorization": "Bearer mock-token"},
                    json={},
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["data"]["name"] == MOCK_TENANT_2.name
