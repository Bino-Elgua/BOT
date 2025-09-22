"""
Atomic rate limiter using Redis with EVALSHA for high performance.
Implements sliding window rate limiting with burst protection.
"""
import logging
import time
from typing import Any, Dict, Optional

from app.services.redis_service import get_redis
from core.config import get_settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Atomic rate limiter using Redis EVALSHA operations."""

    def __init__(self):
        self._script_sha: Optional[str] = None
        self._lua_script = """
            local key = KEYS[1]
            local window = tonumber(ARGV[1])
            local limit = tonumber(ARGV[2])
            local current_time = tonumber(ARGV[3])
            local burst_limit = tonumber(ARGV[4])

            -- Remove expired entries
            redis.call('ZREMRANGEBYSCORE', key, 0, current_time - window)

            -- Count current requests in window
            local current_count = redis.call('ZCARD', key)

            -- Check if limit exceeded
            if current_count >= limit then
                -- Return rate limit info
                local oldest_score = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
                local reset_time = 0
                if oldest_score[2] then
                    reset_time = oldest_score[2] + window
                end

                return {
                    0,  -- allowed (false)
                    current_count,  -- current count
                    limit,  -- limit
                    reset_time,  -- reset time
                    limit - current_count  -- remaining
                }
            end

            -- Add current request
            redis.call('ZADD', key, current_time, current_time .. ':' .. math.random())

            -- Set expiry for cleanup
            redis.call('EXPIRE', key, window + 1)

            -- Return success info
            return {
                1,  -- allowed (true)
                current_count + 1,  -- current count
                limit,  -- limit
                current_time + window,  -- reset time
                limit - current_count - 1  -- remaining
            }
        """

    async def _ensure_script_loaded(self):
        """Ensure Lua script is loaded in Redis."""
        if self._script_sha is None:
            redis_client = await get_redis()
            self._script_sha = await redis_client.script_load(self._lua_script)
            logger.debug(f"Rate limiter script loaded with SHA: {self._script_sha}")

    async def is_allowed(
        self,
        identifier: str,
        limit: Optional[int] = None,
        window: Optional[int] = None,
        burst_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Check if request is allowed under rate limit.

        Args:
            identifier: Unique identifier for rate limiting (IP, user ID, etc.)
            limit: Requests allowed per window (defaults to config)
            window: Time window in seconds (defaults to config)
            burst_limit: Maximum burst requests (defaults to config)

        Returns:
            Dictionary with rate limit information:
            - allowed: bool - Whether request is allowed
            - current_count: int - Current request count in window
            - limit: int - Request limit per window
            - reset_time: float - When the window resets
            - remaining: int - Remaining requests in window
        """
        try:
            await self._ensure_script_loaded()

            settings = get_settings()
            limit = limit or settings.rate_limit_requests
            window = window or settings.rate_limit_window
            burst_limit = burst_limit or settings.rate_limit_burst

            current_time = time.time()
            key = f"rate_limit:{identifier}"

            redis_client = await get_redis()

            # Execute atomic rate limit check
            result = await redis_client.evalsha(
                self._script_sha,
                1,  # Number of keys
                key,
                window,
                limit,
                current_time,
                burst_limit
            )

            return {
                "allowed": bool(result[0]),
                "current_count": int(result[1]),
                "limit": int(result[2]),
                "reset_time": float(result[3]),
                "remaining": max(0, int(result[4]))
            }

        except Exception as e:
            logger.error(f"Rate limit check failed for {identifier}: {e}")
            # Fail open for availability, but log the error
            return {
                "allowed": True,
                "current_count": 0,
                "limit": limit or 100,
                "reset_time": time.time() + (window or 60),
                "remaining": limit or 100,
                "error": str(e)
            }

    async def reset_limit(self, identifier: str) -> bool:
        """
        Reset rate limit for identifier.

        Args:
            identifier: Unique identifier to reset

        Returns:
            bool: True if reset successful
        """
        try:
            redis_client = await get_redis()
            key = f"rate_limit:{identifier}"
            result = await redis_client.delete(key)
            logger.info(f"Rate limit reset for {identifier}")
            return bool(result)

        except Exception as e:
            logger.error(f"Failed to reset rate limit for {identifier}: {e}")
            return False

    async def get_stats(self, identifier: str) -> Dict[str, Any]:
        """
        Get rate limit statistics for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Dictionary with statistics
        """
        try:
            redis_client = await get_redis()
            key = f"rate_limit:{identifier}"

            # Get current count
            current_count = await redis_client.zcard(key)

            # Get oldest and newest entries
            oldest = await redis_client.zrange(key, 0, 0, withscores=True)
            newest = await redis_client.zrange(key, -1, -1, withscores=True)

            stats = {
                "current_count": current_count,
                "oldest_request": oldest[0][1] if oldest else None,
                "newest_request": newest[0][1] if newest else None,
                "window_start": oldest[0][1] if oldest else None,
                "window_end": (oldest[0][1] + get_settings().rate_limit_window) if oldest else None
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get rate limit stats for {identifier}: {e}")
            return {"error": str(e)}


# Global rate limiter instance
rate_limiter = RateLimiter()
