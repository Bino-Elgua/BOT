# 🔑 Secrets Management Guide

This document explains how to securely manage secrets and sensitive configuration in the BOT application.

## 🎯 Overview

The BOT application uses 🔑 placeholder symbols to indicate where secrets should be provided. **Never commit actual secrets to version control**.

## 🔧 Required Secrets

### Core Application Secrets
- **🔑 SECRET_KEY**: Cryptographic key for security operations
- **🔑 DATABASE_URL**: PostgreSQL connection string
- **🔑 REDIS_URL**: Redis connection string

### Additional Configuration
- **🔑 DB_PASSWORD**: Database password for Docker Compose

## 🛠️ Setup Instructions

### 1. Generate Secure Secret Key
```bash
# Generate a cryptographically secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Create Environment File
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and replace 🔑 placeholders with actual values
```

### 3. Replace Placeholders

#### Example .env Configuration:
```bash
# Replace this:
SECRET_KEY=🔑 SECRET_KEY

# With this (example - generate your own):
SECRET_KEY=your-actual-secret-key-32-chars-minimum

# Replace this:
DATABASE_URL=🔑 DATABASE_URL

# With this (example):
DATABASE_URL=postgresql://username:password@localhost:5432/database

# Replace this:
REDIS_URL=🔑 REDIS_URL

# With this (example):
REDIS_URL=redis://localhost:6379/0
```

## 🐳 Docker Deployment

### For Docker Compose:
1. Create `.env` file in the project root
2. Replace all 🔑 placeholders with actual values
3. The Docker Compose file will automatically use values from `.env`

```bash
# Example .env for Docker
SECRET_KEY=your-generated-secret-key
DATABASE_URL=postgresql://botuser:your-db-password@postgres:5432/botdb
REDIS_URL=redis://redis:6379/0
DB_PASSWORD=your-database-password
```

### For Production Docker:
```bash
# Pass secrets as environment variables
docker run -e SECRET_KEY="your-secret" \
           -e DATABASE_URL="your-db-url" \
           -e REDIS_URL="your-redis-url" \
           your-app-image
```

## ☁️ Cloud Deployment

### Environment Variables
Set the following environment variables in your cloud platform:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret key | `your-32-char-secret` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection | `redis://host:6379/0` |
| `ENVIRONMENT` | Deployment environment | `production` |

### Platform-Specific Instructions

#### Heroku:
```bash
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set DATABASE_URL="your-database-url"
heroku config:set REDIS_URL="your-redis-url"
heroku config:set ENVIRONMENT="production"
```

#### AWS ECS/Fargate:
- Use AWS Systems Manager Parameter Store or AWS Secrets Manager
- Configure task definition with secret ARNs
- Never include secrets in container images

#### Kubernetes:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: bot-secrets
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key"
  DATABASE_URL: "your-database-url"
  REDIS_URL: "your-redis-url"
```

## 🔒 Security Best Practices

### Secret Generation
- **SECRET_KEY**: Minimum 32 characters, cryptographically random
- **Passwords**: Use strong, unique passwords
- **URLs**: Include credentials only in connection strings, never log them

### Secret Rotation
- Rotate secrets regularly (quarterly recommended)
- Use a secret management system in production
- Monitor for compromised credentials

### Access Control
- Limit who has access to production secrets
- Use least-privilege principle
- Audit secret access regularly

### Storage
- **Never commit secrets to Git**
- Use encrypted storage for secrets at rest
- Use secure transmission (TLS) for secrets in transit
- Consider using dedicated secret management tools

## 🚨 Security Violations

### What NOT to Do:
❌ Commit `.env` files with real secrets  
❌ Include secrets in Dockerfile  
❌ Log secrets or credentials  
❌ Share secrets via insecure channels  
❌ Use weak or default passwords  
❌ Reuse secrets across environments  

### If Secrets are Compromised:
1. **Immediately rotate** all affected secrets
2. **Revoke access** for compromised credentials
3. **Audit logs** for unauthorized access
4. **Update all deployments** with new secrets
5. **Document the incident** for future prevention

## 🛠️ Development vs Production

### Development Environment:
- Use `.env` file with development secrets
- Never use production secrets in development
- Use local instances of databases and Redis when possible

### Production Environment:
- Use environment variables or secret management systems
- Never use `.env` files in production containers
- Implement proper access controls and auditing

## 📋 Validation Checklist

Before deploying, ensure:
- [ ] All 🔑 placeholders replaced with actual values
- [ ] SECRET_KEY is at least 32 characters long
- [ ] No secrets committed to version control
- [ ] Database and Redis connections tested
- [ ] Environment variables properly set
- [ ] Access controls configured
- [ ] Monitoring and alerting enabled

## 🆘 Troubleshooting

### Common Issues:

#### "SECRET_KEY must be set in production":
- Ensure SECRET_KEY environment variable is set
- Verify the key is at least 32 characters long

#### "DATABASE_URL must be set in production":
- Check DATABASE_URL environment variable
- Verify connection string format: `postgresql://user:pass@host:port/db`

#### "Redis connection failed":
- Verify REDIS_URL format: `redis://host:port/db`
- Check Redis server is accessible from application

#### Application won't start:
- Check all required environment variables are set
- Verify no 🔑 placeholders remain in production
- Check application logs for specific error messages

## 📞 Support

For questions about secrets management:
- Check this documentation first
- Review error messages and logs
- Contact the development team
- For security issues, follow the Security Policy

---

**Remember**: When in doubt, treat it as a secret and protect it accordingly!