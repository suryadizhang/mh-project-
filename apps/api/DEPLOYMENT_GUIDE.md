# MyHibachi AI Sales CRM - Deployment Guide

## 🚀 Complete Deployment Guide

### Overview

This document provides comprehensive deployment instructions for the
MyHibachi AI Sales CRM system with CQRS architecture, OAuth 2.1 + MFA
authentication, and zero-conflict integration.

## 📋 Prerequisites

### System Requirements

- Python 3.11+
- PostgreSQL 14+ (recommended) or SQLite for development
- Redis (for rate limiting and caching in production)
- Node.js 18+ (for frontend)

### Required Services

- **Email Service**: SMTP, SendGrid, or AWS SES
- **SMS Service**: RingCentral (optional)
- **Payment Processing**: Stripe (optional)

## 🔧 Installation & Setup

### 1. Environment Configuration

Copy the comprehensive configuration template:

```bash
cp .env.comprehensive .env
```

**CRITICAL**: Update these values in your `.env` file:

```bash
# SECURITY (MUST CHANGE)
SECRET_KEY=your-super-secret-key-here-change-in-production
FIELD_ENCRYPTION_KEY=your-base64-encoded-32-byte-encryption-key

# DATABASE
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/myhibachi_crm
DATABASE_URL_SYNC=postgresql://username:password@localhost:5432/myhibachi_crm

# ADMIN ACCOUNT (CHANGE IMMEDIATELY)
DEFAULT_ADMIN_EMAIL=admin@myhibachi.com
DEFAULT_ADMIN_PASSWORD=ChangeThisPassword123!

# EMAIL CONFIGURATION
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=no-reply@myhibachichef.com
```

### 2. Generate Security Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"

# Generate FIELD_ENCRYPTION_KEY
python -c "import base64, secrets; print('FIELD_ENCRYPTION_KEY=' + base64.b64encode(secrets.token_bytes(32)).decode())"
```

### 3. Database Setup

#### PostgreSQL (Recommended for Production)

```bash
# Create database
createdb myhibachi_crm

# Or using psql
psql -c "CREATE DATABASE myhibachi_crm;"
```

#### SQLite (Development Only)

No setup required - will be created automatically.

### 4. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

### 5. Initialize Database

```bash
# Run database migrations
python -m alembic upgrade head

# Create initial data (admin user, etc.)
python scripts/init_db.py
```

## 🚀 Running the Application

### Development Mode

```bash
# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start with workers (recommended)
python -m app.main
```

### Production Mode

```bash
# Using Gunicorn with Uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or using the provided start script
./start.sh
```

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f api
```

### Production Docker

```bash
# Build production image
docker build -f Dockerfile.prod -t myhibachi-crm:latest .

# Run with environment file
docker run -d --env-file .env -p 8000:8000 myhibachi-crm:latest
```

## ☸️ Kubernetes Deployment

### Apply Kubernetes manifests

```bash
# Create namespace
kubectl create namespace myhibachi

# Apply configurations
kubectl apply -f k8s/
```

### Verify deployment

```bash
# Check pods
kubectl get pods -n myhibachi

# Check services
kubectl get svc -n myhibachi

# View logs
kubectl logs -f deployment/myhibachi-api -n myhibachi
```

## 🔒 Security Configuration

### 1. SSL/TLS Setup

For production, configure SSL certificates:

```bash
# In your .env file
SSL_CERT_PATH=/path/to/certificate.pem
SSL_KEY_PATH=/path/to/private-key.pem
```

### 2. Firewall Rules

```bash
# Allow HTTP/HTTPS traffic
ufw allow 80/tcp
ufw allow 443/tcp

# Allow API port (if not behind reverse proxy)
ufw allow 8000/tcp
```

### 3. Database Security

```bash
# Create dedicated database user
CREATE USER myhibachi_app WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE myhibachi_crm TO myhibachi_app;
GRANT USAGE ON SCHEMA public TO myhibachi_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO myhibachi_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO myhibachi_app;
```

## 📊 Monitoring & Health Checks

### Health Check Endpoints

- **API Health**: `GET /health`
- **Database Health**: `GET /health/db`
- **Worker Health**: `GET /health/workers`
- **Features Status**: `GET /health/features`

