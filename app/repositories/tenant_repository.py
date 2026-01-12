"""Tenant Management Service - Tenant Repository"""
from typing import Optional, List, Tuple
from datetime import datetime
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from app.utils import cosmos_client
import logging

logger = logging.getLogger(__name__)


class TenantRepository:
    """Tenant repository for CosmosDB operations"""
    
    def __init__(self):
        self.container = None
    
    def _get_container(self):
        """Get the tenants container"""
        if not self.container:
            self.container = cosmos_client.tenants_container
        return self.container
    
    async def create(self, tenant_data: dict) -> dict:
        """Create a new tenant"""
        container = self._get_container()
        try:
            created_item = container.create_item(body=tenant_data)
            logger.info(f"Tenant created: {created_item['id']}")
            return created_item
        except Exception as e:
            logger.error(f"Error creating tenant: {str(e)}")
            raise
    
    async def get_by_id(self, tenant_id: str) -> Optional[dict]:
        """Get tenant by ID"""
        container = self._get_container()
        try:
            item = container.read_item(item=tenant_id, partition_key=tenant_id)
            return item
        except CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error retrieving tenant: {str(e)}")
            raise
    
    async def update(self, tenant_id: str, tenant_data: dict) -> Optional[dict]:
        """Update tenant"""
        container = self._get_container()
        try:
            # Get existing tenant first
            existing_tenant = await self.get_by_id(tenant_id)
            if not existing_tenant:
                return None
            
            # Merge updates
            existing_tenant.update(tenant_data)
            existing_tenant['updatedAt'] = datetime.utcnow().isoformat()
            
            # Upsert the item
            updated_item = container.upsert_item(body=existing_tenant)
            logger.info(f"Tenant updated: {tenant_id}")
            return updated_item
        except Exception as e:
            logger.error(f"Error updating tenant: {str(e)}")
            raise
    
    async def delete(self, tenant_id: str) -> bool:
        """Soft delete tenant"""
        container = self._get_container()
        try:
            tenant = await self.get_by_id(tenant_id)
            if not tenant:
                return False
            
            # Soft delete by setting status
            tenant['status'] = 'deleted'
            tenant['deletedAt'] = datetime.utcnow().isoformat()
            tenant['updatedAt'] = datetime.utcnow().isoformat()
            
            container.upsert_item(body=tenant)
            logger.info(f"Tenant soft deleted: {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting tenant: {str(e)}")
            raise
    
    async def list_tenants(
        self,
        status: Optional[str] = None,
        plan: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[dict], int]:
        """
        List tenants with filtering and pagination.
        
        Returns:
            Tuple of (items, total_count)
        """
        container = self._get_container()
        try:
            # Build query
            query = "SELECT * FROM c WHERE c.status != 'deleted'"
            parameters = []
            
            if status:
                query += " AND c.status = @status"
                parameters.append({'name': '@status', 'value': status})
            
            if plan:
                query += " AND c.subscription.plan = @plan"
                parameters.append({'name': '@plan', 'value': plan})
            
            query += " ORDER BY c.createdAt DESC"
            
            # Get total count
            count_query = query.replace("SELECT *", "SELECT VALUE COUNT(1)")
            count_items = list(container.query_items(
                query=count_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            total_count = count_items[0] if count_items else 0
            
            # Get paginated items
            query += f" OFFSET {skip} LIMIT {limit}"
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items, total_count
        except Exception as e:
            logger.error(f"Error listing tenants: {str(e)}")
            raise


class TenantUserRepository:
    """Tenant User repository for CosmosDB operations"""
    
    def __init__(self):
        self.container = None
    
    def _get_container(self):
        """Get the tenant users container"""
        if not self.container:
            self.container = cosmos_client.tenant_users_container
        return self.container
    
    async def create(self, tenant_user_data: dict) -> dict:
        """Create a new tenant user relationship"""
        container = self._get_container()
        try:
            created_item = container.create_item(body=tenant_user_data)
            logger.info(f"Tenant user created: {created_item['id']}")
            return created_item
        except Exception as e:
            logger.error(f"Error creating tenant user: {str(e)}")
            raise
    
    async def get_by_user_and_tenant(
        self,
        user_id: str,
        tenant_id: str
    ) -> Optional[dict]:
        """Get tenant user relationship"""
        container = self._get_container()
        try:
            query = """
                SELECT * FROM c 
                WHERE c.userId = @userId 
                AND c.tenantId = @tenantId
            """
            parameters = [
                {'name': '@userId', 'value': user_id},
                {'name': '@tenantId', 'value': tenant_id}
            ]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error retrieving tenant user: {str(e)}")
            raise


# Global instances
tenant_repository = TenantRepository()
tenant_user_repository = TenantUserRepository()
