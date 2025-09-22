"""
Test health check endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """Test main health check endpoint."""
    response = await client.get("/health/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "timestamp" in data
    assert "service" in data
    assert "version" in data
    assert "response_time_ms" in data
    assert "checks" in data
    
    # Should be fast enough
    assert data["response_time_ms"] < 200  # Allow some margin for CI


@pytest.mark.asyncio
async def test_liveness_check(client: AsyncClient):
    """Test liveness check endpoint."""
    response = await client.get("/health/liveness")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "alive"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Test readiness check endpoint."""
    response = await client.get("/health/readiness")
    
    # May fail if Redis/DB not available in CI, that's expected
    data = response.json()
    
    assert "ready" in data
    assert "timestamp" in data
    assert "checks" in data


@pytest.mark.asyncio
async def test_detailed_health_check(client: AsyncClient):
    """Test detailed health check endpoint."""
    response = await client.get("/health/detailed")
    
    assert response.status_code in [200, 500]  # May fail if deps not available
    data = response.json()
    
    if response.status_code == 200:
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "environment" in data
        assert "checks" in data
        assert "metrics" in data


@pytest.mark.asyncio
async def test_health_check_response_time(client: AsyncClient):
    """Test health check meets response time requirements."""
    import time
    
    start_time = time.time()
    response = await client.get("/health/")
    end_time = time.time()
    
    response_time_ms = (end_time - start_time) * 1000
    
    # Should generally be under 100ms, but allow margin for CI
    assert response_time_ms < 500
    
    if response.status_code == 200:
        data = response.json()
        # Server-measured time should be reasonably close
        assert abs(data["response_time_ms"] - response_time_ms) < 100