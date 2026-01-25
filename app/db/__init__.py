"""
Database module for Cosmos DB operations.
"""
from app.db.cosmos import db_client, CosmosDBClient

__all__ = ["db_client", "CosmosDBClient"]
