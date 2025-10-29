# My Hibachi VPS Deployment Guide

## Overview

This guide covers the complete deployment process for the My Hibachi application stack on a production VPS using Docker Compose and systemd services.

## Infrastructure Requirements

### Minimum Server Specifications
- **CPU**: 2 cores (4 recommended)
- **RAM**: 4GB (8GB recommended)
- **Storage**: 50GB SSD (100GB recommended)
- **OS**: Ubuntu 22.04 LTS or newer
- **Network**: Static IP with SSL certificate

### Required Ports
- **80/443**: HTTP/HTTPS (Nginx)
- **8000**: FastAPI Backend (internal)
- **8001**: AI Backend (internal)  
- **3000**: Frontend (internal)
- **5432**: PostgreSQL (internal)
- **6379**: Redis (internal)
- **22**: SSH (secure configuration)

## Pre-Deployment Setup

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    docker.io \
    docker-compose-v2 \
    nginx \
    postgresql-client \
    redis-tools \
    python3 \
    python3-pip \
    python3-venv \
    git \
    htop \
    ufw \
    fail2ban \
    certbot \
    python3-certbot-nginx

# Enable and start Docker
sudo systemctl enable docker
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
```

### 2. Security Configuration

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Configure fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Disable root login and password authentication
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

### 3. Create Application User

```bash
# Create myhibachi user
sudo useradd -m -s /bin/bash myhibachi
sudo usermod -aG docker myhibachi

# Create directory structure
sudo mkdir -p /opt/myhibachi/{config,logs,data,backups}
sudo chown -R myhibachi:myhibachi /opt/myhibachi

# Create backup directories
sudo mkdir -p /var/backups/myhibachi
sudo mkdir -p /var/log/myhibachi
sudo mkdir -p /var/lib/myhibachi/monitoring
sudo chown myhibachi:myhibachi /var/backups/myhibachi
sudo chown myhibachi:myhibachi /var/log/myhibachi
sudo chown myhibachi:myhibachi /var/lib/myhibachi/monitoring
```

## Application Deployment

### 1. Clone Repository

```bash
# Switch to myhibachi user
sudo su - myhibachi

# Clone repository
cd /opt/myhibachi
git clone <your-repo-url> app
cd app
```

### 2. Environment Configuration

```bash
# Copy environment templates
cp myhibachi-backend-fastapi/.env.example /opt/myhibachi/config/.env

# Edit environment variables
nano /opt/myhibachi/config/.env
```

**Required Environment Variables:**
```env
# Database
DATABASE_URL=postgresql://<username>:<password>@postgres:5432/myhibachi
REDIS_URL=redis://redis:6379/0

# Security
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]

# Email (SMTP)
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
EMAIL_FROM=your-email@gmail.com

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Features
ENABLE_ADMIN_API=true
ENABLE_ANALYTICS=true
ENABLE_NEWSLETTER=true

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=100

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=INFO
```

### 3. SSL Certificate Setup

```bash
# Install SSL certificate with Certbot
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

### 4. Deploy with Docker Compose

```bash
# Start services
cd /opt/myhibachi/app
docker compose -f docker-compose.prod.yml up -d

# Verify services are running
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
```

### 5. Database Setup

```bash
# Run database migrations
docker compose -f docker-compose.prod.yml exec fastapi-backend alembic upgrade head

# Create admin user (optional)
docker compose -f docker-compose.prod.yml exec fastapi-backend python -c "
from app.auth import create_admin_user
create_admin_user('admin@yourdomain.com', 'secure_admin_password')
"
```

## Systemd Services Setup

### 1. Install Service Files

```bash
# Copy systemd service files
sudo cp ops/systemd/*.service /etc/systemd/system/
sudo cp ops/systemd/*.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload
```

### 2. Enable Services

```bash
# Enable and start services
sudo systemctl enable myhibachi-health-monitor.service
sudo systemctl start myhibachi-health-monitor.service

# Enable backup timer
sudo systemctl enable myhibachi-backup.timer
sudo systemctl start myhibachi-backup.timer

# Check service status
sudo systemctl status myhibachi-health-monitor
sudo systemctl status myhibachi-backup.timer
```

## Monitoring and Maintenance

