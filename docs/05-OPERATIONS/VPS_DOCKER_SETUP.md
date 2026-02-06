# VPS Docker Setup Guide

**Last Updated:** 2025-01-31 **VPS Provider:** IONOS VPS Linux M
**Control Panel:** Plesk Obsidian **Status:** Reference Guide

---

## Overview

This guide covers Docker setup on the My Hibachi VPS for containerized
deployment alongside the existing Apache httpd reverse proxy managed
by Plesk.

### Current Infrastructure

| Component          | Details                            |
| ------------------ | ---------------------------------- |
| **VPS IP**         | 108.175.12.154                     |
| **Plesk URL**      | https://108.175.12.154:8443        |
| **Web Server**     | Apache httpd (RHEL/CentOS style)   |
| **Config Path**    | `/etc/httpd/conf.d/`               |
| **Production API** | Port 8000 (4 workers)              |
| **Staging API**    | Port 8002 (2 workers)              |
| **PostgreSQL**     | localhost:5432 (NOT containerized) |
| **Redis**          | localhost:6379 (NOT containerized) |
| **SSL**            | Cloudflare (frontend only)         |

---

## Prerequisites

### SSH Access

```bash
# Connect to VPS
ssh root@108.175.12.154

# Or with key file
ssh -i ~/.ssh/myhibachi_vps root@108.175.12.154
```

### Verify Current Setup

```bash
# Check systemd services
systemctl status myhibachi-backend.service
systemctl status myhibachi-staging.service

# Check ports in use
ss -tlnp | grep -E "8000|8002"

# Check Apache config
ls -la /etc/httpd/conf.d/ | grep myhibachi
```

---

## Part 1: Docker Installation on Plesk VPS

### Step 1: Install Docker Engine

```bash
# Update system packages
yum update -y

# Install required dependencies
yum install -y yum-utils device-mapper-persistent-data lvm2

# Add Docker repository
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Install Docker
yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start Docker service
systemctl start docker
systemctl enable docker

# Verify installation
docker --version
docker compose version
```

### Step 2: Configure Docker for Plesk Coexistence

```bash
# Create Docker daemon config
cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true,
  "userland-proxy": false
}
EOF

# Restart Docker to apply config
systemctl restart docker
```

### Step 3: Configure Firewall for Docker

```bash
# Check current firewall status
firewall-cmd --state

# If running, add Docker ports (internal only - Apache proxies)
firewall-cmd --permanent --zone=public --add-port=8000/tcp
firewall-cmd --permanent --zone=public --add-port=8002/tcp
firewall-cmd --reload

# Verify ports are open
firewall-cmd --list-ports
```

---

## Part 2: Apache httpd Reverse Proxy Configuration

### Current Apache Config Structure

```
/etc/httpd/conf.d/
├── myhibachi-api-apache.conf      # Production proxy to :8000
├── myhibachi-staging-apache.conf  # Staging proxy to :8002
└── ssl.conf                       # SSL settings (if any)
```

### Production VirtualHost

```apache
# /etc/httpd/conf.d/myhibachi-api-apache.conf

<VirtualHost *:80>
    ServerName mhapi.mysticdatanode.net
    ServerAdmin webmaster@mysticdatanode.net

    # Proxy to backend (Docker or systemd)
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    # Timeout settings
    ProxyTimeout 300
    ProxyBadHeader Ignore

    # Headers
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Real-IP %{REMOTE_ADDR}s

    # Logging
    ErrorLog /var/log/httpd/myhibachi-api-error.log
    CustomLog /var/log/httpd/myhibachi-api-access.log combined
</VirtualHost>
```

### Staging VirtualHost

```apache
# /etc/httpd/conf.d/myhibachi-staging-apache.conf

<VirtualHost *:80>
    ServerName staging-api.mysticdatanode.net
    ServerAdmin webmaster@mysticdatanode.net

    # Proxy to staging backend
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8002/
    ProxyPassReverse / http://127.0.0.1:8002/

    ProxyTimeout 300
    RequestHeader set X-Forwarded-Proto "https"

    ErrorLog /var/log/httpd/myhibachi-staging-error.log
    CustomLog /var/log/httpd/myhibachi-staging-access.log combined
</VirtualHost>
```

