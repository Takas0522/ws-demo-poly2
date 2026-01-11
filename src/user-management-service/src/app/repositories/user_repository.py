"""User Management Service - User Repository"""
from typing import Optional, List
from datetime import datetime
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from app.utils import cosmos_client
from app.schemas import UserResponse, UserSearchCriteria, PaginationParams
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    """User repository for CosmosDB operations"""
    
    def __init__(self):
        self.container = None
    
    def _get_container(self):
        """Get the users container"""
        if not self.container:
            self.container = cosmos_client.users_container
        return self.container
    
    async def create(self, user_data: dict) -> dict:
        """Create a new user"""
        container = self._get_container()
        try:
            created_item = container.create_item(body=user_data)
            logger.info(f"User created: {created_item['id']}")
            return created_item
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    async def get_by_id(self, user_id: str, tenant_id: str) -> Optional[dict]:
        """Get user by ID and tenant ID"""
        container = self._get_container()
        try:
            item = container.read_item(item=user_id, partition_key=tenant_id)
            return item
        except CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error retrieving user: {str(e)}")
            raise
    
    async def update(self, user_id: str, tenant_id: str, user_data: dict) -> Optional[dict]:
        """Update user"""
        container = self._get_container()
        try:
            # Get existing item first
            existing_item = await self.get_by_id(user_id, tenant_id)
            if not existing_item:
                return None
            
            # Merge updates
            existing_item.update(user_data)
            existing_item['updatedAt'] = datetime.utcnow().isoformat()
            
            updated_item = container.replace_item(
                item=user_id,
                body=existing_item
            )
            logger.info(f"User updated: {user_id}")
            return updated_item
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            raise
    
    async def delete(self, user_id: str, tenant_id: str) -> bool:
        """Delete user (soft delete by updating status)"""
        container = self._get_container()
        try:
            existing_item = await self.get_by_id(user_id, tenant_id)
            if not existing_item:
                return False
            
            existing_item['status'] = 'DELETED'
            existing_item['updatedAt'] = datetime.utcnow().isoformat()
            
            container.replace_item(item=user_id, body=existing_item)
            logger.info(f"User deleted: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            raise
    
    async def search(
        self,
        criteria: UserSearchCriteria,
        pagination: PaginationParams
    ) -> tuple[List[dict], int]:
        """Search users with pagination"""
        container = self._get_container()
        
        # Build query
        query_parts = ["SELECT * FROM c WHERE c.tenantId = @tenantId"]
        parameters = [{"name": "@tenantId", "value": criteria.tenant_id}]
        
        if criteria.email:
            query_parts.append("AND c.email = @email")
            parameters.append({"name": "@email", "value": criteria.email})
        
        if criteria.username:
            query_parts.append("AND c.username = @username")
            parameters.append({"name": "@username", "value": criteria.username})
        
        if criteria.status:
            query_parts.append("AND c.status = @status")
            parameters.append({"name": "@status", "value": criteria.status})
        
        if criteria.search_term:
            query_parts.append(
                "AND (CONTAINS(c.email, @searchTerm) OR "
                "CONTAINS(c.username, @searchTerm) OR "
                "CONTAINS(c.firstName, @searchTerm) OR "
                "CONTAINS(c.lastName, @searchTerm))"
            )
            parameters.append({"name": "@searchTerm", "value": criteria.search_term})
        
        # Add ordering
        sort_order = "DESC" if pagination.sort_order == "desc" else "ASC"
        query_parts.append(f"ORDER BY c.{pagination.sort_by} {sort_order}")
        
        query = " ".join(query_parts)
        
        try:
            # Execute query
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            total_count = len(items)
            
            # Apply pagination
            start_idx = (pagination.page_number - 1) * pagination.page_size
            end_idx = start_idx + pagination.page_size
            paginated_items = items[start_idx:end_idx]
            
            return paginated_items, total_count
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            raise
    
    async def get_by_email(self, email: str, tenant_id: str) -> Optional[dict]:
        """Get user by email and tenant ID"""
        container = self._get_container()
        query = "SELECT * FROM c WHERE c.email = @email AND c.tenantId = @tenantId"
        parameters = [
            {"name": "@email", "value": email},
            {"name": "@tenantId", "value": tenant_id}
        ]
        
        try:
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return items[0] if items else None
        except Exception as e:
            logger.error(f"Error retrieving user by email: {str(e)}")
            raise


user_repository = UserRepository()
