"""
Redis connection pool management with singleton pattern.
Provides secure, high-performance Redis connections with atomic operations.
"""
import asyncio
import logging
from typing import Any, Dict, Optional

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from core.config import get_settings

logger = logging.getLogger(__name__)


class RedisConnectionManager:
    """Singleton Redis connection pool manager."""

    _instance: Optional['RedisConnectionManager'] = None
    _pool: Optional[ConnectionPool] = None
    _redis: Optional[redis.Redis] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> 'RedisConnectionManager':
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self) -> None:
        """Initialize Redis connection pool."""
        if self._pool is not None:
            return

        async with self._lock:
            if self._pool is not None:
                return

            settings = get_settings()

            try:
                # Create connection pool with security and performance settings
                self._pool = ConnectionPool.from_url(
                    settings.redis_url,
                    max_connections=settings.redis_max_connections,
                    socket_timeout=settings.redis_socket_timeout,
                    socket_connect_timeout=settings.redis_socket_connect_timeout,
                    retry_on_timeout=True,
                    health_check_interval=30,
                    decode_responses=True,
                    encoding='utf-8'
                )

                # Create Redis client
                self._redis = redis.Redis(
                    connection_pool=self._pool,
                    decode_responses=True,
                    socket_keepalive=True,
                    socket_keepalive_options={}
                )

                # Test connection
                await self._redis.ping()
                logger.info(
                    f"Redis connection pool initialized with max "
                    f"{settings.redis_max_connections} connections"
                )

            except Exception as e:
                logger.error(f"Failed to initialize Redis connection pool: {e}")
                await self.close()
                raise

    async def get_redis(self) -> redis.Redis:
        """Get Redis client instance."""
        if self._redis is None:
            await self.initialize()
        return self._redis

    async def close(self) -> None:
        """Close Redis connections and cleanup."""
        async with self._lock:
            if self._redis:
                await self._redis.close()
                self._redis = None

            if self._pool:
                await self._pool.disconnect()
                self._pool = None

            logger.info("Redis connection pool closed")

    async def health_check(self) -> Dict[str, Any]:
        """Perform Redis health check."""
        try:
            if self._redis is None:
                return {"status": "error", "message": "Redis not initialized"}

            # Test basic operations
            start_time = asyncio.get_event_loop().time()
            await self._redis.ping()
            end_time = asyncio.get_event_loop().time()

            ping_time = (end_time - start_time) * 1000  # Convert to milliseconds

            # Get connection pool info
            pool_info = {
                "available_connections": (
                    self._pool.available_connections if self._pool else 0
                ),
                "max_connections": self._pool.max_connections if self._pool else 0,
                "created_connections": (
                    self._pool.created_connections if self._pool else 0
                ),
            }

            return {
                "status": "healthy",
                "ping_time_ms": round(ping_time, 2),
                "pool_info": pool_info
            }

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


# Global instance
redis_manager = RedisConnectionManager()


async def get_redis() -> redis.Redis:
    """Get Redis client instance (convenience function)."""
    return await redis_manager.get_redis()


async def close_redis():
    """Close Redis connections (convenience function)."""
    await redis_manager.close()
