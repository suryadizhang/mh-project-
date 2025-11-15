# Staging Deployment Guide

Guide for deploying the MyHibachi application to staging environment
for integration testing.

## 📋 Prerequisites

Before deploying to staging:

- [x] All ESLint warnings fixed
- [x] Tests passing (24/24)
- [x] Environment variables documented
- [x] Admin training guide created
- [x] Code pushed to `nuclear-refactor-clean-architecture` branch

---

## 🚀 Deployment Steps

### 1. Prepare Staging Environment

#### A. Server Setup

```bash
# SSH into staging server
ssh admin@staging.myhibachi.com

# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install required software
sudo apt-get install -y \
    postgresql-15 \
    redis-server \
    nginx \
    python3.11 \
    python3-pip \
    python3-venv \
    nodejs \
    npm

# Install PM2 for process management
sudo npm install -g pm2
```

#### B. Create Staging Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create staging database
CREATE DATABASE myhibachi_staging;
CREATE USER myhibachi_staging WITH PASSWORD 'SECURE_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE myhibachi_staging TO myhibachi_staging;

# Enable extensions
\c myhibachi_staging
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\q
```

#### C. Configure Redis

```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Set password
requirepass SECURE_REDIS_PASSWORD_HERE

# Restart Redis
sudo systemctl restart redis
```

### 2. Clone and Setup Application

```bash
# Create application directory
sudo mkdir -p /var/www/myhibachi-staging
sudo chown -R $USER:$USER /var/www/myhibachi-staging
cd /var/www/myhibachi-staging

# Clone repository
git clone https://github.com/suryadizhang/mh-project-.git .
git checkout nuclear-refactor-clean-architecture

# Create environment files from documentation
cp ENVIRONMENT_CONFIGURATION.md .env.staging.template
```

### 3. Backend Setup

```bash
cd apps/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
nano .env
```

**Backend .env for Staging:**

```bash
# Database
DATABASE_URL=postgresql://myhibachi_staging:SECURE_PASSWORD@localhost:5432/myhibachi_staging
DATABASE_POOL_SIZE=10

# Redis
REDIS_URL=redis://:SECURE_REDIS_PASSWORD@localhost:6379/0
CELERY_BROKER_URL=redis://:SECURE_REDIS_PASSWORD@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:SECURE_REDIS_PASSWORD@localhost:6379/2

# RingCentral (Production credentials, staging webhook)
RINGCENTRAL_CLIENT_ID=your_client_id
RINGCENTRAL_CLIENT_SECRET=your_client_secret
RINGCENTRAL_JWT_TOKEN=your_jwt_token
RINGCENTRAL_SERVER_URL=https://platform.ringcentral.com
RINGCENTRAL_PHONE_NUMBER=+1234567890
RINGCENTRAL_WEBHOOK_URL=https://staging.myhibachi.com/api/v1/webhooks/sms/delivery

# IONOS SMTP
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USER=staging@myhibachi.com
SMTP_PASSWORD=your_smtp_password
SMTP_FROM_EMAIL=staging@myhibachi.com

# Security
SECRET_KEY=<generate_with_secrets.token_urlsafe(32)>
FIELD_ENCRYPTION_KEY=<generate_with_Fernet.generate_key()>
JWT_SECRET_KEY=<generate_with_secrets.token_hex(32)>

# Compliance
TCPA_CONSENT_REQUIRED=true
COMPANY_NAME=MyHibachi Inc.
COMPANY_ADDRESS=123 Main St, City, ST 12345
UNSUBSCRIBE_URL=https://staging.myhibachi.com/unsubscribe

# CORS
ALLOWED_ORIGINS=https://staging.myhibachi.com,https://admin-staging.myhibachi.com

# Environment
ENVIRONMENT=staging
DEBUG=false
DEV_MODE=true
LOG_LEVEL=INFO

# Monitoring
SENTRY_DSN=<staging_sentry_dsn>
```

**Run Migrations:**

```bash
# Apply all migrations
alembic upgrade head

# Verify
alembic current
```

### 4. Frontend Setup

```bash
cd /var/www/myhibachi-staging/apps/admin

