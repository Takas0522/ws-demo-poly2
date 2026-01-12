"""Test Redis Client"""
import pytest
from unittest.mock import MagicMock, patch
import json

from app.utils.redis_client import RedisClient


@pytest.fixture
def redis_client():
    """Create Redis client instance"""
    client = RedisClient()
    client.client = MagicMock()
    client._enabled = True
    return client


def test_redis_is_enabled(redis_client):
    """Test Redis enabled check"""
    assert redis_client.is_enabled() is True
    
    redis_client._enabled = False
    assert redis_client.is_enabled() is False


def test_redis_get_success(redis_client):
    """Test successful get from Redis"""
    redis_client.client.get.return_value = "test_value"
    
    result = redis_client.get("test_key")
    
    assert result == "test_value"
    redis_client.client.get.assert_called_once_with("test_key")


def test_redis_get_disabled():
    """Test get when Redis is disabled"""
    client = RedisClient()
    client._enabled = False
    
    result = client.get("test_key")
    
    assert result is None


def test_redis_get_error(redis_client):
    """Test get with error"""
    redis_client.client.get.side_effect = Exception("Connection error")
    
    result = redis_client.get("test_key")
    
    assert result is None


def test_redis_set_success(redis_client):
    """Test successful set in Redis"""
    result = redis_client.set("test_key", "test_value")
    
    assert result is True
    redis_client.client.set.assert_called_once_with("test_key", "test_value")


def test_redis_set_with_ttl(redis_client):
    """Test set with TTL"""
    result = redis_client.set("test_key", "test_value", ttl=300)
    
    assert result is True
    redis_client.client.setex.assert_called_once_with("test_key", 300, "test_value")


def test_redis_set_disabled():
    """Test set when Redis is disabled"""
    client = RedisClient()
    client._enabled = False
    
    result = client.set("test_key", "test_value")
    
    assert result is False


def test_redis_delete_success(redis_client):
    """Test successful delete from Redis"""
    result = redis_client.delete("key1", "key2")
    
    assert result is True
    redis_client.client.delete.assert_called_once_with("key1", "key2")


def test_redis_delete_disabled():
    """Test delete when Redis is disabled"""
    client = RedisClient()
    client._enabled = False
    
    result = client.delete("test_key")
    
    assert result is False


def test_redis_get_json_success(redis_client):
    """Test successful get JSON from Redis"""
    test_data = {"key": "value", "number": 123}
    redis_client.client.get.return_value = json.dumps(test_data)
    
    result = redis_client.get_json("test_key")
    
    assert result == test_data


def test_redis_get_json_invalid():
    """Test get JSON with invalid JSON data"""
    client = RedisClient()
    client.client = MagicMock()
    client._enabled = True
    client.client.get.return_value = "invalid json"
    
    result = client.get_json("test_key")
    
    assert result is None


def test_redis_set_json_success(redis_client):
    """Test successful set JSON in Redis"""
    test_data = {"key": "value", "number": 123}
    
    result = redis_client.set_json("test_key", test_data)
    
    assert result is True
    redis_client.client.set.assert_called_once()


def test_redis_set_json_with_ttl(redis_client):
    """Test set JSON with TTL"""
    test_data = {"key": "value"}
    
    result = redis_client.set_json("test_key", test_data, ttl=300)
    
    assert result is True
    redis_client.client.setex.assert_called_once()


def test_redis_initialize_success():
    """Test successful Redis initialization"""
    with patch("app.utils.redis_client.redis.Redis") as mock_redis:
        mock_instance = MagicMock()
        mock_instance.ping.return_value = True
        mock_redis.return_value = mock_instance
        
        client = RedisClient()
        client.initialize()
        
        assert client.is_enabled() is True
        assert client.client is not None


def test_redis_initialize_failure():
    """Test Redis initialization failure"""
    with patch("app.utils.redis_client.redis.Redis") as mock_redis:
        mock_redis.side_effect = Exception("Connection failed")
        
        client = RedisClient()
        client.initialize()
        
        assert client.is_enabled() is False
        assert client.client is None


def test_redis_close(redis_client):
    """Test Redis close"""
    redis_client.close()
    
    redis_client.client.close.assert_called_once()
