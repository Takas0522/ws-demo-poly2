"""User Management Service - CosmosDB Client"""
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class CosmosDBClient:
    """CosmosDB client wrapper"""
    
    def __init__(self):
        self.client = CosmosClient(settings.cosmos_endpoint, settings.cosmos_key)
        self.database = None
        self.users_container = None
        self.audit_container = None
    
    def initialize(self):
        """Initialize database and containers"""
        try:
            # Create or get database
            self.database = self.client.create_database_if_not_exists(
                id=settings.cosmos_database_name
            )
            logger.info(f"Database '{settings.cosmos_database_name}' initialized")
            
            # Create or get users container
            self.users_container = self.database.create_container_if_not_exists(
                id=settings.cosmos_container_name,
                partition_key=PartitionKey(path="/tenantId"),
                offer_throughput=400
            )
            logger.info(f"Container '{settings.cosmos_container_name}' initialized")
            
            # Create or get audit logs container
            self.audit_container = self.database.create_container_if_not_exists(
                id=settings.cosmos_audit_container_name,
                partition_key=PartitionKey(path="/tenantId"),
                offer_throughput=400
            )
            logger.info(f"Container '{settings.cosmos_audit_container_name}' initialized")
            
        except Exception as e:
            logger.error(f"Error initializing CosmosDB: {str(e)}")
            raise
    
    def close(self):
        """Close the client connection"""
        if self.client:
            self.client.close()
            logger.info("CosmosDB client closed")


# Global instance
cosmos_client = CosmosDBClient()