### Apply Apache Changes

```bash
# Test configuration
httpd -t

# If syntax OK, reload
systemctl reload httpd

# Check status
systemctl status httpd
```

---

## Part 3: Docker Compose Deployment

### Deploy Files

Copy these files to the VPS:

```bash
# Local machine
scp configs/docker-compose.vps.yml root@108.175.12.154:/opt/myhibachi/
scp configs/.env.vps.example root@108.175.12.154:/opt/myhibachi/.env.production

# On VPS, create directory structure
mkdir -p /opt/myhibachi/logs
cd /opt/myhibachi
```

### Configure Environment

```bash
# Edit .env.production with actual secrets
vi /opt/myhibachi/.env.production

# Key variables to set:
# - DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/myhibachi_production
# - DATABASE_URL_SYNC=postgresql+psycopg2://user:pass@localhost:5432/myhibachi_production
# - REDIS_URL=redis://localhost:6379/0
# - GCP_PROJECT_ID=my-hibachi-crm
```

### Start Docker Services

```bash
# Navigate to docker directory
cd /opt/myhibachi

# Pull/build images (first time)
docker compose -f docker-compose.vps.yml pull

# Start services
docker compose -f docker-compose.vps.yml up -d

# Check status
docker compose -f docker-compose.vps.yml ps
docker compose -f docker-compose.vps.yml logs --tail=50
```

### Verify Services

```bash
# Check production API
curl -s http://localhost:8000/health | jq .

# Check staging API
curl -s http://localhost:8002/health | jq .

# Check external access
curl -s https://mhapi.mysticdatanode.net/health | jq .
```

---

## Part 4: Plesk Panel Integration

### Accessing Plesk

1. Open browser: **https://108.175.12.154:8443**
2. Login with admin credentials
3. Navigate to **Domains > mysticdatanode.net**

### Docker Extension (Optional)

If Plesk Docker extension is installed:

1. Go to **Extensions > Docker**
2. You can view running containers
3. **Note:** We manage Docker via CLI for better control

### Monitoring via Plesk

1. **Server Management > Services**
   - Verify Docker service is running

2. **Logs > Apache Logs**
   - View reverse proxy logs

3. **Server Health**
   - Monitor CPU/memory usage

### SSL Certificates

SSL is handled by Cloudflare, but if needed:

1. **Websites & Domains > Let's Encrypt**
2. Issue certificate for API subdomain
3. Update Apache config for HTTPS

---

## Part 5: Operational Commands

### Docker Management

```bash
# View all containers
docker ps -a

# View logs (follow mode)
docker compose -f docker-compose.vps.yml logs -f myhibachi-api-prod

# Restart a service
docker compose -f docker-compose.vps.yml restart myhibachi-api-prod

# Stop all services
docker compose -f docker-compose.vps.yml down

# Update and restart
docker compose -f docker-compose.vps.yml pull
docker compose -f docker-compose.vps.yml up -d
```

### Health Checks

```bash
# Container health
docker inspect --format='{{.State.Health.Status}}' myhibachi-api-prod

# API health endpoints
curl http://localhost:8000/health
curl http://localhost:8002/health

# Database connectivity (from container)
docker exec myhibachi-api-prod python -c "from db.session import engine; print('DB OK')"
```

### Log Access

```bash
# Docker container logs
docker logs myhibachi-api-prod --tail=100
docker logs myhibachi-api-staging --tail=100

# Apache reverse proxy logs
tail -f /var/log/httpd/myhibachi-api-error.log
tail -f /var/log/httpd/myhibachi-api-access.log

# Application logs (if volume mounted)
tail -f /opt/myhibachi/logs/app.log
```

---

## Part 6: Troubleshooting

