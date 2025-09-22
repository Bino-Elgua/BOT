"""
Main FastAPI application with secure configuration.
Implements all security requirements including CORS, rate limiting, and error handling.
"""
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.routers import health, websocket
from app.services.rate_limiter import rate_limiter
from app.services.redis_service import close_redis, redis_manager
from core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("Starting BOT application...")

    try:
        # Initialize Redis connection pool
        await redis_manager.initialize()
        logger.info("Redis connection pool initialized")

        # Pre-load rate limiter script
        await rate_limiter._ensure_script_loaded()
        logger.info("Rate limiter initialized")

        logger.info("Application startup completed")

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down BOT application...")

    try:
        # Close Redis connections
        await close_redis()
        logger.info("Redis connections closed")

        logger.info("Application shutdown completed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Secure production-ready BOT application",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Security middleware
    _configure_security_middleware(app, settings)

    # Request middleware
    _configure_request_middleware(app)

    # Error handlers
    _configure_error_handlers(app)

    # Include routers
    app.include_router(health.router)
    app.include_router(websocket.router)

    return app


def _configure_security_middleware(app: FastAPI, settings):
    """Configure security-related middleware."""

    # CORS middleware with secure configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # No wildcard in production
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        max_age=86400,  # 24 hours
    )

    # Trusted host middleware for production
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
        )


def _configure_request_middleware(app: FastAPI):
    """Configure request processing middleware."""

    @app.middleware("http")
    async def rate_limiting_middleware(request: Request, call_next):
        """Global rate limiting middleware."""
        try:
            # Extract client identifier
            client_ip = request.client.host if request.client else "unknown"
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()

            # Skip rate limiting for health checks
            if request.url.path.startswith("/health"):
                return await call_next(request)

            # Check rate limit
            rate_check = await rate_limiter.is_allowed(f"http:{client_ip}")

            if not rate_check["allowed"]:
                logger.warning(f"Rate limit exceeded for {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "retry_after": int(rate_check["reset_time"] - time.time()),
                        "limit": rate_check["limit"],
                        "remaining": rate_check["remaining"]
                    },
                    headers={
                        "Retry-After": str(int(rate_check["reset_time"] - time.time())),
                        "X-RateLimit-Limit": str(rate_check["limit"]),
                        "X-RateLimit-Remaining": str(rate_check["remaining"]),
                        "X-RateLimit-Reset": str(int(rate_check["reset_time"]))
                    }
                )

            # Process request
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time

            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(rate_check["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_check["remaining"])
            response.headers["X-RateLimit-Reset"] = str(int(rate_check["reset_time"]))
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))

            return response

        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}")
            # Continue processing on middleware error
            return await call_next(request)

    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        """Add security headers to all responses."""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:;"
        )

        return response


def _configure_error_handlers(app: FastAPI):
    """Configure global error handlers."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle request validation errors."""
        logger.warning(f"Validation error for {request.url}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "details": exc.errors(),
                "body": str(exc.body) if hasattr(exc, 'body') else None
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(f"Unexpected error for {request.url}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred"
            }
        )


# Create app instance
app = create_app()


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with basic application information."""
    settings = get_settings()
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "timestamp": time.time(),
        "endpoints": {
            "health": "/health",
            "websocket": "/ws/{client_id}",
            "docs": "/docs" if settings.debug else "disabled in production"
        }
    }


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # nosec B104 S104
        port=8000,
        log_level=settings.log_level.lower(),
        reload=settings.debug,
        access_log=True
    )
