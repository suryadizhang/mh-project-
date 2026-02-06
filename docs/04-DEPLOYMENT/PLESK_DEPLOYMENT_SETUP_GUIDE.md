# 🚀 Plesk VPS Deployment Setup Guide

## Overview

This guide will help you set up your My Hibachi backend on a
Plesk-managed VPS for production deployment with CI/CD automation.

---

## Prerequisites

- ✅ VPS with Plesk Panel installed
- ✅ Domain configured (e.g., `mhapi.mysticdatanode.net`)
- ✅ SSH access to VPS
- ✅ PostgreSQL database created
- ✅ Redis installed (optional, for rate limiting)
- ✅ SSL certificate (Let's Encrypt via Plesk)

---

## Part 1: Plesk Panel Setup

### Step 1: Create Domain/Subdomain

1. **Login to Plesk** → `Websites & Domains`
2. **Click** "Add Domain" or "Add Subdomain"
3. **Configure**:
   - Domain: `mhapi.mysticdatanode.net`
   - Document root: `/httpdocs/backend`
   - Enable SSL/TLS (Let's Encrypt)

### Step 2: Create Database

1. **Go to** `Databases` → `Add Database`
2. **Configure**:
   ```
   Database name: myhibachi_prod
   Database user: myhibachi_user
   Password: <generate-strong-password>
   ```
3. **Save** credentials securely

### Step 3: Install Python

1. **Go to** `Languages` → `Python`
2. **Enable** Python 3.11 (or latest 3.x)
3. **Ensure** `pip` and `virtualenv` are available

### Step 4: Configure Application

1. **Go to** `Hosting Settings` for `mhapi.mysticdatanode.net`
2. **Set** Application Root: `/httpdocs/backend`
3. **Enable** "Python application"
4. **Configure**:
   ```
   Python version: 3.11
   Application startup file: run_backend.py
   Application root: /httpdocs/backend
   Application URL: https://mhapi.mysticdatanode.net
   ```

### Step 5: Install Redis (Optional but Recommended)

**Via SSH**:

```bash
# Login to VPS
ssh user@your-vps-ip

# Install Redis
sudo apt update
sudo apt install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Verify
redis-cli ping
# Should return: PONG
```

**Alternative**: Use Plesk Redis extension if available

---

## Part 2: SSH & Security Setup

### Step 1: Generate SSH Key for Deployment

**On your local machine**:

```powershell
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/myhibachi_deploy

# View public key
cat ~/.ssh/myhibachi_deploy.pub
```

### Step 2: Add SSH Key to VPS

**Option A: Via Plesk Panel**

1. Go to `Websites & Domains` → `Web Hosting Access`
2. Enable SSH access
3. Add your SSH public key

**Option B: Via SSH**

```bash
# Login to VPS
ssh user@your-vps-ip

# Add public key
mkdir -p ~/.ssh
echo "your-public-key-here" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### Step 3: Test SSH Connection

```powershell
# Test connection
ssh -i ~/.ssh/myhibachi_deploy user@your-vps-ip

# Should login without password prompt
```

---

## Part 3: Initial Backend Deployment

### Step 1: Create Directory Structure

**On VPS via SSH**:

```bash
# Navigate to web root
cd /var/www/vhosts/myhibachi.com/httpdocs

# Create backend directory
mkdir -p backend
cd backend

# Create necessary directories
mkdir -p logs backups src

# Set permissions
chown -R your-user:psacln .
chmod -R 755 .
```

### Step 2: Create Python Virtual Environment

```bash
cd /var/www/vhosts/myhibachi.com/httpdocs/backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install basic dependencies
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary
```

### Step 3: Create Environment File

```bash
cd /var/www/vhosts/myhibachi.com/httpdocs/backend

# Create .env file
cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://myhibachi_user:your-password@localhost/myhibachi_prod

# Redis (if installed)
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Environment
ENVIRONMENT=production
DEBUG=false

# API Settings
API_VERSION=1.0.0
API_BASE_URL=https://mhapi.mysticdatanode.net

# CORS Origins
CORS_ORIGINS=https://myhibachichef.com,https://www.myhibachichef.com,https://admin.mysticdatanode.net

# Twilio
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=your-twilio-phone-number

# Stripe
STRIPE_SECRET_KEY=sk_live_your-stripe-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Sentry (optional)
SENTRY_DSN=your-sentry-dsn-here

# Rate Limiting
RATE_LIMIT_ENABLED=true
EOF

# Secure the file
chmod 600 .env
```

### Step 4: Upload Backend Code (Manual First Deploy)

**From your local machine**:

```powershell
cd "c:\Users\surya\projects\MH webapps\apps\backend"

# Create deployment package
tar -czf backend-initial.tar.gz src/ requirements.txt alembic.ini alembic/ run_backend.py

# Upload to VPS
scp backend-initial.tar.gz user@your-vps-ip:/var/www/vhosts/myhibachi.com/httpdocs/backend/

# SSH into VPS
ssh user@your-vps-ip

# Extract files
cd /var/www/vhosts/myhibachi.com/httpdocs/backend
tar -xzf backend-initial.tar.gz
rm backend-initial.tar.gz

# Install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations
cd src
alembic upgrade head
```

### Step 5: Configure Supervisor (Process Manager)

Plesk uses **Passenger** by default, but for better control, use
**Supervisor**.

**Create supervisor config**:

```bash
sudo nano /etc/supervisor/conf.d/myhibachi-backend.conf
```

**Add configuration**:

```ini
[program:myhibachi-backend]
directory=/var/www/vhosts/myhibachi.com/httpdocs/backend
command=/var/www/vhosts/myhibachi.com/httpdocs/backend/venv/bin/python run_backend.py
user=your-user
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/www/vhosts/myhibachi.com/httpdocs/backend/logs/app.log
environment=PATH="/var/www/vhosts/myhibachi.com/httpdocs/backend/venv/bin"
```

**Start the service**:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start myhibachi-backend
sudo supervisorctl status myhibachi-backend
```

### Step 6: Configure Nginx Reverse Proxy

Plesk uses Nginx by default. Configure it to proxy to your FastAPI
app.

**Via Plesk Panel**:

1. Go to `Websites & Domains` → `mhapi.mysticdatanode.net`
2. Click `Apache & nginx Settings`
3. **Add to "Additional nginx directives"**:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # WebSocket support (if needed)
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}

# Health check endpoint (no auth required)
location /health {
    proxy_pass http://127.0.0.1:8000/health;
}
```

4. **Click** "OK" to apply

### Step 7: Verify Deployment

**Check service status**:

```bash
sudo supervisorctl status myhibachi-backend
```

**Test locally on VPS**:

```bash
curl http://localhost:8000/health
```

**Test externally**:

```bash
curl https://mhapi.mysticdatanode.net/health
```

**Expected response**:

```json
{
  "status": "healthy",
  "service": "unified-api",
  "version": "1.0.0",
  "environment": "production"
}
```

---

## Part 4: GitHub Actions Setup

### Step 1: Add GitHub Secrets

1. **Go to** your GitHub repository
2. **Navigate to** `Settings` → `Secrets and variables` → `Actions`
3. **Add the following secrets**:

```
VPS_SSH_KEY          = (paste contents of ~/.ssh/myhibachi_deploy private key)
VPS_HOST             = your-vps-ip-address
VPS_USER             = your-ssh-username
```

**Example**:

```
VPS_SSH_KEY:
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAACmFlczI1Ni1jdHIAAAAGYmNyeXB0AAAAGAAAABDxX...
... (full private key content)
-----END OPENSSH PRIVATE KEY-----

VPS_HOST: 123.456.789.012
VPS_USER: myhibachi_deploy
```

### Step 2: Create Production Environment

1. **Go to** `Settings` → `Environments`
2. **Click** "New environment"
3. **Name**: `production`
4. **Add protection rules** (optional):
   - ✅ Required reviewers (1 person)
   - ✅ Wait timer (0 minutes)
5. **Save**

### Step 3: Test CI/CD Pipeline

**Trigger deployment**:

```powershell
# Make a small change to backend code
cd "c:\Users\surya\projects\MH webapps\apps\backend"

# Add a comment or update version
# ... make change ...

# Commit and push
git add .
git commit -m "test: trigger CI/CD pipeline"
git push origin main
```

**Monitor deployment**:

1. Go to GitHub → `Actions` tab
2. Watch the workflow run
3. Check each step for success ✅

**Expected workflow**:

```
🧪 Run Tests          → ✅ Passed (30s)
🏗️ Build & Validate   → ✅ Passed (20s)
🚀 Deploy to VPS      → ✅ Deployed (45s)
🏥 Health Check       → ✅ Healthy (10s)
```

---

## Part 5: Monitoring & Maintenance

### Database Backups

**Create backup script**:

```bash
sudo nano /usr/local/bin/backup-myhibachi.sh
```

**Add**:

```bash
#!/bin/bash
BACKUP_DIR="/var/www/vhosts/myhibachi.com/httpdocs/backend/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
pg_dump -U myhibachi_user myhibachi_prod > "$BACKUP_DIR/db_$DATE.sql"

# Compress
gzip "$BACKUP_DIR/db_$DATE.sql"

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_$DATE.sql.gz"
```

**Make executable and schedule**:

```bash
sudo chmod +x /usr/local/bin/backup-myhibachi.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-myhibachi.sh") | crontab -
```

### Log Rotation

**Create logrotate config**:

```bash
sudo nano /etc/logrotate.d/myhibachi-backend
```

**Add**:

```
/var/www/vhosts/myhibachi.com/httpdocs/backend/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 your-user psacln
    sharedscripts
    postrotate
        supervisorctl restart myhibachi-backend > /dev/null
    endscript
}
```

### Monitoring Health Checks

**Create health check cron**:

```bash
# Add to crontab (every 5 minutes)
*/5 * * * * curl -f https://mhapi.mysticdatanode.net/health || echo "Backend health check failed" | mail -s "My Hibachi Backend Alert" your-email@example.com
```

---

## Part 6: Rollback Procedure

### Automatic Rollback (Via CI/CD)

If health checks fail after deployment, the CI/CD pipeline will
automatically rollback.

### Manual Rollback

**If you need to manually rollback**:

```bash
# SSH into VPS
ssh user@your-vps-ip

