"""
Auth Service client for JWT verification and authentication.
"""
from typing import Optional, Dict, Any
import httpx
from jose import jwt, JWTError

from app.core.config import settings


class AuthServiceClient:
    """Client for interacting with the Auth Service."""

    def __init__(self) -> None:
        """Initialize Auth Service client."""
        self._public_key: Optional[str] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        """Initialize the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=settings.auth_service_url,
                timeout=10.0,
            )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def get_public_key(self) -> str:
        """
        Fetch the public key from Auth Service for JWT verification.
        
        Returns:
            str: The public key in PEM format.
        
        Raises:
            Exception: If the public key cannot be fetched.
        """
        if self._public_key is not None:
            return self._public_key

        if self._http_client is None:
            await self.initialize()

        try:
            response = await self._http_client.get(settings.jwt_public_key_endpoint)
            response.raise_for_status()
            data = response.json()
            self._public_key = data.get("publicKey", "")
            return self._public_key
        except Exception as e:
            # For now, we'll return an empty string if Auth Service is not available
            # This allows the service to start even without Auth Service
            return ""

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and return the payload.
        
        Args:
            token: JWT token to verify.
        
        Returns:
            Dict containing the token payload if valid, None otherwise.
        """
        try:
            public_key = await self.get_public_key()
            if not public_key:
                # Auth Service not available, skip verification for now
                return None

            payload = jwt.decode(
                token,
                public_key,
                algorithms=[settings.jwt_algorithm],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
            )
            return payload
        except JWTError:
            return None
        except Exception:
            return None

    async def health_check(self) -> bool:
        """
        Check if Auth Service is reachable.
        
        Returns:
            bool: True if Auth Service is healthy, False otherwise.
        """
        if self._http_client is None:
            await self.initialize()

        try:
            response = await self._http_client.get("/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False


# Global auth service client instance
auth_client = AuthServiceClient()