# Install dependencies
npm install

# Create .env.local
nano .env.local
```

**Frontend .env.local for Staging:**

```bash
NEXT_PUBLIC_API_URL=https://staging.myhibachi.com
NEXT_PUBLIC_WS_URL=wss://staging.myhibachi.com
NEXT_PUBLIC_ESCALATION_WS_URL=wss://staging.myhibachi.com/api/v1/ws/escalations
NEXT_PUBLIC_COMPLIANCE_WS_URL=wss://staging.myhibachi.com/ws/compliance-updates
NEXT_PUBLIC_ENVIRONMENT=staging
NEXT_PUBLIC_ENABLE_SMS_TRACKING=true
NEXT_PUBLIC_ENABLE_COMPLIANCE_DASHBOARD=true
```

**Build Frontend:**

```bash
npm run build

# Verify build
ls -la .next/
```

### 5. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/myhibachi-staging
```

**Nginx Configuration:**

```nginx
# Backend API
server {
    listen 80;
    listen [::]:80;
    server_name staging.myhibachi.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name staging.myhibachi.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/staging.myhibachi.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.myhibachi.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API proxy
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket proxy
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}

# Admin Dashboard
server {
    listen 80;
    listen [::]:80;
    server_name admin-staging.myhibachi.com;

    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name admin-staging.myhibachi.com;

    ssl_certificate /etc/letsencrypt/live/admin-staging.myhibachi.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin-staging.myhibachi.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    root /var/www/myhibachi-staging/apps/admin/.next;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /_next/static {
        alias /var/www/myhibachi-staging/apps/admin/.next/static;
        expires 1y;
        access_log off;
    }
}
```

**Enable site:**

```bash
# Enable configuration
sudo ln -s /etc/nginx/sites-available/myhibachi-staging /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 6. SSL Certificates

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificates
sudo certbot --nginx -d staging.myhibachi.com -d admin-staging.myhibachi.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 7. Start Services with PM2

**Backend (FastAPI):**

```bash
cd /var/www/myhibachi-staging/apps/backend

# Create PM2 ecosystem file
nano ecosystem.config.js
```

```javascript
module.exports = {
  apps: [
    {
      name: 'myhibachi-api-staging',
      script: 'venv/bin/uvicorn',
      args: 'src.main:app --host 0.0.0.0 --port 8000 --workers 4',
      cwd: '/var/www/myhibachi-staging/apps/backend',
      env: {
        ENVIRONMENT: 'staging',
      },
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: '/var/log/myhibachi/api-error.log',
      out_file: '/var/log/myhibachi/api-out.log',
      time: true,
    },
    {
      name: 'myhibachi-celery-worker-staging',
      script: 'venv/bin/celery',
      args: '-A src.workers.celery_config worker --loglevel=info',
      cwd: '/var/www/myhibachi-staging/apps/backend',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      max_memory_restart: '512M',
      error_file: '/var/log/myhibachi/celery-error.log',
      out_file: '/var/log/myhibachi/celery-out.log',
    },
    {
      name: 'myhibachi-celery-beat-staging',
      script: 'venv/bin/celery',
      args: '-A src.workers.celery_config beat --loglevel=info',
      cwd: '/var/www/myhibachi-staging/apps/backend',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      error_file: '/var/log/myhibachi/beat-error.log',
      out_file: '/var/log/myhibachi/beat-out.log',
    },
  ],
};
```

```bash
# Create log directory
sudo mkdir -p /var/log/myhibachi
sudo chown -R $USER:$USER /var/log/myhibachi

# Start services
pm2 start ecosystem.config.js

# Save PM2 config
pm2 save

# Setup PM2 startup
pm2 startup
# Run the command it outputs
```

**Frontend (Next.js):**

```bash
cd /var/www/myhibachi-staging/apps/admin

# Start with PM2
pm2 start npm --name "myhibachi-admin-staging" -- start -- -p 3000

# Save
pm2 save
```

### 8. Verify Deployment

```bash
# Check PM2 processes
pm2 list