cd /var/www/vhosts/myhibachi.com/httpdocs/backend

# List available backups
ls -lt backups/

# Restore from backup (example: backup_20251030_143022)
rm -rf src
cp -r backups/backup_20251030_143022/src .

# Restart service
sudo supervisorctl restart myhibachi-backend

# Verify
curl http://localhost:8000/health
```

---

## Part 7: SSL Certificate Management

### Option 1: Let's Encrypt via Plesk (Recommended)

1. **Go to** `Websites & Domains` → `mhapi.mysticdatanode.net`
2. **Click** `SSL/TLS Certificates`
3. **Click** "Get it free" (Let's Encrypt)
4. **Enable** auto-renewal
5. **Secure** all subdomains

### Option 2: Manual Let's Encrypt

```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d mhapi.mysticdatanode.net

# Configure Plesk to use the certificate
# (See Plesk documentation for manual certificate import)
```

---

## Troubleshooting

### Issue: Backend not starting

**Check logs**:

```bash
sudo supervisorctl tail -f myhibachi-backend
# Or
tail -f /var/www/vhosts/myhibachi.com/httpdocs/backend/logs/app.log
```

**Check process**:

```bash
sudo supervisorctl status myhibachi-backend
```

**Restart service**:

```bash
sudo supervisorctl restart myhibachi-backend
```

### Issue: Database connection failed

**Check PostgreSQL**:

```bash
sudo systemctl status postgresql
```

**Test connection**:

```bash
psql -U myhibachi_user -d myhibachi_prod -h localhost
```

**Check DATABASE_URL in .env**

### Issue: 502 Bad Gateway

**Check if backend is running**:

```bash
curl http://localhost:8000/health
```

**Check Nginx configuration**:

```bash
sudo nginx -t
```

**Check Nginx logs**:

```bash
sudo tail -f /var/log/nginx/error.log
```

### Issue: CI/CD deployment fails

**Check SSH connection**:

```bash
ssh -i ~/.ssh/myhibachi_deploy user@your-vps-ip
```

**Check GitHub Actions logs**:

- Go to GitHub → Actions tab
- Click on failed workflow
- Review error messages

**Common issues**:

- SSH key not added correctly
- Wrong VPS_HOST or VPS_USER
- Permissions issue on VPS
- Supervisor not running

---

## Security Checklist

- [x] SSH key-based authentication (no password)
- [x] `.env` file permissions set to 600
- [x] SSL certificate installed and auto-renewing
- [x] Firewall configured (only ports 22, 80, 443 open)
- [x] Database user has limited privileges
- [x] Backups scheduled daily
- [x] Log rotation configured
- [x] Health checks monitoring
- [x] Rate limiting enabled
- [x] Security headers configured

---

## Quick Commands Reference

```bash
# Check backend status
sudo supervisorctl status myhibachi-backend

# Restart backend
sudo supervisorctl restart myhibachi-backend

# View logs (live)
sudo supervisorctl tail -f myhibachi-backend

# Run migrations
cd /var/www/vhosts/myhibachi.com/httpdocs/backend/src
source ../venv/bin/activate
alembic upgrade head

# Create database backup
/usr/local/bin/backup-myhibachi.sh

# Test health endpoint
curl https://mhapi.mysticdatanode.net/health

# Test from VPS
curl http://localhost:8000/health

# Check Redis
redis-cli ping

# Check database
psql -U myhibachi_user -d myhibachi_prod
```

---

## Next Steps

1. ✅ Complete Plesk setup (Steps 1-7)
2. ✅ Configure GitHub secrets
3. ✅ Test CI/CD pipeline
4. ✅ Set up monitoring and backups
5. ✅ Configure SSL certificate
6. ✅ Test rollback procedure
7. ✅ Document any custom configurations

---

**Setup Guide Version**: 1.0  
**Date**: October 30, 2025  
**Status**: Ready for Production Deployment 🚀
