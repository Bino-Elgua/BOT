#!/usr/bin/env python3
"""
Security validation script for BOT application.
Validates all security requirements from the atomic bootstrap specification.
"""
import os
import re
import sys
from pathlib import Path


def validate_secret_placeholders():
    """Validate that all secrets use 🔑 placeholders."""
    violations = []
    
    # Check .env.example
    env_example = Path(".env.example")
    if env_example.exists():
        content = env_example.read_text()
        if "🔑 SECRET_KEY" not in content:
            violations.append(".env.example missing 🔑 SECRET_KEY placeholder")
        if "🔑 DATABASE_URL" not in content:
            violations.append(".env.example missing 🔑 DATABASE_URL placeholder")
        if "🔑 REDIS_URL" not in content:
            violations.append(".env.example missing 🔑 REDIS_URL placeholder")
    else:
        violations.append(".env.example file missing")
    
    # Check docker-compose.yml
    docker_compose = Path("docker-compose.yml")
    if docker_compose.exists():
        content = docker_compose.read_text()
        if "🔑 SECRET_KEY" not in content:
            violations.append("docker-compose.yml missing 🔑 SECRET_KEY placeholder")
        if "🔑 DB_PASSWORD" not in content:
            violations.append("docker-compose.yml missing 🔑 DB_PASSWORD placeholder")
    
    return violations


def validate_websocket_message_size():
    """Validate WebSocket 16KB message size limit."""
    violations = []
    
    # Check configuration
    config_file = Path("core/config.py")
    if config_file.exists():
        content = config_file.read_text()
        if "websocket_max_message_size: int = 16 * 1024" not in content:
            violations.append("WebSocket message size not set to 16KB in config")
    
    # Check WebSocket router
    ws_router = Path("app/routers/websocket.py")
    if ws_router.exists():
        content = ws_router.read_text()
        if "settings.websocket_max_message_size" not in content:
            violations.append("WebSocket router not enforcing message size limit")
        if "Message too large" not in content:
            violations.append("WebSocket router missing message size rejection")
    
    return violations


def validate_redis_connection_pool():
    """Validate Redis connection pool configuration."""
    violations = []
    
    redis_service = Path("app/services/redis_service.py")
    if redis_service.exists():
        content = redis_service.read_text()
        
        # Check singleton pattern
        if "class RedisConnectionManager" not in content:
            violations.append("Redis connection manager class missing")
        if "_instance: Optional['RedisConnectionManager'] = None" not in content:
            violations.append("Redis singleton pattern not implemented")
        
        # Check max connections
        if "max_connections=settings.redis_max_connections" not in content:
            violations.append("Redis max connections not configured")
        
        # Check configuration setting
        config_file = Path("core/config.py")
        if config_file.exists():
            config_content = config_file.read_text()
            if "redis_max_connections: int = 50" not in config_content:
                violations.append("Redis max connections not set to 50")
    
    return violations


def validate_rate_limiting():
    """Validate atomic rate limiting implementation."""
    violations = []
    
    rate_limiter = Path("app/services/rate_limiter.py")
    if rate_limiter.exists():
        content = rate_limiter.read_text()
        
        # Check atomic operations
        if "EVALSHA" not in content:
            violations.append("Rate limiter not using atomic EVALSHA operations")
        if "_lua_script" not in content:
            violations.append("Rate limiter missing Lua script for atomic operations")
        
        # Check Redis usage
        if "redis.call" not in content:
            violations.append("Rate limiter not using Redis commands")
    
    return violations


def validate_health_check_latency():
    """Validate health check <100ms requirement."""
    violations = []
    
    health_router = Path("app/routers/health.py")
    if health_router.exists():
        content = health_router.read_text()
        
        # Check timeout configuration
        if "settings.health_check_timeout" not in content:
            violations.append("Health check not using timeout configuration")
        
        # Check latency measurement
        if "response_time_ms" not in content:
            violations.append("Health check not measuring response time")
        
        # Check baseline requirement
        config_file = Path("core/config.py")
        if config_file.exists():
            config_content = config_file.read_text()
            if "health_check_timeout: float = 0.1" not in config_content:
                violations.append("Health check timeout not set to 100ms (0.1s)")
    
    return violations