# Should show:
# myhibachi-api-staging         online
# myhibachi-celery-worker-staging   online
# myhibachi-celery-beat-staging     online
# myhibachi-admin-staging       online

# Check logs
pm2 logs myhibachi-api-staging --lines 50

# Test backend health
curl https://staging.myhibachi.com/api/v1/health/detailed

# Expected response:
# {
#   "status": "healthy",
#   "checks": {
#     "database": "ok",
#     "redis": "ok",
#     "ringcentral": "ok",
#     "smtp": "ok"
#   }
# }

# Test frontend
curl -I https://admin-staging.myhibachi.com
# Expected: HTTP 200
```

---

## 🧪 Integration Testing

### 1. Smoke Tests

**Backend API:**

```bash
# Health check
curl https://staging.myhibachi.com/health

# API documentation
open https://staging.myhibachi.com/docs

# Auth endpoint
curl -X POST https://staging.myhibachi.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

**Frontend:**

1. Open https://admin-staging.myhibachi.com
2. Log in with admin credentials
3. Verify dashboard loads
4. Check real-time updates (WebSocket connection status)

### 2. SMS Tracking Test

```bash
# Create test campaign
curl -X POST https://staging.myhibachi.com/api/admin/newsletter/campaigns \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Staging Test Campaign",
    "message": "Test SMS from staging. Reply STOP to opt-out.",
    "channel": "sms",
    "recipient_ids": [1, 2, 3]
  }'

# Monitor in admin dashboard:
# 1. Go to Newsletter → Campaigns
# 2. Watch real-time sending progress
# 3. Verify delivery statuses update
# 4. Check cost calculation
```

### 3. Compliance Test

```bash
# Test TCPA consent check
curl https://staging.myhibachi.com/api/admin/newsletter/subscribers/1 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Verify response includes:
# - sms_consent: true/false
# - sms_consent_date: timestamp
# - sms_consent_ip: IP address

# Test opt-out (send "STOP" SMS to RingCentral number)
# Monitor in admin dashboard:
# 1. Go to Newsletter → Compliance
# 2. Verify subscriber marked inactive
# 3. Check opt-out appears in recent activity
```

### 4. WebSocket Test

Open browser console on admin dashboard:

```javascript
// Check WebSocket connections
const escalationWs = new WebSocket(
  'wss://staging.myhibachi.com/api/v1/ws/escalations'
);
escalationWs.onopen = () => console.log('✅ Escalation WS connected');
escalationWs.onerror = e =>
  console.error('❌ Escalation WS error:', e);

const complianceWs = new WebSocket(
  'wss://staging.myhibachi.com/ws/compliance-updates'
);
complianceWs.onopen = () => console.log('✅ Compliance WS connected');
complianceWs.onerror = e =>
  console.error('❌ Compliance WS error:', e);
```

### 5. Load Testing

```bash
# Install locust
pip install locust

# Create load test script
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class DashboardUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        # Login
        response = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "password"
        })
        self.token = response.json()["access_token"]

    @task(3)
    def view_analytics(self):
        self.client.get("/api/admin/newsletter/analytics",
                       headers={"Authorization": f"Bearer {self.token}"})

    @task(2)
    def view_campaigns(self):
        self.client.get("/api/admin/newsletter/campaigns",
                       headers={"Authorization": f"Bearer {self.token}"})

    @task(1)
    def view_subscribers(self):
        self.client.get("/api/admin/newsletter/subscribers",
                       headers={"Authorization": f"Bearer {self.token}"})
EOF

# Run load test (10 users, 2 users/second spawn rate)
locust -f locustfile.py --host=https://staging.myhibachi.com --users 10 --spawn-rate 2 --run-time 5m --headless
```

---

## 📊 Monitoring

### 1. Setup Monitoring

**Install monitoring tools:**

```bash
# Prometheus
sudo apt-get install -y prometheus

# Grafana
sudo apt-get install -y grafana

# Start services
sudo systemctl start prometheus grafana-server
sudo systemctl enable prometheus grafana-server
```

**Configure Prometheus:**

```yaml
# /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'myhibachi-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'myhibachi-celery'
    static_configs:
      - targets: ['localhost:5555'] # Flower
```

