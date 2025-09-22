# 🤖 BOT - Secure Production-Ready Application

A secure, scalable FastAPI application with WebSocket support, Redis-based rate limiting, and comprehensive security features.

## ✨ Features

- 🔐 **Security First**: No hardcoded secrets, comprehensive security headers, CORS protection
- ⚡ **High Performance**: Redis connection pooling, atomic rate limiting, <100ms health checks
- 🔌 **WebSocket Support**: Real-time communication with 16KB message size limits
- 📊 **Monitoring**: Health checks, metrics, connection statistics
- 🚀 **Production Ready**: Docker deployment, CI/CD pipeline, security scanning
- 🛡️ **Compliance**: Security best practices, vulnerability scanning, audit trails

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/Bino-Elgua/BOT.git
cd BOT

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Secrets

```bash
# Copy environment template
cp .env.example .env

# Generate secret key
python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')"

# Edit .env and replace 🔑 placeholders with actual values
# See SECRETS.md for detailed instructions
```

**Required Configuration:**
- `SECRET_KEY`: Generate with the command above
- `DATABASE_URL`: Your PostgreSQL connection string
- `REDIS_URL`: Your Redis connection string

### 3. Start Services

#### Option A: Using Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app
```

#### Option B: Local Development
```bash
# Start PostgreSQL and Redis locally
# Then run the application
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# Test WebSocket (using wscat)
npm install -g wscat
wscat -c ws://localhost:8000/ws/test-client
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Cryptographic secret (32+ chars) | 🔑 SECRET_KEY | Yes |
| `DATABASE_URL` | PostgreSQL connection string | 🔑 DATABASE_URL | Yes |
| `REDIS_URL` | Redis connection string | 🔑 REDIS_URL | Yes |
| `ENVIRONMENT` | Environment (development/production) | development | No |
| `DEBUG` | Enable debug mode | false | No |
| `LOG_LEVEL` | Logging level | INFO | No |

See `.env.example` for complete configuration options.

## 📡 API Endpoints

### Health Checks
- `GET /health/` - Comprehensive health check (<100ms)
- `GET /health/liveness` - Basic liveness check
- `GET /health/readiness` - Readiness check for dependencies
- `GET /health/detailed` - Detailed system information

### WebSocket
- `WS /ws/{client_id}` - WebSocket connection with rate limiting

### Statistics
- `GET /ws/stats` - WebSocket connection statistics

## 🔒 Security Features

### Built-in Security
- ✅ No wildcard CORS in production
- ✅ Rate limiting with Redis (100 req/min default)
- ✅ WebSocket message size limit (16KB)
- ✅ Security headers on all responses
- ✅ Input validation and sanitization
- ✅ Secure error handling

### Security Headers
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: [strict policy]
```

### Rate Limiting
- **HTTP**: 100 requests per minute per IP
- **WebSocket**: Rate limited connections and messages
- **Atomic**: Redis-based atomic operations
- **Headers**: Rate limit info in response headers

## 🐳 Docker Deployment

### Build and Run
```bash
# Build image
docker build -t bot-app .

# Run container
docker run -p 8000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e DATABASE_URL="your-db-url" \
  -e REDIS_URL="your-redis-url" \
  bot-app
```

### Docker Compose
```bash
# Development with dev tools
docker-compose --profile dev up -d

# Production
docker-compose up -d
```

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov=core --cov-report=html

# Run security tests
bandit -r app/ core/
safety check
pip-audit
```

### Test Coverage
- Unit tests for all core functionality
- Integration tests with Redis and PostgreSQL
- WebSocket connection testing
- Security validation tests

## 🔍 Monitoring

### Health Monitoring
- **Baseline**: Health checks complete in <100ms
- **Dependencies**: Redis and PostgreSQL connectivity
- **Metrics**: Response times, connection counts, error rates

### Logging
- Structured JSON logging
- Security event logging
- Performance metrics
- Error tracking

### Metrics Available
- Request/response times
- Rate limiting statistics
- WebSocket connection metrics
- Database connection pool status
- Redis connection pool status

## 🛠️ Development

### Code Quality
```bash
# Format code
black app/ core/ tests/
isort app/ core/ tests/

# Lint code
ruff check app/ core/ tests/

# Type checking
mypy app/ core/
```

### Security Scanning
```bash
# Security analysis
bandit -r app/ core/

# Dependency vulnerabilities
safety check
pip-audit

# CI/CD automatically runs these checks
```

## 🚀 CI/CD Pipeline

### Automated Checks
- ✅ Code linting and formatting
- ✅ Type checking with MyPy
- ✅ Security analysis with Bandit
- ✅ Dependency vulnerability scanning
- ✅ Unit and integration testing
- ✅ Docker image building and pushing

### Security Gates
- **Blocks merge** on medium+ severity vulnerabilities
- **Automated security reports** on pull requests
- **Dependency monitoring** for known vulnerabilities

## 📚 Documentation

- [Security Policy](SECURITY.md) - Security features and reporting
- [Secrets Management](SECRETS.md) - How to manage secrets securely
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (dev mode)

## 🔧 Troubleshooting

### Common Issues

#### Application won't start
```bash
# Check configuration
python -c "from core.config import get_settings; print(get_settings())"

# Verify database connection
python -c "import asyncpg; asyncio.run(asyncpg.connect('your-db-url'))"

# Check Redis connection
redis-cli -u your-redis-url ping
```

#### Health check fails
- Verify Redis and PostgreSQL are running
- Check network connectivity
- Review application logs

#### WebSocket connections fail
- Check CORS configuration
- Verify rate limiting settings
- Test with a WebSocket client

### Debug Mode
```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with debug logging
python -m uvicorn app.main:app --reload --log-level debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following security guidelines
4. Run tests and security checks
5. Submit a pull request

### Security Guidelines
- Never commit secrets or credentials
- Use 🔑 placeholders for sensitive configuration
- Run security scans before submitting PRs
- Follow secure coding practices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the docs/ directory
- **Security Issues**: See [SECURITY.md](SECURITY.md)
- **General Issues**: Create a GitHub issue
- **Questions**: Start a discussion

---

**Security Notice**: This application implements comprehensive security measures. Always use 🔑 placeholders for secrets and follow the security guidelines in [SECURITY.md](SECURITY.md).