import pickle
import logging
from typing import Any, Optional

import redis.asyncio as redis
from src.core.config import settings

class CacheClient:
    """
    An asynchronous Redis cache client that handles connection pooling and data serialization.
    """
    def __init__(self, redis_url: str):
        """
        Initializes the client and creates a connection pool to Redis.
        """
        try:
            # Create a connection pool. This is more efficient than creating
            # a new connection for every request.
            self.redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=False)
            logging.info("Redis client initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Redis client: {e}")
            self.redis = None

    async def ping(self) -> bool:
        """Checks if the connection to the Redis server is alive."""
        if not self.redis:
            return False
        try:
            return await self.redis.ping()
        except Exception as e:
            logging.error(f"Redis ping failed: {e}")
            return False

    async def set(self, key: str, value: Any, expiry_time: Optional[int] = 300) -> bool:
        """
        Sets a key-value pair in the cache with an optional expiry time.

        Args:
            key (str): The key to set.
            value (Any): The value to store. It will be serialized using pickle.
            expiry_time (int, optional): Expiry time in seconds. Defaults to 300 (5 minutes).
        """
        if not self.redis:
            return False
        try:
            # Serialize the Python object to bytes using pickle before storing
            serialized_value = pickle.dumps(value)
            await self.redis.set(key, serialized_value, ex=expiry_time)
            return True
        except Exception as e:
            logging.error(f"Redis SET failed for key '{key}': {e}")
            return False

    async def get(self, key: str) -> Any:
        """
        Gets a value from the cache by key.
        """
        if not self.redis:
            return None
        try:
            # Retrieve the value as bytes
            cached_value = await self.redis.get(key)
            if cached_value:
                # Deserialize the bytes back into a Python object
                return pickle.loads(cached_value)
            return None
        except Exception as e:
            logging.error(f"Redis GET failed for key '{key}': {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Deletes a key from the cache."""
        if not self.redis:
            return False
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logging.error(f"Redis DELETE failed for key '{key}': {e}")
            return False

    async def close(self):
        """Closes the Redis connection pool."""
        if self.redis:
            await self.redis.close()

# Create a single, shared instance of the CacheClient for the entire application.
# This is the 'singleton' pattern.
cache = CacheClient(redis_url=settings.REDIS_URL)