"""User Management Service - Redis Client"""
import redis
from typing import Optional
from app.config import settings
import logging
import json

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper for caching"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._enabled = False
    
    def initialize(self):
        """Initialize Redis connection"""
        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self.client.ping()
            self._enabled = True
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Caching will be disabled.")
            self.client = None
            self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if Redis is enabled and available"""
        return self._enabled and self.client is not None
    
    def get(self, key: str) -> Optional[str]:
        """Get value from Redis cache"""
        if not self.is_enabled():
            return None
        
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Error getting key from Redis: {str(e)}")
            return None
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache with optional TTL (seconds)"""
        if not self.is_enabled():
            return False
        
        try:
            if ttl:
                self.client.setex(key, ttl, value)
            else:
                self.client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Error setting key in Redis: {str(e)}")
            return False
    
    def delete(self, *keys: str) -> bool:
        """Delete one or more keys from Redis cache"""
        if not self.is_enabled():
            return False
        
        try:
            self.client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Error deleting keys from Redis: {str(e)}")
            return False
    
    def close(self):
        """Close Redis connection"""
        if self.client:
            try:
                self.client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {str(e)}")
    
    def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from Redis cache"""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from Redis: {str(e)}")
                return None
        return None
    
    def set_json(self, key: str, value: dict, ttl: Optional[int] = None) -> bool:
        """Set JSON value in Redis cache"""
        try:
            json_str = json.dumps(value)
            return self.set(key, json_str, ttl)
        except (TypeError, ValueError) as e:
            logger.error(f"Error encoding JSON for Redis: {str(e)}")
            return False


# Global instance
redis_client = RedisClient()