### 1. Health Monitoring

```bash
# Check system health
python3 ops/system_health_monitor.py --once

# View health monitor logs
sudo journalctl -u myhibachi-health-monitor -f

# Check health data
ls -la /var/lib/myhibachi/monitoring/
```

### 2. Database Backups

```bash
# Manual backup
python3 ops/backup_db.py

# Verify backups
ls -la /var/backups/myhibachi/

# Test backup restore
python3 ops/backup_db.py --verify-only /var/backups/myhibachi/latest_backup.sql.gz
```

### 3. Log Management

```bash
# View application logs
docker compose -f docker-compose.prod.yml logs -f fastapi-backend
docker compose -f docker-compose.prod.yml logs -f myhibachi-frontend

# View system logs
sudo journalctl -u myhibachi-health-monitor
sudo journalctl -u myhibachi-backup

# Log rotation (configure logrotate)
sudo nano /etc/logrotate.d/myhibachi
```

## Scaling and Performance

### 1. Horizontal Scaling

```bash
# Scale backend workers
docker compose -f docker-compose.prod.yml up -d --scale fastapi-backend=3

# Scale frontend instances
docker compose -f docker-compose.prod.yml up -d --scale myhibachi-frontend=2
```

### 2. Resource Monitoring

```bash
# Monitor container resources
docker stats

# Monitor system resources
htop
df -h
free -h
```

### 3. Database Optimization

```bash
# Connect to database
docker compose -f docker-compose.prod.yml exec postgres psql -U myhibachi -d myhibachi

# Analyze queries
EXPLAIN ANALYZE SELECT * FROM bookings WHERE created_at > NOW() - INTERVAL '30 days';

# Vacuum and analyze
VACUUM ANALYZE;
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   # Check logs
   docker compose -f docker-compose.prod.yml logs service-name
   
   # Check systemd status
   sudo systemctl status myhibachi-backend
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connection
   docker compose -f docker-compose.prod.yml exec postgres pg_isready
   
   # Check environment variables
   docker compose -f docker-compose.prod.yml exec fastapi-backend env | grep DATABASE
   ```

3. **SSL Certificate Issues**
   ```bash
   # Check certificate status
   sudo certbot certificates
   
   # Renew certificate
   sudo certbot renew
   ```

4. **High Memory Usage**
   ```bash
   # Check memory usage by service
   docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
   
   # Restart services if needed
   docker compose -f docker-compose.prod.yml restart
   ```

### Emergency Procedures

1. **Service Outage**
   ```bash
   # Quick restart all services
   cd /opt/myhibachi/app
   docker compose -f docker-compose.prod.yml restart
   
   # Check health
   python3 ops/system_health_monitor.py --once
   ```

2. **Database Corruption**
   ```bash
   # Stop application
   docker compose -f docker-compose.prod.yml stop
   
   # Restore from backup
   # (See backup restore procedures)
   
   # Start application
   docker compose -f docker-compose.prod.yml start
   ```

## Maintenance Schedule

### Daily
- Automated database backups (via systemd timer)
- Health monitoring (continuous via systemd service)
- Log rotation

### Weekly
- Review system metrics and alerts
- Check disk space and cleanup old logs
- Verify backup integrity

### Monthly
- Update system packages
- Review and rotate secrets
- Performance optimization review
- Security audit

### Quarterly
- Full system backup
- Disaster recovery testing
- Dependencies update
- Security assessment

## Security Checklist

### Server Security
- [ ] SSH key-based authentication only
- [ ] Firewall configured (UFW)
- [ ] Fail2ban enabled
- [ ] Regular security updates
- [ ] SSL certificates valid and auto-renewing

### Application Security
- [ ] Environment variables secured
- [ ] Database credentials rotated
- [ ] JWT secrets are strong and rotated
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Input validation implemented

### Monitoring Security
- [ ] Health monitoring active
- [ ] Log aggregation configured
- [ ] Alerting system functional
- [ ] Backup verification automated
- [ ] Incident response plan documented

## Contact and Support

For deployment issues or questions:
- Check logs first: `docker compose logs`
- Review health status: `python3 ops/system_health_monitor.py --once`
- Check documentation in `docs/operations/`
- Contact system administrator