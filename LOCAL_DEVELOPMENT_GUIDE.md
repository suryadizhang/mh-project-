# Local Development Guide - Windows PowerShell

Complete guide for running the MyHibachi system locally on Windows using PowerShell.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Database Setup](#database-setup)
- [Running Services](#running-services)
- [Testing Features](#testing-features)
- [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

Before starting, ensure you have installed:

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Node.js 20+** ([Download](https://nodejs.org/))
- **PostgreSQL 15+** ([Download](https://www.postgresql.org/download/windows/))
- **Redis** ([Download](https://redis.io/docs/getting-started/installation/install-redis-on-windows/))
- **Git** ([Download](https://git-scm.com/download/win))

---

## 🔧 Environment Setup

### 1. Clone the Repository

```powershell
cd C:\Users\surya\projects
git clone <repository-url> "MH webapps"
cd "MH webapps"
```

### 2. Set Up Python Virtual Environment

```powershell
# Navigate to backend directory
cd apps\backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt

# Return to root
cd ..\..
```

### 3. Install Node.js Dependencies

```powershell
# Install admin frontend dependencies
cd apps\admin
npm install
cd ..\..

# Install customer frontend dependencies
cd apps\customer
npm install
cd ..\..
```

### 4. Configure Environment Variables

Create `.env` file in `apps/backend`:

```powershell
# Navigate to backend
cd apps\backend

# Create .env file
@"
# Database
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/myhibachi_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=myhibachi_dev

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# RingCentral (SMS/Voice)
RINGCENTRAL_CLIENT_ID=your_client_id
RINGCENTRAL_CLIENT_SECRET=your_client_secret
RINGCENTRAL_SERVER_URL=https://platform.ringcentral.com
RINGCENTRAL_JWT_TOKEN=your_jwt_token
RINGCENTRAL_SMS_NUMBER=+1234567890

# JWT Secret
JWT_SECRET=your-secret-key-change-in-production

# API URLs
API_BASE_URL=http://localhost:8000
ADMIN_URL=http://localhost:3001
CUSTOMER_URL=http://localhost:3007

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
"@ | Out-File -FilePath .env -Encoding utf8

# Return to root
cd ..\..
```

Create `.env.local` file in `apps/admin`:

```powershell
cd apps\admin
@"
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_CHAT_API_URL=http://localhost:8002
"@ | Out-File -FilePath .env.local -Encoding utf8
cd ..\..
```

**Environment Variables Explained:**
- `NEXT_PUBLIC_API_URL`: Main backend API endpoint (FastAPI)
- `NEXT_PUBLIC_WS_URL`: WebSocket endpoint for real-time updates (compliance, escalations)
- `NEXT_PUBLIC_CHAT_API_URL`: Chat service API endpoint (separate microservice)

Create `.env.local` file in `apps/customer`:

```powershell
cd apps\customer
@"
NEXT_PUBLIC_API_URL=http://localhost:8000
"@ | Out-File -FilePath .env.local -Encoding utf8
cd ..\..
```

---

## 🗄️ Database Setup

### 1. Start PostgreSQL

```powershell
# Check if PostgreSQL service is running
Get-Service -Name postgresql*

# If not running, start it
Start-Service -Name "postgresql-x64-15"  # Adjust version number as needed
```

### 2. Create Database

```powershell
# Connect to PostgreSQL
psql -U postgres

# In psql terminal:
CREATE DATABASE myhibachi_dev;
\c myhibachi_dev
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
\q
```

### 3. Run Database Migrations

```powershell
# Navigate to backend
cd apps\backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run Alembic migrations
python -m alembic upgrade head

# Verify migrations
python -m alembic current

# Return to root
cd ..\..
```

---

## 🚀 Running Services

### Service Overview

| Service | Port | Purpose |
|---------|------|---------|
| Backend API | 8000 | FastAPI backend server |
| Admin Frontend | 3001 | Next.js admin dashboard |
| Customer Frontend | 3007 | Next.js customer portal |
| Redis | 6379 | Cache & message broker |
| Celery Worker | - | Background job processor |
| Celery Beat | - | Scheduled task scheduler |
| Flower | 5555 | Celery monitoring UI |

### Start All Services (Recommended for Development)

Open **5 separate PowerShell windows** and run each command:

#### Window 1: Backend API Server

```powershell
cd "C:\Users\surya\projects\MH webapps\apps\backend"
.\venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Test it:**
- Open browser: http://localhost:8000/docs
- You should see FastAPI Swagger documentation

#### Window 2: Redis Server

```powershell
redis-server
```

**Test it:**
```powershell
redis-cli ping
# Should return: PONG
```

#### Window 3: Celery Worker

```powershell
cd "C:\Users\surya\projects\MH webapps\apps\backend\src"
..\venv\Scripts\Activate.ps1
celery -A workers.celery_config:celery_app worker --loglevel=info -P solo
```

**Note:** Use `-P solo` on Windows to avoid multiprocessing issues.

**Test it:**
- Check console output for "celery@<hostname> ready"
- Should show registered tasks including:
  - `workers.campaign_metrics_tasks.update_active_campaign_metrics`
  - `workers.recording_tasks.cleanup_expired_recordings`
  - `monitoring.collect_metrics`

#### Window 4: Celery Beat (Scheduler)

```powershell
cd "C:\Users\surya\projects\MH webapps\apps\backend\src"
..\venv\Scripts\Activate.ps1
celery -A workers.celery_config:celery_app beat --loglevel=info
```

**Test it:**
- Check console output for "Scheduler: Starting..."
- Should show scheduled tasks like:
  - `update-active-campaign-metrics` (every 5 minutes)
  - `cleanup-completed-campaign-metrics` (every hour)

#### Window 5: Admin Frontend

```powershell
cd "C:\Users\surya\projects\MH webapps\apps\admin"
npm run dev
```

**Test it:**
- Open browser: http://localhost:3001
- Should see admin login page

#### Window 6 (Optional): Customer Frontend

```powershell
cd "C:\Users\surya\projects\MH webapps\apps\customer"
npm run dev
```

**Test it:**
- Open browser: http://localhost:3007
- Should see customer portal

#### Window 7 (Optional): Flower (Celery Monitor)

```powershell
cd "C:\Users\surya\projects\MH webapps\apps\backend\src"
..\venv\Scripts\Activate.ps1
celery -A workers.celery_config:celery_app flower --port=5555
```

**Test it:**
- Open browser: http://localhost:5555
- Username: `admin`
- Password: `admin123` (from `.env`)

---

## 🧪 Testing Features

### Test SMS Tracking System

#### 1. Create Test Subscriber

```powershell
# Using curl (install from https://curl.se/windows/)
curl -X POST "http://localhost:8000/api/newsletter/subscribers" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -d '{\"email\":\"test@example.com\",\"phone\":\"+15551234567\",\"sms_consent\":true,\"first_name\":\"Test\",\"last_name\":\"User\"}'
```

**Or use the Admin Dashboard:**
1. Go to http://localhost:3001
2. Login as admin
3. Navigate to Newsletter > Subscribers
4. Click "Add Subscriber"
5. Fill form and check "SMS Consent"

#### 2. Create SMS Campaign

**Via Admin Dashboard:**
1. Navigate to Newsletter > Campaigns
2. Click "New Campaign"
3. Select Channel: SMS
4. Enter campaign details
5. Save as Draft

#### 3. Send Test SMS

```powershell
# Using PowerShell Invoke-RestMethod
$headers = @{
    "Authorization" = "Bearer YOUR_TOKEN"
    "Content-Type" = "application/json"
}

$body = @{
    campaign_id = 1
    test_mode = $true
    test_phone = "+15551234567"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/newsletter/campaigns/1/send" `
  -Method POST `
  -Headers $headers `
  -Body $body
```

#### 4. Verify SMS Tracking

**Check Subscriber Metrics:**
```powershell
# Get subscriber details
Invoke-RestMethod -Uri "http://localhost:8000/api/newsletter/subscribers/1" `
  -Headers @{"Authorization" = "Bearer YOUR_TOKEN"}

# Should show:
# - total_sms_sent: 1
# - last_sms_sent_date: <timestamp>
```

**Check Delivery Events:**
```powershell
# Get delivery events for campaign
Invoke-RestMethod -Uri "http://localhost:8000/api/newsletter/campaigns/1/delivery-events" `
  -Headers @{"Authorization" = "Bearer YOUR_TOKEN"}

# Should show SMSDeliveryEvent with:
# - status: SENT
# - ringcentral_message_id: msg-xxx
# - cost_cents: 1
```

#### 5. Simulate RingCentral Webhook

```powershell
# Simulate delivery confirmation
$webhookPayload = @{
    messageId = "msg-xxx"  # Use actual message ID from step 4
    messageStatus = "Delivered"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/webhooks/ringcentral" `
  -Method POST `
  -Headers @{"Content-Type" = "application/json"} `
  -Body $webhookPayload
```

**Verify Update:**
```powershell
# Check subscriber metrics again
Invoke-RestMethod -Uri "http://localhost:8000/api/newsletter/subscribers/1" `
  -Headers @{"Authorization" = "Bearer YOUR_TOKEN"}

# Should now show:
# - total_sms_delivered: 1
# - last_sms_delivered_date: <timestamp>
```

#### 6. View Analytics Dashboard

1. Open http://localhost:3001/newsletter/analytics
2. Should see:
   - SMS Consented count
   - Total SMS Delivered
   - Delivery Rate percentage
   - Cost tracking
   - TCPA Compliance Score

#### 7. Check Compliance Widget

1. Add compliance widget to dashboard:
   ```tsx
   import { ComplianceWidget } from '@/components/newsletter/ComplianceWidget';
   
   // In your page:
   <ComplianceWidget />
   ```

2. Should display:
   - Overall compliance score (target: >95%)
   - SMS consent rate
   - Unsubscribe rate
   - Delivery success rate
   - Any compliance violations

### Test Campaign Metrics Worker

```powershell
# Manually trigger metrics update
Invoke-RestMethod -Uri "http://localhost:8000/api/admin/campaigns/1/refresh-metrics" `
  -Method POST `
  -Headers @{"Authorization" = "Bearer YOUR_TOKEN"}

# Check Celery Worker window - should see task execution:
# [INFO] Task workers.campaign_metrics_tasks.update_single_campaign_metrics[xxx] succeeded
```

**Or wait 5 minutes for automatic update via Celery Beat**

### Run Test Suite

```powershell
cd "C:\Users\surya\projects\MH webapps\apps\backend"
.\venv\Scripts\Activate.ps1

# Run all SMS tracking tests
pytest tests/test_sms_tracking_comprehensive.py -v

# Run with coverage report
pytest tests/test_sms_tracking_comprehensive.py --cov=. --cov-report=html

# View coverage report
Start-Process "htmlcov\index.html"
```

---

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use

```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill process (replace <PID> with actual process ID)
Stop-Process -Id <PID> -Force
```

#### Redis Connection Error

```powershell
# Check if Redis is running
Get-Process -Name redis-server -ErrorAction SilentlyContinue

# If not running, start Redis
redis-server

# Test connection
redis-cli ping
```

#### Database Connection Error

```powershell
# Check PostgreSQL service
Get-Service -Name postgresql*

# Restart PostgreSQL
Restart-Service -Name "postgresql-x64-15"

# Test connection
psql -U postgres -d myhibachi_dev -c "SELECT version();"
```

#### Celery Worker Not Processing Tasks

```powershell
# Check if Redis is accessible
redis-cli -h localhost -p 6379 ping

# Check Celery worker logs for errors
# Restart worker with verbose logging
celery -A workers.celery_config:celery_app worker --loglevel=debug -P solo
```

#### Migration Fails

```powershell
# Check current migration
cd apps\backend
.\venv\Scripts\Activate.ps1
python -m alembic current

# Check pending migrations
python -m alembic heads

# Downgrade one revision
python -m alembic downgrade -1

# Upgrade again
python -m alembic upgrade head
```

#### Module Import Errors

```powershell
# Ensure you're in the correct directory
cd "C:\Users\surya\projects\MH webapps\apps\backend\src"

# Ensure virtual environment is activated
..\venv\Scripts\Activate.ps1

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Reinstall dependencies
pip install -r ..\requirements.txt --force-reinstall
```

### Logs and Debugging

#### View Backend API Logs

```powershell
# API logs are in the terminal running uvicorn
# For file logging, check:
Get-Content "C:\Users\surya\projects\MH webapps\apps\backend\logs\app.log" -Tail 50 -Wait
```

#### View Celery Worker Logs

```powershell
# Worker logs are in the terminal running celery worker
# Or check:
Get-Content "C:\Users\surya\projects\MH webapps\apps\backend\logs\celery-worker.log" -Tail 50 -Wait
```

#### View Database Query Logs

```powershell
# Enable SQL logging in .env
# Add: SQLALCHEMY_ECHO=True

# Restart backend API
# SQL queries will appear in terminal
```

#### Monitor Redis

```powershell
# Connect to Redis CLI
redis-cli

# Monitor all commands in real-time
MONITOR

# List all keys
KEYS *

# Check memory usage
INFO memory

# Exit Redis CLI
EXIT
```

---

## 📊 Health Checks

### Quick System Health Check

```powershell
# Create health check script
@"
Write-Host \"=== MyHibachi System Health Check ===\" -ForegroundColor Cyan

# Check Backend API
try {
    `$api = Invoke-RestMethod -Uri \"http://localhost:8000/health\"
    Write-Host \"✅ Backend API: Running\" -ForegroundColor Green
} catch {
    Write-Host \"❌ Backend API: Down\" -ForegroundColor Red
}

# Check Admin Frontend
try {
    `$response = Invoke-WebRequest -Uri \"http://localhost:3001\" -TimeoutSec 2 -UseBasicParsing
    if (`$response.StatusCode -eq 200) {
        Write-Host \"✅ Admin Frontend: Running\" -ForegroundColor Green
    }
} catch {
    Write-Host \"❌ Admin Frontend: Down\" -ForegroundColor Red
}

# Check Redis
try {
    `$redis = redis-cli ping
    if (`$redis -eq \"PONG\") {
        Write-Host \"✅ Redis: Running\" -ForegroundColor Green
    }
} catch {
    Write-Host \"❌ Redis: Down\" -ForegroundColor Red
}

# Check PostgreSQL
try {
    `$pg = psql -U postgres -d myhibachi_dev -c \"SELECT 1;\" 2>`$null
    Write-Host \"✅ PostgreSQL: Running\" -ForegroundColor Green
} catch {
    Write-Host \"❌ PostgreSQL: Down\" -ForegroundColor Red
}

# Check Celery Worker (via Flower API)
try {
    `$flower = Invoke-RestMethod -Uri \"http://localhost:5555/api/workers\"
    if (`$flower) {
        Write-Host \"✅ Celery Worker: Running\" -ForegroundColor Green
    }
} catch {
    Write-Host \"⚠️  Celery Worker: Cannot verify (Flower might not be running)\" -ForegroundColor Yellow
}

Write-Host \"`n=== Health Check Complete ===\" -ForegroundColor Cyan
"@ | Out-File -FilePath health-check.ps1 -Encoding utf8

# Run health check
.\health-check.ps1
```

---

## 🌐 WebSocket Real-Time Updates

The application includes WebSocket endpoints for real-time updates:

### Compliance Updates WebSocket

**Endpoint:** `ws://localhost:8000/ws/compliance-updates?token=your_jwt_token`

**Events:**
- `connection_established`: Initial connection confirmation
- `compliance_update`: Triggered when:
  - New SMS sent
  - Delivery status changes
  - Subscriber metrics updated
  - Campaign metrics updated

**Client Messages:**
- `ping`: Keep connection alive

**Frontend Implementation:**
- `ComplianceWidget.tsx` automatically connects to WebSocket
- Falls back to manual refresh if WebSocket connection fails
- Uses `NEXT_PUBLIC_WS_URL` environment variable

**Testing WebSocket:**
```powershell
# Install websocat (WebSocket client)
# https://github.com/vi/websocat

# Connect to compliance updates (replace TOKEN with actual JWT)
websocat "ws://localhost:8000/ws/compliance-updates?token=TOKEN"

# Send ping
{ "type": "ping" }
```

### Escalation Updates WebSocket

**Endpoint:** `ws://localhost:8000/api/v1/ws/escalations?token=your_jwt_token`

**Events:**
- `escalation_created`: New escalation
- `escalation_updated`: Status/assignment changed
- `escalation_resolved`: Escalation resolved

---

## 🎯 Quick Start Script

Save this as `start-dev.ps1` in the project root:

```powershell
# Quick start script for all services
Write-Host "Starting MyHibachi Development Environment..." -ForegroundColor Cyan

# Start Redis
Start-Process powershell -ArgumentList "-NoExit", "-Command", "redis-server"
Start-Sleep -Seconds 2

# Start Backend API
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\surya\projects\MH webapps\apps\backend'; .\venv\Scripts\Activate.ps1; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
Start-Sleep -Seconds 3

# Start Celery Worker
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\surya\projects\MH webapps\apps\backend\src'; ..\venv\Scripts\Activate.ps1; celery -A workers.celery_config:celery_app worker --loglevel=info -P solo"
Start-Sleep -Seconds 2

# Start Celery Beat
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\surya\projects\MH webapps\apps\backend\src'; ..\venv\Scripts\Activate.ps1; celery -A workers.celery_config:celery_app beat --loglevel=info"
Start-Sleep -Seconds 2

# Start Admin Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\surya\projects\MH webapps\apps\admin'; npm run dev"

Write-Host "`nAll services started!" -ForegroundColor Green
Write-Host "Backend API: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "Admin Dashboard: http://localhost:3001" -ForegroundColor Yellow
Write-Host "WebSocket Compliance: ws://localhost:8000/ws/compliance-updates" -ForegroundColor Yellow
Write-Host "WebSocket Escalations: ws://localhost:8000/api/v1/ws/escalations" -ForegroundColor Yellow
```

**Run it:**
```powershell
.\start-dev.ps1
```

---

## 📝 Notes

- Always activate the Python virtual environment before running backend commands
- Use separate PowerShell windows for each service to see logs clearly
- Redis must be running before starting Celery workers
- Database must be migrated before starting the API server
- Check firewall settings if services can't connect to each other
- WebSocket connections require valid JWT authentication tokens
- All environment variables must be configured in `.env.local` files
- No secrets or credentials should be hardcoded - always use environment variables

---

## 🆘 Getting Help

If you encounter issues:

1. Check this guide's troubleshooting section
2. Review service logs in each PowerShell window
3. Run the health check script to identify which service is down
4. Check `.env` configuration files for correct values
5. Verify all prerequisites are installed and services are running

Happy developing! 🚀
