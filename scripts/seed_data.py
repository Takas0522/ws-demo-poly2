"""
Seed data script for User Management Service.

This script creates initial seed data including:
- Privileged tenant
- Initial user bindings
"""
import sys
import os
from datetime import datetime, timezone
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceExistsError

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.models.tenant import Tenant
from app.models.tenant_user import TenantUser


def seed_data() -> None:
    """Create seed data for the User Management Service."""
    print("Connecting to Cosmos DB...")
    client = CosmosClient(
        url=settings.cosmosdb_endpoint,
        credential=settings.cosmosdb_key,
    )
    
    try:
        database = client.get_database_client(settings.cosmosdb_database)
        tenants_container = database.get_container_client(settings.cosmosdb_container_tenants)
        tenant_users_container = database.get_container_client(
            settings.cosmosdb_container_tenant_users
        )
        
        # Create privileged tenant
        print("\nCreating privileged tenant...")
        privileged_tenant = Tenant(
            id="tenant-001",
            name="特権管理テナント",
            isPrivileged=True,
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
        )
        
        try:
            tenants_container.create_item(body=privileged_tenant.model_dump(mode="json"))
            print(f"✓ Created privileged tenant: {privileged_tenant.id}")
        except CosmosResourceExistsError:
            print(f"⚠ Privileged tenant already exists: {privileged_tenant.id}")
        
        # Create initial user binding
        # Note: This assumes user-001 exists in the Auth Service
        print("\nCreating initial user binding...")
        tenant_user = TenantUser(
            id="tu-001",
            tenantId="tenant-001",
            userId="user-001",
            addedAt=datetime.now(timezone.utc),
        )
        
        try:
            tenant_users_container.create_item(body=tenant_user.model_dump(mode="json"))
            print(f"✓ Created tenant-user binding: {tenant_user.id}")
        except CosmosResourceExistsError:
            print(f"⚠ Tenant-user binding already exists: {tenant_user.id}")
        
        print("\n✅ Seed data creation completed successfully!")
        print("\nCreated resources:")
        print(f"  - Tenant: {privileged_tenant.id} ({privileged_tenant.name})")
        print(f"  - TenantUser: {tenant_user.id} (tenant: {tenant_user.tenantId}, user: {tenant_user.userId})")
        
    except Exception as e:
        print(f"\n❌ Error creating seed data: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    seed_data()
