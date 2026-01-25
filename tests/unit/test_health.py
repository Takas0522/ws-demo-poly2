"""
Unit tests for health check endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_health_check_healthy() -> None:
    """Test health check endpoint when all dependencies are healthy."""
    with patch("app.api.health.db_client.health_check", new_callable=AsyncMock) as mock_db_health:
        with patch("app.api.health.auth_client.health_check", new_callable=AsyncMock) as mock_auth_health:
            mock_db_health.return_value = True
            mock_auth_health.return_value = True
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "user-management-service"
            assert data["dependencies"]["database"] == "healthy"
            assert data["dependencies"]["auth_service"] == "healthy"


@pytest.mark.asyncio
async def test_health_check_db_unhealthy() -> None:
    """Test health check endpoint when database is unhealthy."""
    with patch("app.api.health.db_client.health_check", new_callable=AsyncMock) as mock_db_health:
        with patch("app.api.health.auth_client.health_check", new_callable=AsyncMock) as mock_auth_health:
            mock_db_health.return_value = False
            mock_auth_health.return_value = True
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["dependencies"]["database"] == "unhealthy"


@pytest.mark.asyncio
async def test_health_check_auth_unavailable() -> None:
    """Test health check endpoint when auth service is unavailable."""
    with patch("app.api.health.db_client.health_check", new_callable=AsyncMock) as mock_db_health:
        with patch("app.api.health.auth_client.health_check", new_callable=AsyncMock) as mock_auth_health:
            mock_db_health.return_value = True
            mock_auth_health.return_value = False
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["dependencies"]["auth_service"] == "unavailable"


def test_root_endpoint() -> None:
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert data["status"] == "running"
