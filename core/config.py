"""
Secure configuration management for the BOT application.
Uses 🔑 placeholders for all secrets and provides environment-based configuration.
"""
import os
import secrets
from typing import Optional

from pydantic import BaseSettings, validator
from pydantic.fields import Field


class Settings(BaseSettings):
    """Application settings with secure defaults and validation."""

    # Core application settings
    app_name: str = "BOT"
    app_version: str = "1.0.0"
    debug: bool = False

    # Security settings
    secret_key: str = Field(
        default="🔑 SECRET_KEY",
        min_length=32,
        description="Secret key for cryptographic operations (min 32 chars)"
    )

    # Database configuration
    database_url: str = Field(
        default="🔑 DATABASE_URL",
        description="PostgreSQL database connection URL"
    )

    # Redis configuration
    redis_url: str = Field(
        default="🔑 REDIS_URL",
        description="Redis connection URL"
    )
    redis_max_connections: int = 50
    redis_socket_timeout: float = 5.0
    redis_socket_connect_timeout: float = 5.0

    # WebSocket configuration
    websocket_max_message_size: int = 16 * 1024  # 16KB
    websocket_ping_interval: int = 20
    websocket_ping_timeout: int = 60

    # CORS configuration
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:8000",
        ]
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )
    cors_allow_headers: list[str] = Field(
        default_factory=lambda: ["*"]
    )

    # Rate limiting configuration
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    rate_limit_burst: int = 20

    # Health check configuration
    health_check_timeout: float = 0.1  # 100ms baseline

    # Server configuration
    host: str = Field(
        default="127.0.0.1",
        description=(
            "Host to bind server to. Use 0.0.0.0 for all interfaces "
            "(WARNING: Security risk)"
        )
    )
    port: int = Field(
        default=8000,
        description="Port to bind server to"
    )

    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @validator("secret_key")
    def validate_secret_key(self, v):
        """Ensure secret key meets minimum security requirements."""
        if v == "🔑 SECRET_KEY":
            # In development, generate a secure random key
            if os.getenv("ENVIRONMENT", "development") == "development":
                return secrets.token_urlsafe(32)
            else:
                raise ValueError(
                    "SECRET_KEY must be set in production. "
                    "Generate with: python -c 'import secrets; "
                    "print(secrets.token_urlsafe(32))'"
                )
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @validator("host")
    def validate_host(self, v):
        """Validate host binding - warn about security implications."""
        if v == "0.0.0.0":  # nosec S104
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                "⚠️  SECURITY WARNING: Binding to 0.0.0.0 exposes the application "
                "to all network interfaces. Ensure proper firewall configuration."
            )
        return v

    @validator("cors_origins")
    def validate_cors_origins(self, v):
        """Ensure no wildcard CORS origins in production."""
        if os.getenv("ENVIRONMENT") == "production" and "*" in v:
            raise ValueError("Wildcard CORS origins not allowed in production")
        return v

    @validator("database_url")
    def validate_database_url(self, v):
        """Validate database URL format."""
        if v == "🔑 DATABASE_URL":
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError("DATABASE_URL must be set in production")
            # Return development default
            return "postgresql://user:password@localhost:5432/botdb"
        return v

    @validator("redis_url")
    def validate_redis_url(self, v):
        """Validate Redis URL format."""
        if v == "🔑 REDIS_URL":
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError("REDIS_URL must be set in production")
            # Return development default
            return "redis://localhost:6379/0"
        return v

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance (singleton)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings():
    """Reset settings for testing purposes."""
    global _settings
    _settings = None
