"""
Services module for external service integrations.
"""
from app.services.auth_client import auth_client, AuthServiceClient

__all__ = ["auth_client", "AuthServiceClient"]