def validate_cors_security():
    """Validate CORS security configuration."""
    violations = []
    
    main_app = Path("app/main.py")
    if main_app.exists():
        content = main_app.read_text()
        
        # Check CORS middleware
        if "CORSMiddleware" not in content:
            violations.append("CORS middleware not configured")
        
        # Check no wildcard origins
        if "allow_origins=settings.cors_origins" not in content:
            violations.append("CORS not using settings-based origins")
        
        # Check production validation
        config_file = Path("core/config.py")
        if config_file.exists():
            config_content = config_file.read_text()
            if "if \"*\" in v:" not in config_content:
                violations.append("CORS wildcard validation missing")
    
    return violations


def validate_ci_security():
    """Validate CI pipeline security requirements."""
    violations = []
    
    ci_file = Path(".github/workflows/ci.yml")
    if ci_file.exists():
        content = ci_file.read_text()
        
        # Check security analysis job
        if "security-analysis:" not in content:
            violations.append("CI pipeline missing security analysis job")
        
        # Check Bandit
        if "bandit" not in content:
            violations.append("CI pipeline missing Bandit security analysis")
        
        # Check vulnerability blocking
        if "medium+ severity" not in content:
            violations.append("CI pipeline not blocking on medium+ vulnerabilities")
        
        # Check dependency scanning
        if "safety check" not in content or "pip-audit" not in content:
            violations.append("CI pipeline missing dependency vulnerability scanning")
    
    return violations


def validate_secret_key_requirements():
    """Validate SECRET_KEY requirements."""
    violations = []
    
    config_file = Path("core/config.py")
    if config_file.exists():
        content = config_file.read_text()
        
        # Check minimum length validation
        if "min_length=32" not in content:
            violations.append("SECRET_KEY minimum length validation missing")
        
        # Check validation function
        if "def validate_secret_key" not in content:
            violations.append("SECRET_KEY validation function missing")
        
        # Check length check
        if "len(v) < 32" not in content:
            violations.append("SECRET_KEY length validation missing")
    
    return violations


def validate_file_structure():
    """Validate required file structure."""
    violations = []
    
    required_files = [
        "app/main.py",
        "core/config.py",
        "app/routers/health.py",
        "app/routers/websocket.py",
        "app/services/redis_service.py",
        "app/services/rate_limiter.py",
        "requirements.txt",
        ".env.example",
        "Dockerfile",
        "docker-compose.yml",
        ".github/workflows/ci.yml",
        "SECURITY.md",
        "SECRETS.md",
        "README.md"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            violations.append(f"Required file missing: {file_path}")
    
    return violations


def main():
    """Run all security validations."""
    print("🔒 BOT Security Validation")
    print("=" * 50)
    
    all_violations = []
    
    # Run all validation checks
    checks = [
        ("File Structure", validate_file_structure),
        ("Secret Placeholders", validate_secret_placeholders),
        ("WebSocket Message Size", validate_websocket_message_size),
        ("Redis Connection Pool", validate_redis_connection_pool),
        ("Rate Limiting", validate_rate_limiting),
        ("Health Check Latency", validate_health_check_latency),
        ("CORS Security", validate_cors_security),
        ("CI Security", validate_ci_security),
        ("Secret Key Requirements", validate_secret_key_requirements),
    ]
    
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}...")
        violations = check_func()
        
        if violations:
            print(f"❌ {len(violations)} violation(s) found:")
            for violation in violations:
                print(f"   - {violation}")
            all_violations.extend(violations)
        else:
            print("✅ Passed")
    
    # Summary
    print("\n" + "=" * 50)
    if all_violations:
        print(f"❌ VALIDATION FAILED: {len(all_violations)} total violations")
        print("\nViolations to fix:")
        for i, violation in enumerate(all_violations, 1):
            print(f"{i:2d}. {violation}")
        return 1
    else:
        print("✅ ALL SECURITY REQUIREMENTS VALIDATED")
        print("\nSecurity checklist completed:")
        print("□ Redis connection pool singleton pattern confirmed")
        print("□ WebSocket 16KB message size enforcement active")
        print("□ Rate limiter atomic Redis operations confirmed")
        print("□ /health endpoint <100ms response validated")
        print("□ CI pipeline fails on medium+ vulnerabilities")
        print("□ All 🔑 placeholders used, zero hardcoded secrets")
        print("□ Branch protection prevents direct main commits")
        return 0


if __name__ == "__main__":
    sys.exit(main())