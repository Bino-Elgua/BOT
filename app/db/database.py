"""
Database connection and session management.
Provides secure PostgreSQL connections with connection pooling.
"""
import asyncio
import logging
from typing import Optional, AsyncGenerator
import asyncpg
from asyncpg import Pool
from core.config import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection pool manager."""
    
    def __init__(self):
        self._pool: Optional[Pool] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize database connection pool."""
        if self._pool is not None:
            return
        
        async with self._lock:
            if self._pool is not None:
                return
            
            settings = get_settings()
            
            try:
                self._pool = await asyncpg.create_pool(
                    settings.database_url,
                    min_size=2,
                    max_size=20,
                    command_timeout=60,
                    server_settings={
                        'application_name': settings.app_name,
                        'jit': 'off'
                    }
                )
                
                logger.info("Database connection pool initialized")
                
                # Test connection
                async with self._pool.acquire() as conn:
                    await conn.execute("SELECT 1")
                
                logger.info("Database connection verified")
                
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                await self.close()
                raise
    
    async def get_connection(self):
        """Get database connection from pool."""
        if self._pool is None:
            await self.initialize()
        return self._pool.acquire()
    
    async def close(self) -> None:
        """Close database connections."""
        async with self._lock:
            if self._pool:
                await self._pool.close()
                self._pool = None
                logger.info("Database connection pool closed")
    
    async def health_check(self) -> dict:
        """Perform database health check."""
        try:
            if self._pool is None:
                return {"status": "error", "message": "Database not initialized"}
            
            start_time = asyncio.get_event_loop().time()
            
            async with self._pool.acquire() as conn:
                await conn.execute("SELECT 1")
            
            end_time = asyncio.get_event_loop().time()
            response_time = (end_time - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "pool_size": self._pool.get_size(),
                "pool_max_size": self._pool.get_max_size(),
                "pool_min_size": self._pool.get_min_size()
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "error", "message": str(e)}


# Global database manager
db_manager = DatabaseManager()


async def get_db_connection():
    """Get database connection (dependency injection)."""
    async with db_manager.get_connection() as conn:
        yield conn


async def close_db():
    """Close database connections."""
    await db_manager.close()