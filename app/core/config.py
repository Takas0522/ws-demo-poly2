"""
Core configuration module for the User Management Service.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application Settings
    app_name: str = "User Management Service"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8002

    # Cosmos DB Settings
    cosmosdb_endpoint: str = "https://localhost:8081"
    cosmosdb_key: str = "mock-key-for-testing"
    cosmosdb_database: str = "management-app"
    cosmosdb_container_tenants: str = "tenants"
    cosmosdb_container_tenant_users: str = "tenant-users"

    # Auth Service Integration
    auth_service_url: str = "http://localhost:8001"
    auth_service_verify_endpoint: str = "/api/auth/verify"
    jwt_public_key_endpoint: str = "/api/auth/public-key"
    jwt_algorithm: str = "RS256"
    jwt_audience: str = "management-app"
    jwt_issuer: str = "auth-service"

    # CORS Settings
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
