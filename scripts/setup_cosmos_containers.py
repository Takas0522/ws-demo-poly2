"""
Cosmos DB container setup script.

This script creates the necessary containers for the User Management Service.
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from azure.cosmos import CosmosClient, PartitionKey  # noqa: E402
from azure.cosmos.exceptions import CosmosResourceExistsError  # noqa: E402

from app.core.config import settings  # noqa: E402


def create_containers() -> None:
    """Create Cosmos DB containers with proper partition keys."""
    print("Connecting to Cosmos DB...")
    client = CosmosClient(
        url=settings.cosmosdb_endpoint,
        credential=settings.cosmosdb_key,
    )
    
    try:
        # Get or create database
        print(f"Using database: {settings.cosmosdb_database}")
        database = client.get_database_client(settings.cosmosdb_database)
        
        # Create tenants container with partition key /id
        print(f"Creating container: {settings.cosmosdb_container_tenants}")
        try:
            database.create_container(
                id=settings.cosmosdb_container_tenants,
                partition_key=PartitionKey(path="/id"),
                offer_throughput=400,
            )
            print(f"✓ Created container: {settings.cosmosdb_container_tenants}")
        except CosmosResourceExistsError:
            print(f"⚠ Container already exists: {settings.cosmosdb_container_tenants}")
        
        # Create tenant-users container with partition key /tenantId
        print(f"Creating container: {settings.cosmosdb_container_tenant_users}")
        try:
            database.create_container(
                id=settings.cosmosdb_container_tenant_users,
                partition_key=PartitionKey(path="/tenantId"),
                offer_throughput=400,
            )
            print(f"✓ Created container: {settings.cosmosdb_container_tenant_users}")
        except CosmosResourceExistsError:
            print(f"⚠ Container already exists: {settings.cosmosdb_container_tenant_users}")
        
        print("\n✅ Container setup completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error setting up containers: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    create_containers()
