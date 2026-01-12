"""User Management Service - Configuration"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

# プロジェクトルートディレクトリを取得
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings"""
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 3002
    environment: str = "development"

    # CosmosDB Configuration
    # NOTE: These defaults are for testing only. Override in production via environment variables.
    cosmos_endpoint: str = "https://localhost:8081"
    cosmos_key: str = "test-key"
    cosmos_database_name: str = "UserManagement"
    cosmos_container_name: str = "Users"
    cosmos_audit_container_name: str = "AuditLogs"

    # Redis Configuration (for caching)
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0

    # JWT Configuration
    # NOTE: Use a strong, randomly generated secret in production environments.
    jwt_secret: str = "test-secret"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "auth-service"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = str(ENV_FILE) if ENV_FILE.exists() else ".env"
        case_sensitive = False


settings = Settings()