### Metrics (if enabled)

- **Prometheus Metrics**: `GET /metrics`
- **Application Metrics**: Available on port 8001

### Logging Configuration

```bash
# Set log level in .env
LOG_LEVEL=info  # debug, info, warning, error

# View logs
tail -f /var/log/myhibachi/api.log
```

## 🔧 Background Workers

The system includes background workers for:

- **Email Processing**: Outbox pattern for reliable email delivery
- **SMS Messaging**: RingCentral integration with retry logic
- **Payment Processing**: Stripe webhook processing
- **Audit Log Processing**: Asynchronous audit trail

### Worker Management

```bash
# Check worker status
curl http://localhost:8000/health/workers

# Restart workers (if using systemd)
systemctl restart myhibachi-workers
```

## 🎯 Testing the Deployment

### 1. API Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "environment": "production"
}
```

### 2. Authentication Test

```bash
# Login with admin credentials
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@myhibachi.com", "password": "ChangeThisPassword123!"}'
```

### 3. Database Connection Test

```bash
curl http://localhost:8000/health/db
```

### 4. Feature Status Test

```bash
curl http://localhost:8000/health/features
```

## 🔄 Integration with Existing System

### Zero-Conflict Integration

The CRM system is designed for zero-conflict integration:

1. **Separate Database Schemas**: Core, Events, Integration, and Read
   schemas
2. **Event Sourcing**: All changes tracked through events
3. **API Versioning**: Backward-compatible API design
4. **Feature Flags**: Gradual rollout capability

### Frontend Integration

```javascript
// Configure API client
const apiClient = new CRMApiClient({
  baseURL: 'http://localhost:8000',
  apiKey: 'your-api-key',
});

// Use CRM features
const bookings = await apiClient.bookings.list();
```

## 📁 File Structure

```
apps/api/
├── app/
│   ├── main.py              # FastAPI application with CRM integration
│   ├── config.py            # Comprehensive configuration management
│   ├── database.py          # Database configuration with CRM support
│   ├── auth/               # OAuth 2.1 + MFA authentication system
│   ├── crm/                # Complete CRM implementation
│   ├── workers/            # Background workers for external integrations
│   └── utils/              # Utilities including encryption
├── migrations/              # Database migrations
├── scripts/                # Deployment and maintenance scripts
├── requirements.txt        # Python dependencies
├── .env.comprehensive      # Complete configuration template
└── docker-compose.yml      # Docker deployment configuration
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Errors**

   ```bash
   # Check database status
   pg_isready -h localhost -p 5432

   # Verify credentials
   psql -h localhost -U username -d myhibachi_crm
   ```

2. **Worker Not Starting**

   ```bash
   # Check worker configuration
   curl http://localhost:8000/health/workers

   # Review logs
   tail -f /var/log/myhibachi/workers.log
   ```

3. **Authentication Issues**

   ```bash
   # Verify JWT configuration
   python -c "from app.config import settings; print(settings.SECRET_KEY)"

   # Check MFA setup
   curl http://localhost:8000/api/auth/mfa/status
   ```

### Debug Mode

Enable debug mode for detailed error information:

```bash
# In .env file
DEBUG=true
LOG_LEVEL=debug
```

## 📞 Support

For deployment issues:

1. Check the logs: `/var/log/myhibachi/`
2. Verify configuration: Review `.env` file
3. Test connectivity: Use health check endpoints
4. Review documentation: This deployment guide

## 🔐 Security Checklist

Before production deployment:

- [ ] Change default SECRET_KEY
- [ ] Generate new FIELD_ENCRYPTION_KEY
- [ ] Update default admin credentials
- [ ] Configure SSL/TLS certificates
- [ ] Set up firewall rules
- [ ] Configure rate limiting
- [ ] Enable audit logging
- [ ] Restrict CORS origins
- [ ] Set secure database passwords
- [ ] Configure backup strategy

## 🚀 Go Live Checklist

- [ ] All environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Health checks passing
- [ ] Workers running successfully
- [ ] External integrations tested
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Security audit completed
- [ ] Performance testing done

Your MyHibachi AI Sales CRM system is now ready for production
deployment! 🎉
