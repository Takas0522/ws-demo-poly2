"""User Management Service - Audit Repository"""
from typing import List
from datetime import datetime
from app.utils import cosmos_client
from app.schemas import CreateAuditLogRequest
import logging

logger = logging.getLogger(__name__)


class AuditRepository:
    """Audit log repository for CosmosDB operations"""
    
    def __init__(self):
        self.container = None
    
    def _get_container(self):
        """Get the audit logs container"""
        if not self.container:
            self.container = cosmos_client.audit_container
        return self.container
    
    async def create(self, audit_data: dict) -> dict:
        """Create a new audit log entry"""
        container = self._get_container()
        try:
            created_item = container.create_item(body=audit_data)
            logger.info(f"Audit log created: {created_item['id']}")
            return created_item
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
            raise
    
    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        tenant_id: str
    ) -> List[dict]:
        """Get audit logs for a specific entity"""
        container = self._get_container()
        query = """
            SELECT * FROM c 
            WHERE c.entityType = @entityType 
            AND c.entityId = @entityId 
            AND c.tenantId = @tenantId
            ORDER BY c.performedAt DESC
        """
        parameters = [
            {"name": "@entityType", "value": entity_type},
            {"name": "@entityId", "value": entity_id},
            {"name": "@tenantId", "value": tenant_id}
        ]
        
        try:
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {str(e)}")
            raise


audit_repository = AuditRepository()