### Container Won't Start

```bash
# Check container logs
docker logs myhibachi-api-prod

# Check if port is in use (by systemd service)
ss -tlnp | grep 8000

# If systemd is still running, stop it first
systemctl stop myhibachi-backend.service
systemctl disable myhibachi-backend.service
```

### Database Connection Failed

```bash
# Verify PostgreSQL is running
systemctl status postgresql

# Check connection from host
psql -U myhibachi_user -d myhibachi_production -c "SELECT 1"

# For Docker, ensure host.docker.internal resolves
# In docker-compose, we use "host.docker.internal:host-gateway"
```

### Port Conflicts

```bash
# Find what's using a port
ss -tlnp | grep :8000
lsof -i :8000

# Kill conflicting process (carefully!)
kill -9 <PID>
```

### Apache Proxy Issues

```bash
# Test Apache config
httpd -t

# Check mod_proxy is loaded
httpd -M | grep proxy

# Enable proxy modules if missing
# In /etc/httpd/conf.modules.d/00-proxy.conf
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_http_module modules/mod_proxy_http.so
```

### Reset Docker State

```bash
# Stop everything
docker compose -f docker-compose.vps.yml down

# Remove all containers (careful!)
docker container prune -f

# Remove unused images
docker image prune -f

# Start fresh
docker compose -f docker-compose.vps.yml up -d
```

---

## Part 7: Migration Checklist

### Pre-Migration

- [ ] Backup database: `pg_dump myhibachi_production > backup.sql`
- [ ] Document current systemd config
- [ ] Test Docker locally if possible
- [ ] Schedule maintenance window
- [ ] Notify team of downtime window

### Migration Steps

1. [ ] Stop systemd services
2. [ ] Disable systemd services (prevent auto-start)
3. [ ] Start Docker containers
4. [ ] Verify health endpoints
5. [ ] Test API functionality
6. [ ] Monitor logs for errors
7. [ ] Update monitoring/alerts

### Post-Migration

- [ ] Verify all endpoints respond correctly
- [ ] Check payment processing (test booking)
- [ ] Verify database writes work
- [ ] Set up Docker auto-restart on boot
- [ ] Update runbooks/documentation

### Rollback Plan

If issues occur:

```bash
# Stop Docker
docker compose -f docker-compose.vps.yml down

# Re-enable systemd
systemctl enable myhibachi-backend.service
systemctl start myhibachi-backend.service

# Verify rollback
curl http://localhost:8000/health
```

---

## Quick Reference

### Key Paths

| Item           | Path                                    |
| -------------- | --------------------------------------- |
| Docker Compose | `/opt/myhibachi/docker-compose.vps.yml` |
| Environment    | `/opt/myhibachi/.env.production`        |
| Logs           | `/opt/myhibachi/logs/`                  |
| Apache Config  | `/etc/httpd/conf.d/myhibachi-*.conf`    |
| PostgreSQL     | `localhost:5432`                        |
| Redis          | `localhost:6379`                        |

### Key Commands

```bash
# Start/stop
docker compose -f docker-compose.vps.yml up -d
docker compose -f docker-compose.vps.yml down

# Logs
docker compose -f docker-compose.vps.yml logs -f

# Health
curl http://localhost:8000/health

# Apache reload
systemctl reload httpd
```

### Emergency Contacts

- **VPS Issues:** IONOS Support
- **Plesk Issues:** Plesk Support
- **Application Issues:** cs@myhibachichef.com

---

## Related Documentation

- [MANUAL_PAYMENT_HANDLING.md](./MANUAL_PAYMENT_HANDLING.md) - Payment
  reconciliation
- [VPS_DEPLOYMENT_GUIDE.md](../../VPS_DEPLOYMENT_GUIDE.md) - Original
  systemd setup
- [migrate-to-docker.sh](../../scripts/migrate-to-docker.sh) -
  Migration automation
- [docker-compose.vps.yml](../../configs/docker-compose.vps.yml) -
  Docker Compose file
