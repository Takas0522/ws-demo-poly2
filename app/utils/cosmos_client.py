"""User Management Service - CosmosDB Client"""
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from app.config import settings
import logging
import urllib3

# SSL警告を無効化（開発環境のCosmosDBエミュレーター用）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class CosmosDBClient:
    """CosmosDB client wrapper"""
    
    def __init__(self):
        self.client = None
        self.database = None
        self.users_container = None
        self.audit_container = None
    
    def initialize(self):
        """Initialize database and containers"""
        try:
            # Create client (SSL検証を無効化 - 開発環境のエミュレーター用)
            self.client = CosmosClient(
                settings.cosmos_endpoint,
                settings.cosmos_key,
                connection_verify=False
            )
            
            # Get existing database
            self.database = self.client.get_database_client(settings.cosmos_database_name)
            logger.info(f"Database '{settings.cosmos_database_name}' connected")
            
            # Get existing users container
            self.users_container = self.database.get_container_client(settings.cosmos_container_name)
            logger.info(f"Container '{settings.cosmos_container_name}' connected")
            
            # Get existing audit logs container
            self.audit_container = self.database.get_container_client(settings.cosmos_audit_container_name)
            logger.info(f"Container '{settings.cosmos_audit_container_name}' connected")
            
        except Exception as e:
            logger.error(f"Error initializing CosmosDB: {str(e)}")
            raise
    
    def close(self):
        """Close the client connection"""
        if self.client:
            self.client.close()
            logger.info("CosmosDB client closed")


# Global instance (will be initialized on startup)
cosmos_client = CosmosDBClient()