### 2. Application Metrics

Monitor these key metrics:

**API Performance:**

- Request latency (p50, p95, p99)
- Requests per second
- Error rate
- Active connections

**SMS Delivery:**

- Messages sent/hour
- Delivery rate (%)
- Failed deliveries
- Cost per hour

**Compliance:**

- Consent rate
- Opt-out rate
- Compliance violations

**System Resources:**

- CPU usage
- Memory usage
- Database connections
- Redis operations/sec

### 3. Log Aggregation

```bash
# Install Loki (for log aggregation)
sudo apt-get install -y loki promtail

# Configure Promtail to tail application logs
# /etc/promtail/config.yml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  - job_name: myhibachi
    static_configs:
      - targets:
          - localhost
        labels:
          job: myhibachi-logs
          __path__: /var/log/myhibachi/*.log
```

### 4. Alerts

Configure Alertmanager for critical alerts:

```yaml
# /etc/alertmanager/alertmanager.yml
route:
  receiver: 'email'
  group_by: ['alertname']

receivers:
  - name: 'email'
    email_configs:
      - to: 'devops@myhibachi.com'
        from: 'alerts@myhibachi.com'
        smarthost: smtp.ionos.com:587
        auth_username: 'alerts@myhibachi.com'
        auth_password: 'password'

# Alert rules
groups:
  - name: myhibachi
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: 'High error rate detected'

      - alert: LowDeliveryRate
        expr: (sms_delivered / sms_sent) < 0.95
        for: 10m
        annotations:
          summary: 'SMS delivery rate below 95%'
```

---

## 🔄 Update Deployment

When code changes:

```bash
# SSH into staging
ssh admin@staging.myhibachi.com
cd /var/www/myhibachi-staging

# Pull latest code
git fetch origin
git checkout nuclear-refactor-clean-architecture
git pull origin nuclear-refactor-clean-architecture

# Backend updates
cd apps/backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Frontend updates
cd ../admin
npm install
npm run build

# Restart services
pm2 restart all

# Verify
pm2 list
curl https://staging.myhibachi.com/health
```

---

## 🐛 Troubleshooting

### Issue: Services Won't Start

```bash
# Check PM2 logs
pm2 logs --lines 100

# Check system logs
sudo journalctl -u nginx -f

# Check database connectivity
psql postgresql://myhibachi_staging:password@localhost:5432/myhibachi_staging

# Check Redis
redis-cli -a SECURE_REDIS_PASSWORD ping
```

### Issue: WebSocket Connection Fails

```bash
# Check Nginx WebSocket config
sudo nginx -t

# Test WebSocket directly
wscat -c wss://staging.myhibachi.com/ws/compliance-updates

# Check firewall
sudo ufw status
```

### Issue: SMS Not Sending

```bash
# Check Celery worker
pm2 logs myhibachi-celery-worker-staging

# Check RingCentral credentials
curl -X POST https://staging.myhibachi.com/api/admin/test/ringcentral-connection \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check webhook URL in RingCentral dashboard
```

---

## ✅ Deployment Checklist

- [ ] Server provisioned and secured
- [ ] PostgreSQL database created and migrated
- [ ] Redis configured with password
- [ ] SSL certificates installed
- [ ] Nginx configured and running
- [ ] Backend services started with PM2
- [ ] Frontend built and deployed
- [ ] RingCentral webhook URL updated
- [ ] IONOS SMTP credentials verified
- [ ] Environment variables set correctly
- [ ] Health checks passing
- [ ] Smoke tests completed
- [ ] WebSocket connections working
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Load testing performed
- [ ] Documentation updated
- [ ] Team notified

---

## 📞 Support

**Deployment Issues:**

- DevOps Team: devops@myhibachi.com
- Slack: #deployments

**Staging Access:**

- Backend API: https://staging.myhibachi.com
- Admin Dashboard: https://admin-staging.myhibachi.com
- API Docs: https://staging.myhibachi.com/docs
- Monitoring: https://monitoring.myhibachi.com

---

**Last Updated**: November 2025 **Version**: 1.0.0
