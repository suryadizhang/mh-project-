# Environment Configuration Guide

This guide covers all environment variables needed for RingCentral
SMS, IONOS Email, and other services.

## 📋 Table of Contents

- [Backend Environment Variables](#backend-environment-variables)
- [Frontend Environment Variables](#frontend-environment-variables)
- [RingCentral Setup](#ringcentral-setup)
- [IONOS SMTP Setup](#ionos-smtp-setup)
- [Database Configuration](#database-configuration)
- [Security & Compliance](#security--compliance)
- [Development vs Production](#development-vs-production)

---

## Backend Environment Variables

Create `.env` file in `apps/backend/`:

```bash
# ==============================================================================
# DATABASE
# ==============================================================================
DATABASE_URL=postgresql://user:password@localhost:5432/myhibachi
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30

# ==============================================================================
# REDIS (Caching & Celery Broker)
# ==============================================================================
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# ==============================================================================
# RINGCENTRAL SMS INTEGRATION
# ==============================================================================
RINGCENTRAL_CLIENT_ID=your_client_id_here
RINGCENTRAL_CLIENT_SECRET=your_client_secret_here
RINGCENTRAL_JWT_TOKEN=your_jwt_token_here
RINGCENTRAL_SERVER_URL=https://platform.ringcentral.com
RINGCENTRAL_PHONE_NUMBER=+1234567890
RINGCENTRAL_WEBHOOK_URL=https://your-domain.com/api/v1/webhooks/sms/delivery

# SMS Configuration
SMS_COST_PER_SEGMENT=0.0075  # $0.0075 per segment
SMS_MAX_SEGMENTS=10
SMS_ENABLE_TRACKING=true
SMS_DELIVERY_TIMEOUT_SECONDS=300

# ==============================================================================
# IONOS EMAIL (SMTP)
# ==============================================================================
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USER=noreply@your-domain.com
SMTP_PASSWORD=your_smtp_password_here
SMTP_FROM_NAME=MyHibachi
SMTP_FROM_EMAIL=noreply@your-domain.com
SMTP_TIMEOUT=30
SMTP_MAX_RETRIES=3
SMTP_RETRY_DELAY=5

# CAN-SPAM Compliance
COMPANY_NAME=MyHibachi Inc.
COMPANY_ADDRESS=123 Main St, City, ST 12345
UNSUBSCRIBE_URL=https://your-domain.com/unsubscribe

# ==============================================================================
# SECURITY & ENCRYPTION
# ==============================================================================
SECRET_KEY=your_256_bit_secret_key_here_use_secrets.token_urlsafe(32)
FIELD_ENCRYPTION_KEY=your_fernet_key_here_use_Fernet.generate_key()
JWT_SECRET_KEY=your_jwt_secret_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ==============================================================================
# TCPA & COMPLIANCE
# ==============================================================================
TCPA_CONSENT_REQUIRED=true
TCPA_OPT_OUT_KEYWORDS=STOP,UNSUBSCRIBE,CANCEL,END,QUIT
TCPA_HELP_KEYWORD=HELP
TCPA_INFO_KEYWORD=INFO
COMPLIANCE_WEBHOOK_URL=wss://your-domain.com/ws/compliance-updates

# ==============================================================================
# CORS & API
# ==============================================================================
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,https://your-domain.com
API_V1_PREFIX=/api/v1
API_TITLE=MyHibachi API
API_VERSION=1.0.0

# ==============================================================================
# MONITORING & LOGGING
# ==============================================================================
SENTRY_DSN=your_sentry_dsn_here
LOG_LEVEL=INFO
ENVIRONMENT=production

# ==============================================================================
# AI & EXTERNAL SERVICES
# ==============================================================================
OPENAI_API_KEY=your_openai_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# ==============================================================================
# PAYMENT PROCESSING
# ==============================================================================
STRIPE_SECRET_KEY=sk_test_your_stripe_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# ==============================================================================
# DEVELOPMENT MODE
# ==============================================================================
DEV_MODE=false
DEBUG=false
TESTING=false
```

---

## Frontend Environment Variables

Create `.env.local` in `apps/admin/`:

```bash
# ==============================================================================
# API CONNECTION
# ==============================================================================
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# ==============================================================================
# WEBSOCKET ENDPOINTS
# ==============================================================================
NEXT_PUBLIC_ESCALATION_WS_URL=ws://localhost:8000/api/v1/ws/escalations
NEXT_PUBLIC_COMPLIANCE_WS_URL=ws://localhost:8000/ws/compliance-updates

# ==============================================================================
# STRIPE (Client-side)
# ==============================================================================
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here

# ==============================================================================
# FEATURE FLAGS
# ==============================================================================
NEXT_PUBLIC_ENABLE_VOICE_AI=true
NEXT_PUBLIC_ENABLE_SMS_TRACKING=true
NEXT_PUBLIC_ENABLE_COMPLIANCE_DASHBOARD=true

# ==============================================================================
# ENVIRONMENT
# ==============================================================================
NEXT_PUBLIC_ENVIRONMENT=development
NEXT_PUBLIC_APP_VERSION=1.0.0
```

---

## RingCentral Setup

### 1. Create RingCentral Developer Account

1. Go to https://developers.ringcentral.com
2. Sign up or log in
3. Create a new app in the developer portal

### 2. App Configuration

- **App Type**: Server-only (No UI)
- **Platform Type**: REST API
- **Permissions Required**:
  - `SMS` - Send and receive SMS
  - `ReadMessages` - Read message store
  - `WebhookSubscriptions` - Create webhooks

### 3. Get Credentials

After creating the app:

```bash
# Client Credentials
RINGCENTRAL_CLIENT_ID=<from app settings>
RINGCENTRAL_CLIENT_SECRET=<from app settings>

# JWT Token (for server-to-server auth)
RINGCENTRAL_JWT_TOKEN=<generate from app settings>
```

### 4. Webhook Setup

Configure webhook for SMS delivery status:

```bash
# Webhook URL (must be HTTPS in production)
RINGCENTRAL_WEBHOOK_URL=https://your-domain.com/api/v1/webhooks/sms/delivery

# Event Filters
- instant-message-event
- message-delivery-status
```

### 5. Phone Number Setup

1. Purchase a phone number in RingCentral
2. Enable SMS on the number
3. Add number to env:

```bash
RINGCENTRAL_PHONE_NUMBER=+1234567890
```

### 6. Test Connection

```bash
cd apps/backend
python -c "
from integrations.ringcentral_service import RingCentralService
import asyncio

async def test():
    service = RingCentralService()
    result = await service.send_sms('+1234567890', 'Test message')
    print(f'✅ SMS sent: {result}')

asyncio.run(test())
"
```

---

## IONOS SMTP Setup

### 1. IONOS Email Account

1. Log in to IONOS Control Panel
2. Go to **Email & Office** → **Email Settings**
3. Create or select email account

### 2. SMTP Credentials

```bash
# SMTP Server
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587  # Use 587 for TLS, 465 for SSL

# Authentication
SMTP_USER=noreply@your-domain.com
SMTP_PASSWORD=<your_email_password>
```

### 3. DNS Configuration

Verify SPF, DKIM, and DMARC records:

```dns
# SPF Record
TXT @ "v=spf1 include:_spf.ionos.com ~all"

# DMARC Record
TXT _dmarc "v=DMARC1; p=quarantine; rua=mailto:dmarc@your-domain.com"
```

### 4. Test Email

```bash
cd apps/backend
python -c "
from services.email.providers.ionos import IONOSEmailProvider
import asyncio

async def test():
    provider = IONOSEmailProvider()
    result = await provider.send_email(
        to_email='test@example.com',
        subject='Test Email',
        body='This is a test',
        html_body='<p>This is a test</p>'
    )
    print(f'✅ Email sent: {result}')

asyncio.run(test())
"
```

---

## Database Configuration

### PostgreSQL Setup

```bash
# Install PostgreSQL
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql@15

# Windows
# Download from https://www.postgresql.org/download/windows/
```

### Create Database

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE myhibachi;

-- Create user
CREATE USER myhibachi_user WITH PASSWORD 'secure_password_here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE myhibachi TO myhibachi_user;

-- Enable UUID extension
\c myhibachi
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search
```

### Run Migrations

```bash
cd apps/backend

# Run all migrations
alembic upgrade head

# Verify migrations
alembic current

# Rollback if needed
alembic downgrade -1
```

---

## Security & Compliance

### Generate Secure Keys

```bash
# SECRET_KEY (256-bit)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# FIELD_ENCRYPTION_KEY (Fernet key)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

### TCPA Compliance Checklist

- ✅ SMS consent recorded in database (`Subscriber.sms_consent`)
- ✅ Opt-out keywords processed (STOP, UNSUBSCRIBE, etc.)
- ✅ Delivery tracking enabled
- ✅ Audit trail for all SMS sends
- ✅ Unsubscribe link in emails (CAN-SPAM)
- ✅ Company address in email footers

### CAN-SPAM Compliance

```bash
# Required fields
COMPANY_NAME="MyHibachi Inc."
COMPANY_ADDRESS="123 Main St, City, ST 12345"
UNSUBSCRIBE_URL="https://your-domain.com/unsubscribe"
```

---

## Development vs Production

### Development (.env.development)

```bash
DATABASE_URL=postgresql://localhost:5432/myhibachi_dev
RINGCENTRAL_SERVER_URL=https://platform.devtest.ringcentral.com
DEBUG=true
DEV_MODE=true
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Production (.env.production)

```bash
DATABASE_URL=postgresql://prod-user:secure-pass@prod-db.example.com:5432/myhibachi
RINGCENTRAL_SERVER_URL=https://platform.ringcentral.com
DEBUG=false
DEV_MODE=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://your-domain.com,https://admin.your-domain.com
SENTRY_DSN=<production_sentry_dsn>
```

### Staging (.env.staging)

```bash
DATABASE_URL=postgresql://staging-user:pass@staging-db.example.com:5432/myhibachi_staging
RINGCENTRAL_SERVER_URL=https://platform.ringcentral.com
DEBUG=false
DEV_MODE=true
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=https://staging.your-domain.com
```

---

## Health Checks

After configuration, verify all services:

```bash
# Backend health
curl http://localhost:8000/api/v1/health/detailed

# Expected response
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "ringcentral": "ok",
    "smtp": "ok"
  }
}
```

---

## Troubleshooting

### RingCentral Connection Issues

```bash
# Check credentials
python -c "from integrations.ringcentral_service import RingCentralService; print(RingCentralService().test_connection())"

# Common issues:
- Invalid JWT token → Regenerate in developer portal
- Webhook not receiving events → Check HTTPS and firewall
- Rate limits → Check RingCentral dashboard for quota
```

### SMTP Connection Issues

```bash
# Test SMTP connection
python -c "
import smtplib
smtp = smtplib.SMTP('smtp.ionos.com', 587)
smtp.starttls()
smtp.login('user', 'pass')
print('✅ SMTP connected')
"

# Common issues:
- Port blocked → Check firewall rules
- Invalid credentials → Reset password in IONOS
- TLS errors → Use port 587 with STARTTLS
```

### Database Connection Issues

```bash
# Test database
psql postgresql://user:pass@localhost:5432/myhibachi

# Common issues:
- Connection refused → Check PostgreSQL is running
- Authentication failed → Verify pg_hba.conf settings
- SSL required → Add sslmode=require to DATABASE_URL
```

---

## Production Deployment Checklist

- [ ] All environment variables set
- [ ] Database migrations run
- [ ] RingCentral webhook URL configured (HTTPS)
- [ ] IONOS SPF/DKIM/DMARC records verified
- [ ] SSL certificates installed
- [ ] Sentry monitoring configured
- [ ] Redis connection pool tested
- [ ] Celery workers running
- [ ] Health check endpoints accessible
- [ ] CORS origins restricted to production domains
- [ ] Secrets rotated and secured in vault
- [ ] Backup strategy implemented
- [ ] Monitoring dashboards configured

---

## Support

For issues or questions:

- **RingCentral**: https://developers.ringcentral.com/support
- **IONOS**: https://www.ionos.com/help
- **Internal**: Contact DevOps team

---

**Last Updated**: November 2025 **Version**: 1.0.0
