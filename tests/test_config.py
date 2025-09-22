"""
Test configuration management.
"""
import os

import pytest

from core.config import get_settings, reset_settings


def test_settings_initialization():
    """Test settings initialization with defaults."""
    settings = get_settings()
    assert settings.app_name == "BOT"
    assert settings.app_version == "1.0.0"
    assert settings.websocket_max_message_size == 16 * 1024  # 16KB
    assert settings.redis_max_connections == 50


def test_secret_key_validation():
    """Test secret key validation."""
    # Reset to get fresh settings
    reset_settings()

    # Should work with test environment
    settings = get_settings()
    assert len(settings.secret_key) >= 32


def test_cors_validation_development():
    """Test CORS validation in development."""
    os.environ["ENVIRONMENT"] = "development"
    reset_settings()

    settings = get_settings()
    # Should allow any origins in development
    assert isinstance(settings.cors_origins, list)


def test_websocket_message_size_limit():
    """Test WebSocket message size configuration."""
    settings = get_settings()
    assert settings.websocket_max_message_size == 16384  # 16KB exactly


def test_rate_limiting_config():
    """Test rate limiting configuration."""
    settings = get_settings()
    assert settings.rate_limit_requests == 100
    assert settings.rate_limit_window == 60
    assert settings.rate_limit_burst == 20


def test_health_check_timeout():
    """Test health check timeout configuration."""
    settings = get_settings()
    assert settings.health_check_timeout == 0.1  # 100ms


def test_redis_connection_config():
    """Test Redis connection configuration."""
    settings = get_settings()
    assert settings.redis_max_connections == 50
    assert settings.redis_socket_timeout == 5.0
    assert settings.redis_socket_connect_timeout == 5.0


@pytest.mark.parametrize("env_var,expected", [
    ("DEBUG", False),
    ("LOG_LEVEL", "INFO"),
])
def test_environment_variables(env_var, expected):
    """Test environment variable handling."""
    reset_settings()
    settings = get_settings()

    if env_var == "DEBUG":
        assert settings.debug == expected
    elif env_var == "LOG_LEVEL":
        assert settings.log_level == expected
