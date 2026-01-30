# =============================================================================

# Docker Guide for My Hibachi

# =============================================================================

# Complete guide to understanding and using Docker for local development,

# staging, and production environments.

# =============================================================================

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [Understanding Docker](#-understanding-docker)
3. [Project Structure](#-project-structure)
4. [Daily Workflows](#-daily-workflows)
5. [Environment Guide](#-environment-guide)
6. [VS Code Docker Extension](#-vs-code-docker-extension)
7. [Docker Desktop Tips](#-docker-desktop-tips)
8. [Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start

### First Time Setup

```powershell
# 1. Open Docker Desktop (make sure it's running!)

# 2. Navigate to project root
cd "c:\Users\surya\projects\MH webapps"

# 3. Copy environment file
cp .env.docker.example .env

# 4. Edit .env with your actual values (use VS Code)
code .env

# 5. Start development environment
docker compose --profile development up -d

# 6. Check everything is running
docker compose ps
```

### Access Points (Development)

| Service        | URL                        | Description                     |
| -------------- | -------------------------- | ------------------------------- |
| **API**        | http://localhost:8000      | FastAPI Backend                 |
| **API Docs**   | http://localhost:8000/docs | Swagger UI                      |
| **PgAdmin**    | http://localhost:5050      | Database admin                  |
| **Prometheus** | http://localhost:9090      | Metrics (monitoring profile)    |
| **Grafana**    | http://localhost:3001      | Dashboards (monitoring profile) |

---

## 🐳 Understanding Docker

### What is Docker?

Think of Docker as **"shipping containers for software"**:

- **Without Docker**: "Works on my machine" problem
- **With Docker**: Same environment everywhere (dev, staging, prod)

### Key Concepts

| Concept       | Real-World Analogy  | What It Does                            |
| ------------- | ------------------- | --------------------------------------- |
| **Image**     | Recipe/Blueprint    | Defines what software to install        |
| **Container** | Running instance    | Actual running application              |
| **Volume**    | USB drive           | Saves data even if container is deleted |
| **Network**   | Private LAN         | Lets containers talk to each other      |
| **Compose**   | Orchestra conductor | Manages multiple containers together    |

### Our Docker Files

```
MH webapps/
├── Dockerfile                 # Recipe to build images (API, Admin, Customer)
├── docker-compose.yml         # Development environment (all services)
├── docker-compose.staging.yml # Staging API (connects to VPS database)
├── docker-compose.prod.yml    # Production API (VPS deployment)
├── .dockerignore              # Files to exclude from images
├── .env.docker.example        # Environment template for Docker
└── docker/
    └── nginx.local.conf       # Local nginx configuration
```

---

## 📁 Project Structure

### docker-compose.yml (Development)

```yaml
# Uses "profiles" to group services:

# --profile development  →  API + PostgreSQL + Redis + PgAdmin
# --profile production   →  API + PostgreSQL + Redis + Nginx
# --profile monitoring   →  Prometheus + Grafana
```

### How Profiles Work

```powershell
# Start development services only
docker compose --profile development up -d

# Start monitoring too
docker compose --profile development --profile monitoring up -d

# Start everything
docker compose --profile development --profile monitoring up -d
```

---

## 🔄 Daily Workflows

### Morning Startup

```powershell
# Make sure Docker Desktop is running, then:
docker compose --profile development up -d

# Verify services are healthy
docker compose ps
```

### After Code Changes (Backend)

```powershell
# Rebuild and restart API only
docker compose --profile development up -d --build unified-backend
```

### View Logs

```powershell
# All services
docker compose logs -f

# Just the API
docker compose logs -f unified-backend

# Last 100 lines
docker compose logs --tail=100 unified-backend
```

### Stop Everything

```powershell
# Stop but keep data
docker compose --profile development down

# Stop and DELETE data (fresh start)
docker compose --profile development down -v
```

### Clean Up Docker

```powershell
# Remove unused images (saves disk space)
docker image prune -a

# Remove everything unused (containers, images, networks)
docker system prune -a
```

---

## 🌍 Environment Guide

### Development (Your Machine)

```powershell
# Full stack with containerized database
docker compose --profile development up -d
```

**Use when**: Daily development, testing features locally

### Staging (VPS - Port 8002)

```powershell
# Build and deploy staging API
docker compose -f docker-compose.staging.yml up -d
```

**Use when**: Testing before production, QA

**Note**: Connects to VPS PostgreSQL (not containerized)

### Production (VPS - Port 8000)

```powershell
# Deploy production API
docker compose -f docker-compose.prod.yml up -d
```

**Use when**: Serving real customers

**Important**: Database is on VPS (not in Docker) for data safety!

---

## 🔌 VS Code Docker Extension

### Installation

1. Open VS Code
2. Press `Ctrl+Shift+X` (Extensions)
3. Search "Docker"
4. Install "Docker" by Microsoft

### Features You'll Love

| Feature            | How to Access                          | What It Does               |
| ------------------ | -------------------------------------- | -------------------------- |
| **Container List** | Left sidebar → Docker icon             | See all running containers |
| **Logs**           | Right-click container → "View Logs"    | Live log streaming         |
| **Shell**          | Right-click container → "Attach Shell" | Terminal inside container  |
| **Start/Stop**     | Right-click container                  | Quick controls             |
| **Inspect**        | Right-click → "Inspect"                | See container config       |
| **Compose**        | Right-click docker-compose.yml         | Start/stop entire stack    |

### Pro Tips

1. **Quick Actions**: Right-click any container for common actions
2. **IntelliSense**: Get autocomplete in Dockerfile and
   docker-compose.yml
3. **Image Browser**: Explore Docker Hub images directly
4. **Prune**: Right-click "Images" → "Prune" to clean up

---

## 🖥️ Docker Desktop Tips

### Dashboard Overview

When you open Docker Desktop:

- **Containers**: Shows all running/stopped containers
- **Images**: Shows downloaded images
- **Volumes**: Shows persistent data storage

### Useful Settings

1. **Resources** → **Memory**: Allocate 4-8 GB for smooth operation
2. **Resources** → **CPUs**: 2-4 CPUs recommended
3. **Docker Engine**: Advanced settings (usually not needed)

### Monitoring Container Health

1. Click on a container name
2. See **Logs**, **Stats** (CPU/Memory), **Inspect**
3. Green dot = healthy, Red = unhealthy

---

## 🔧 Troubleshooting

### Container Won't Start

```powershell
# Check logs for errors
docker compose logs unified-backend

# Common fixes:
# 1. Check .env file exists and has correct values
# 2. Make sure ports aren't already in use
# 3. Rebuild the image
docker compose --profile development up -d --build
```

### "Port already in use"

```powershell
# Find what's using the port (e.g., 8000)
netstat -ano | findstr :8000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

### Database Connection Error

```powershell
# Check if postgres container is running
docker compose ps postgres

# Check postgres logs
docker compose logs postgres

# Connect to postgres directly
docker compose exec postgres psql -U postgres -d myhibachi
```

### "No space left on device"

```powershell
# Clean up Docker
docker system prune -a --volumes

# Or in Docker Desktop: Settings → Resources → Disk → "Purge data"
```

### Container keeps restarting

```powershell
# Check logs for crash reason
docker compose logs --tail=100 unified-backend

# Common causes:
# 1. Missing environment variable
# 2. Database connection failed
# 3. Syntax error in code
```

---

## 📊 Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    YOUR DEVELOPMENT ENVIRONMENT                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Docker Desktop (Windows)                                              │
│   ├── myhibachi-backend     (FastAPI)       → localhost:8000            │
│   ├── myhibachi-postgres    (PostgreSQL)    → localhost:5432            │
│   ├── myhibachi-redis       (Redis)         → localhost:6379            │
│   ├── myhibachi-pgadmin     (PgAdmin)       → localhost:5050            │
│   ├── myhibachi-prometheus  (Metrics)       → localhost:9090            │
│   └── myhibachi-grafana     (Dashboards)    → localhost:3001            │
│                                                                          │
│   Local Node.js (not Docker - faster hot reload)                        │
│   ├── Customer App                          → localhost:3000            │
│   └── Admin App                             → localhost:3001            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    VPS PRODUCTION ENVIRONMENT                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Docker (Production)                                                   │
│   ├── myhibachi-production-api  → Port 8000                             │
│   └── myhibachi-production-redis                                        │
│                                                                          │
│   Docker (Staging)                                                      │
│   ├── myhibachi-staging-api     → Port 8002                             │
│   └── myhibachi-staging-redis                                           │
│                                                                          │
│   Native Services (NOT in Docker - for data safety)                     │
│   ├── PostgreSQL (myhibachi_production)                                 │
│   ├── PostgreSQL (myhibachi_staging)                                    │
│   └── Cloudflare Tunnel                                                 │
│                                                                          │
│   Vercel (Frontend - automatic deployment)                              │
│   ├── myhibachichef.com (main branch)                                   │
│   ├── admin.myhibachichef.com (main branch)                             │
│   ├── staging.myhibachichef.com (dev branch)                            │
│   └── admin-staging.mysticdatanode.net (dev branch)                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Best Practices

### Do ✅

- Always use `.env` files (never hardcode secrets)
- Use named volumes for data you want to keep
- Use health checks in production
- Clean up unused images regularly
- Use Docker Desktop's stats to monitor resource usage

### Don't ❌

- Don't put production database in Docker (data safety risk)
- Don't expose database ports to the internet
- Don't store secrets in Dockerfile
- Don't ignore .dockerignore (it speeds up builds)
- Don't skip health checks in production

---

## 📚 Commands Reference

### Essential Commands

| Command                                 | Description                    |
| --------------------------------------- | ------------------------------ |
| `docker compose up -d`                  | Start containers in background |
| `docker compose down`                   | Stop containers                |
| `docker compose ps`                     | List running containers        |
| `docker compose logs -f`                | Stream logs                    |
| `docker compose exec <service> sh`      | Shell into container           |
| `docker compose --profile <name> up -d` | Start specific profile         |

### Build Commands

| Command                                  | Description                     |
| ---------------------------------------- | ------------------------------- |
| `docker compose build`                   | Build all images                |
| `docker compose build --no-cache`        | Rebuild from scratch            |
| `docker compose up -d --build <service>` | Rebuild and restart one service |

### Cleanup Commands

| Command                  | Description            |
| ------------------------ | ---------------------- |
| `docker system prune -a` | Remove all unused data |
| `docker volume prune`    | Remove unused volumes  |
| `docker image prune -a`  | Remove unused images   |

---

Need help? Check the logs first: `docker compose logs -f`
