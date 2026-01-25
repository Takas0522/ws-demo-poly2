"""
Tenant repository for database operations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.db import db_client
from app.models.tenant import Tenant


# Allowed fields for sorting to prevent SQL injection
ALLOWED_SORT_FIELDS = {"id", "name", "isPrivileged", "createdAt", "updatedAt"}


class TenantRepository:
    """Repository for tenant database operations."""

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
    ) -> tuple[List[Tenant], int]:
        """
        Get all tenants with pagination and sorting.
        
        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.
            sort_by: Field to sort by (must be in ALLOWED_SORT_FIELDS).
            sort_order: Sort order (asc/desc).
        
        Returns:
            Tuple of (list of tenants, total count).
        """
        # Validate sort_by to prevent SQL injection
        if sort_by not in ALLOWED_SORT_FIELDS:
            sort_by = "createdAt"  # Default to safe value
        
        # Build query with validated parameter
        order = "DESC" if sort_order.lower() == "desc" else "ASC"
        query = f"SELECT * FROM c ORDER BY c.{sort_by} {order}"
        
        # Get all items (Cosmos DB SDK doesn't support OFFSET/LIMIT in query)
        items = list(db_client.tenants_container.query_items(
            query=query,
            enable_cross_partition_query=True,
        ))
        
        total_count = len(items)
        
        # Apply pagination manually
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = items[start_idx:end_idx]
        
        # Convert to Tenant models
        tenants = [Tenant(**item) for item in paginated_items]
        
        return tenants, total_count

    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """
        Get tenant by ID.
        
        Args:
            tenant_id: Tenant ID.
        
        Returns:
            Tenant if found, None otherwise.
        """
        try:
            item = db_client.tenants_container.read_item(
                item=tenant_id,
                partition_key=tenant_id,
            )
            return Tenant(**item)
        except CosmosResourceNotFoundError:
            return None

    async def create(self, tenant: Tenant) -> Tenant:
        """
        Create a new tenant.
        
        Args:
            tenant: Tenant to create.
        
        Returns:
            Created tenant.
        """
        tenant_dict = tenant.model_dump(mode="json")
        created_item = db_client.tenants_container.create_item(body=tenant_dict)
        return Tenant(**created_item)

    async def update(self, tenant_id: str, updates: Dict[str, Any]) -> Optional[Tenant]:
        """
        Update tenant by ID.
        
        Args:
            tenant_id: Tenant ID.
            updates: Dictionary of fields to update.
        
        Returns:
            Updated tenant if found, None otherwise.
        """
        try:
            # Get existing tenant
            existing = db_client.tenants_container.read_item(
                item=tenant_id,
                partition_key=tenant_id,
            )
            
            # Update fields
            for key, value in updates.items():
                if key not in ["id", "createdAt"]:  # Don't allow updating these fields
                    existing[key] = value
            
            # Update timestamp
            existing["updatedAt"] = datetime.now(timezone.utc).isoformat() + "Z"
            
            # Save
            updated_item = db_client.tenants_container.replace_item(
                item=tenant_id,
                body=existing,
            )
            return Tenant(**updated_item)
        except CosmosResourceNotFoundError:
            return None

    async def delete(self, tenant_id: str) -> bool:
        """
        Delete tenant by ID.
        
        Args:
            tenant_id: Tenant ID.
        
        Returns:
            True if deleted, False if not found.
        """
        try:
            db_client.tenants_container.delete_item(
                item=tenant_id,
                partition_key=tenant_id,
            )
            return True
        except CosmosResourceNotFoundError:
            return False

    async def get_user_count(self, tenant_id: str) -> int:
        """
        Get count of users in a tenant.
        
        Args:
            tenant_id: Tenant ID.
        
        Returns:
            Number of users in the tenant.
        """
        query = "SELECT VALUE COUNT(1) FROM c WHERE c.tenantId = @tenantId"
        parameters = [{"name": "@tenantId", "value": tenant_id}]
        
        items = list(db_client.tenant_users_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False,
            partition_key=tenant_id,
        ))
        
        return items[0] if items else 0


# Global repository instance
tenant_repository = TenantRepository()
