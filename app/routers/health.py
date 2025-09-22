"""
Health check router with <100ms baseline latency requirement.
Provides comprehensive system health monitoring.
"""
import asyncio
import logging
import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from app.services.redis_service import redis_manager
from core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Primary health check endpoint with <100ms baseline latency.

    Returns:
        Dictionary with health status and metrics
    """
    start_time = time.time()

    try:
        settings = get_settings()

        # Quick health checks (optimized for speed)
        health_data = {
            "status": "healthy",
            "timestamp": start_time,
            "service": settings.app_name,
            "version": settings.app_version,
            "checks": {}
        }

        # Basic application health
        health_data["checks"]["application"] = {
            "status": "healthy",
            "details": "Application is running"
        }

        # Redis health check (with timeout)
        try:
            redis_task = asyncio.create_task(redis_manager.health_check())
            redis_health = await asyncio.wait_for(
                redis_task,
                timeout=settings.health_check_timeout * 0.5  # Reserve time for response
            )
            health_data["checks"]["redis"] = redis_health

        except asyncio.TimeoutError:
            health_data["checks"]["redis"] = {
                "status": "timeout",
                "message": "Redis health check timed out"
            }
        except Exception as e:
            health_data["checks"]["redis"] = {
                "status": "error",
                "message": str(e)
            }

        # Calculate response time
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        health_data["response_time_ms"] = round(response_time_ms, 2)

        # Check if we're meeting the <100ms requirement
        if response_time_ms > (settings.health_check_timeout * 1000):
            logger.warning(
                f"Health check exceeded baseline latency: {response_time_ms}ms > "
                f"{settings.health_check_timeout * 1000}ms"
            )
            health_data["status"] = "degraded"
            health_data["warning"] = "Response time exceeded baseline latency"

        # Determine overall status
        failed_checks = [
            name for name, check in health_data["checks"].items()
            if check.get("status") not in ["healthy", "ok"]
        ]

        if failed_checks:
            health_data["status"] = "unhealthy"
            health_data["failed_checks"] = failed_checks

        # Return appropriate HTTP status
        if health_data["status"] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_data
            )

        return health_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000

        error_response = {
            "status": "error",
            "timestamp": start_time,
            "response_time_ms": round(response_time_ms, 2),
            "error": str(e)
        }

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_response
        )


@router.get("/liveness")
async def liveness_check() -> Dict[str, str]:
    """
    Minimal liveness check (Kubernetes-style).
    Ultra-fast check to verify the application is running.
    """
    return {
        "status": "alive",
        "timestamp": str(time.time())
    }


@router.get("/readiness")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check to verify all dependencies are available.
    More comprehensive than liveness but still optimized for speed.
    """
    start_time = time.time()

    try:
        # Check critical dependencies
        checks = {}

        # Redis readiness
        try:
            redis_health = await asyncio.wait_for(
                redis_manager.health_check(),
                timeout=0.05  # 50ms timeout for readiness
            )
            checks["redis"] = redis_health["status"] == "healthy"
        except Exception:
            checks["redis"] = False

        # Overall readiness
        ready = all(checks.values())

        end_time = time.time()
        response = {
            "ready": ready,
            "timestamp": start_time,
            "response_time_ms": round((end_time - start_time) * 1000, 2),
            "checks": checks
        }

        if not ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=response
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "ready": False,
                "error": str(e),
                "timestamp": start_time
            }
        )


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with comprehensive system information.
    Note: This endpoint may exceed 100ms latency due to comprehensive checks.
    """
    start_time = time.time()

    try:
        settings = get_settings()

        health_data = {
            "status": "healthy",
            "timestamp": start_time,
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": {
                "debug": settings.debug,
                "log_level": settings.log_level
            },
            "checks": {},
            "metrics": {}
        }

        # Detailed Redis health
        redis_health = await redis_manager.health_check()
        health_data["checks"]["redis"] = redis_health

        # System metrics
        import psutil
        health_data["metrics"]["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }

        # Response time
        end_time = time.time()
        health_data["response_time_ms"] = round((end_time - start_time) * 1000, 2)

        return health_data

    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e)}
        )
