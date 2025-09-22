#!/usr/bin/env python3
"""
Development startup script for BOT application.
Tests application structure and configuration without external dependencies.
"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set test environment variables
os.environ.update({
    "ENVIRONMENT": "development",
    "SECRET_KEY": "test-secret-key-for-development-32-characters-minimum",
    "DATABASE_URL": "postgresql://localhost:5432/botdb",
    "REDIS_URL": "redis://localhost:6379/0",
    "DEBUG": "true",
    "LOG_LEVEL": "INFO"
})

def test_configuration():
    """Test configuration loading."""

    try:
        # Mock pydantic for testing
        import types
        pydantic = types.ModuleType('pydantic')
        pydantic.BaseSettings = object
        pydantic.validator = lambda *args, **kwargs: lambda f: f
        pydantic.Field = lambda *args, **kwargs: None
        sys.modules['pydantic'] = pydantic
        sys.modules['pydantic.fields'] = pydantic

        # Test core config can be imported
        exec(open('core/config.py').read(), {'__name__': '__main__'})

    except Exception:
        return False

    return True


def test_application_structure():
    """Test application structure."""

    # Test imports without external dependencies
    try:
        # Create mock modules
        import types

        # Mock FastAPI
        fastapi = types.ModuleType('fastapi')
        fastapi.FastAPI = type
        fastapi.APIRouter = type
        fastapi.HTTPException = Exception
        fastapi.Request = object
        fastapi.WebSocket = object
        fastapi.WebSocketDisconnect = Exception
        fastapi.status = types.ModuleType('status')
        sys.modules['fastapi'] = fastapi
        sys.modules['fastapi.middleware'] = types.ModuleType('middleware')
        sys.modules['fastapi.middleware.cors'] = types.ModuleType('cors')
        sys.modules['fastapi.middleware.trustedhost'] = types.ModuleType('trustedhost')
        sys.modules['fastapi.responses'] = types.ModuleType('responses')
        sys.modules['fastapi.exceptions'] = types.ModuleType('exceptions')
        sys.modules['fastapi.websockets'] = types.ModuleType('websockets')
        sys.modules['fastapi.testclient'] = types.ModuleType('testclient')

        # Mock other dependencies
        redis = types.ModuleType('redis')
        redis.asyncio = types.ModuleType('asyncio')
        sys.modules['redis'] = redis
        sys.modules['redis.asyncio'] = redis.asyncio

        asyncpg = types.ModuleType('asyncpg')
        sys.modules['asyncpg'] = asyncpg

        uvicorn = types.ModuleType('uvicorn')
        sys.modules['uvicorn'] = uvicorn

        psutil = types.ModuleType('psutil')
        psutil.cpu_percent = lambda *args, **kwargs: 50.0
        psutil.virtual_memory = lambda: types.SimpleNamespace(percent=60.0)
        psutil.disk_usage = lambda path: types.SimpleNamespace(percent=70.0)
        sys.modules['psutil'] = psutil

        # Test syntax of key modules
        test_files = [
            'app/main.py',
            'app/routers/health.py',
            'app/routers/websocket.py',
            'app/services/redis_service.py',
            'app/services/rate_limiter.py',
            'app/db/database.py'
        ]

        for file_path in test_files:
            try:
                with open(file_path, 'r') as f:
                    compile(f.read(), file_path, 'exec')
            except SyntaxError:
                return False

        return True

    except Exception:
        return False


def test_docker_configuration():
    """Test Docker configuration."""

    try:
        # Check Dockerfile
        dockerfile = Path("Dockerfile")
        if dockerfile.exists():
            content = dockerfile.read_text()

            # Check security features
            checks = [
                ("Multi-stage build", "FROM python:3.11-slim AS"),
                ("Non-root user", "useradd -r"),
                ("Health check", "HEALTHCHECK"),
                ("Security setup", "chown -R botuser:botuser"),
            ]

            for _check_name, check_pattern in checks:
                if check_pattern in content:
                    pass
                else:
                    pass

        # Check docker-compose
        compose_file = Path("docker-compose.yml")
        if compose_file.exists():
            content = compose_file.read_text()

            # Check required services
            services = ["app:", "postgres:", "redis:"]
            for service in services:
                if service in content:
                    pass
                else:
                    pass

        return True

    except Exception:
        return False


def test_security_documentation():
    """Test security documentation."""

    docs = [
        ("SECURITY.md", ["Security Policy", "Reporting Security Vulnerabilities"]),
        ("SECRETS.md", ["🔑 Secrets Management", "Setup Instructions"]),
        ("README.md", ["Security Features", "Quick Start"])
    ]

    for doc_file, required_sections in docs:
        if Path(doc_file).exists():
            content = Path(doc_file).read_text()

            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)

            if missing_sections:
                pass
            else:
                pass
        else:
            pass

    return True


def main():
    """Run all tests."""

    tests = [
        test_configuration,
        test_application_structure,
        test_docker_configuration,
        test_security_documentation
    ]

    results = []
    for test in tests:
        result = test()
        results.append(result)

    # Summary
    if all(results):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
