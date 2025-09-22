"""
Test configuration and fixtures.
"""
import asyncio
import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import app  # noqa: E402
from core.config import reset_settings  # noqa: E402

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-32-chars"  # nosec S105
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://testuser:testpassword@localhost:5432/testdb"
)
os.environ["REDIS_URL"] = os.getenv(
    "TEST_REDIS_URL",
    "redis://localhost:6379/1"  # Use different DB for tests
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sync_client():
    """Create synchronous test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_config():
    """Reset configuration for each test."""
    reset_settings()
    yield
    reset_settings()
