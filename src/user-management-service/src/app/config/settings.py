"""User Management Service - Configuration"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"
    
    # CosmosDB Configuration
    cosmos_endpoint: str = "https://localhost:8081"
    cosmos_key: str = "test-key"
    cosmos_database_name: str = "UserManagement"
    cosmos_container_name: str = "Users"
    cosmos_audit_container_name: str = "AuditLogs"
    
    # JWT Configuration
    jwt_secret: str = "test-secret"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "auth-service"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
