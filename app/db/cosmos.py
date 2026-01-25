"""
Cosmos DB client module for database operations.
"""
from typing import Optional
from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.core.config import settings


class CosmosDBClient:
    """Cosmos DB client wrapper for managing database connections."""

    def __init__(self) -> None:
        """Initialize Cosmos DB client."""
        self._client: Optional[CosmosClient] = None
        self._database: Optional[DatabaseProxy] = None
        self._tenants_container: Optional[ContainerProxy] = None
        self._tenant_users_container: Optional[ContainerProxy] = None

    def connect(self) -> None:
        """Connect to Cosmos DB and initialize containers."""
        if self._client is None:
            self._client = CosmosClient(
                url=settings.cosmosdb_endpoint,
                credential=settings.cosmosdb_key,
            )
            self._database = self._client.get_database_client(settings.cosmosdb_database)

            # Initialize container references
            self._tenants_container = self._database.get_container_client(
                settings.cosmosdb_container_tenants
            )
            self._tenant_users_container = self._database.get_container_client(
                settings.cosmosdb_container_tenant_users
            )

    def disconnect(self) -> None:
        """Disconnect from Cosmos DB."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            self._tenants_container = None
            self._tenant_users_container = None

    @property
    def tenants_container(self) -> ContainerProxy:
        """Get tenants container."""
        if self._tenants_container is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._tenants_container

    @property
    def tenant_users_container(self) -> ContainerProxy:
        """Get tenant users container."""
        if self._tenant_users_container is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._tenant_users_container

    async def health_check(self) -> bool:
        """
        Check if the database connection is healthy.
        
        Returns:
            bool: True if connection is healthy, False otherwise.
        """
        try:
            if self._database is None:
                return False
            # Try to read database properties
            self._database.read()
            return True
        except Exception:
            return False


# Global database client instance
db_client = CosmosDBClient()
