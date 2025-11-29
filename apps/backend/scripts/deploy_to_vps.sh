#!/bin/bash
# =============================================================================
# MyHibachi Backend VPS Deployment Script
# =============================================================================
# This script deploys the backend to a Plesk-managed VPS with:
# - PostgreSQL database
# - Redis cache
# - Google Secret Manager integration
# - Systemd services
# - Nginx load balancing
#
# Usage:
#   1. SSH into VPS: ssh root@your-vps-ip
#   2. Run: bash deploy_to_vps.sh
#
# Prerequisites:
#   - Plesk installed on VPS
#   - PostgreSQL installed (via Plesk)
#   - Redis installed
#   - Python 3.11+ installed
#   - Google Cloud SDK installed (for GSM)
# =============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# =============================================================================
# CONFIGURATION - EDIT THESE VALUES
# =============================================================================
DOMAIN="myhibachi.com"
VPS_USER="www-data"
BACKEND_DIR="/var/www/vhosts/${DOMAIN}/backend"
VENV_DIR="${BACKEND_DIR}/.venv"
REPO_URL="https://github.com/suryadizhang/mh-project-.git"
BRANCH="nuclear-refactor-clean-architecture"
GCP_PROJECT="my-hibachi-crm"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

# =============================================================================
# STEP 1: Check Prerequisites
# =============================================================================
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        error "Please run as root (sudo bash deploy_to_vps.sh)"
        exit 1
    fi

    # Check Python
    if ! command -v python3.11 &> /dev/null; then
        error "Python 3.11+ required. Install with: apt install python3.11 python3.11-venv"
        exit 1
    fi

    # Check PostgreSQL
    if ! systemctl is-active --quiet postgresql; then
        warn "PostgreSQL not running. Starting..."
        systemctl start postgresql
    fi
    log "✓ PostgreSQL running"

    # Check Redis
    if ! systemctl is-active --quiet redis-server; then
        warn "Redis not running. Installing/starting..."
        apt-get install -y redis-server
        systemctl enable redis-server
        systemctl start redis-server
    fi
    log "✓ Redis running"

    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        warn "Google Cloud SDK not installed. Installing..."
        curl https://sdk.cloud.google.com | bash
        exec -l $SHELL
    fi
    log "✓ Google Cloud SDK available"
}

# =============================================================================
# STEP 2: Setup Database
# =============================================================================
setup_database() {
    log "Setting up PostgreSQL database..."

    # Generate secure password
    DB_PASSWORD=$(openssl rand -hex 32)

    # Create database and user
    sudo -u postgres psql <<EOF
-- Create database user
CREATE USER myhibachi_user WITH PASSWORD '${DB_PASSWORD}';

-- Create database
CREATE DATABASE myhibachi_production OWNER myhibachi_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE myhibachi_production TO myhibachi_user;

-- Connect to database and create schemas
\c myhibachi_production

-- Create schemas
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS lead;
CREATE SCHEMA IF NOT EXISTS newsletter;
CREATE SCHEMA IF NOT EXISTS ai;

-- Grant schema privileges
GRANT ALL ON SCHEMA core, identity, lead, newsletter, ai TO myhibachi_user;
GRANT ALL ON ALL TABLES IN SCHEMA core, identity, lead, newsletter, ai TO myhibachi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT ALL ON TABLES TO myhibachi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA identity GRANT ALL ON TABLES TO myhibachi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA lead GRANT ALL ON TABLES TO myhibachi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA newsletter GRANT ALL ON TABLES TO myhibachi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA ai GRANT ALL ON TABLES TO myhibachi_user;
EOF

    # Build DATABASE_URL
    DATABASE_URL="postgresql://myhibachi_user:${DB_PASSWORD}@localhost:5432/myhibachi_production"

    log "✓ Database created: myhibachi_production"
    log "✓ User created: myhibachi_user"

    # Store in GSM
    log "Storing DATABASE_URL in Google Secret Manager..."
    echo -n "${DATABASE_URL}" | gcloud secrets create DATABASE_URL \
        --project="${GCP_PROJECT}" \
        --data-file=- \
        --replication-policy="automatic" 2>/dev/null || \
    echo -n "${DATABASE_URL}" | gcloud secrets versions add DATABASE_URL \
        --project="${GCP_PROJECT}" \
        --data-file=-

    log "✓ DATABASE_URL stored in GSM"
}

# =============================================================================
# STEP 3: Setup Redis
# =============================================================================
setup_redis() {
    log "Configuring Redis..."

    # Configure Redis for production
    cat > /etc/redis/redis.conf.d/myhibachi.conf <<EOF
# MyHibachi Redis Configuration
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
EOF

    systemctl restart redis-server

    # Store Redis URL in GSM
    REDIS_URL="redis://localhost:6379/0"

    log "Storing REDIS_URL in Google Secret Manager..."
    echo -n "${REDIS_URL}" | gcloud secrets create REDIS_URL \
        --project="${GCP_PROJECT}" \
        --data-file=- \
        --replication-policy="automatic" 2>/dev/null || \
    echo -n "${REDIS_URL}" | gcloud secrets versions add REDIS_URL \
        --project="${GCP_PROJECT}" \
        --data-file=-

    # Also create Celery URLs
    echo -n "${REDIS_URL}" | gcloud secrets versions add CELERY_BROKER_URL \
        --project="${GCP_PROJECT}" \
        --data-file=- 2>/dev/null || true
    echo -n "${REDIS_URL}" | gcloud secrets versions add CELERY_RESULT_BACKEND \
        --project="${GCP_PROJECT}" \
        --data-file=- 2>/dev/null || true

    log "✓ Redis configured and URLs stored in GSM"
}

# =============================================================================
# STEP 4: Clone/Update Repository
# =============================================================================
setup_code() {
    log "Setting up application code..."

    # Create directory structure
    mkdir -p "${BACKEND_DIR}"
    cd "${BACKEND_DIR}"

    if [ -d ".git" ]; then
        log "Updating existing repository..."
        git fetch origin
        git checkout "${BRANCH}"
        git pull origin "${BRANCH}"
    else
        log "Cloning repository..."
        git clone -b "${BRANCH}" "${REPO_URL}" .
    fi

    # Copy backend files to deployment location
    if [ -d "apps/backend" ]; then
        cp -r apps/backend/* .
    fi

    log "✓ Code deployed to ${BACKEND_DIR}"
}

# =============================================================================
# STEP 5: Setup Python Environment
# =============================================================================
setup_python() {
    log "Setting up Python virtual environment..."

    cd "${BACKEND_DIR}"

    # Create virtual environment
    python3.11 -m venv "${VENV_DIR}"

    # Activate and install dependencies
    source "${VENV_DIR}/bin/activate"
    pip install --upgrade pip wheel setuptools
    pip install -r requirements.txt

    # Install Google Cloud dependencies for GSM
    pip install google-cloud-secret-manager

    deactivate

    log "✓ Python environment ready"
}

# =============================================================================
# STEP 6: Create Production .env with GSM Integration
# =============================================================================
create_env_file() {
    log "Creating production .env file..."

    cat > "${BACKEND_DIR}/.env" <<'EOF'
# =============================================================================
# MyHibachi Backend - PRODUCTION Environment
# =============================================================================
# Secrets are fetched from Google Secret Manager at runtime
# This file only contains non-sensitive configuration

ENVIRONMENT=production
DEBUG=False

# Google Cloud Project for Secret Manager
GCP_PROJECT=my-hibachi-crm
USE_GOOGLE_SECRET_MANAGER=true

# Database (credentials from GSM)
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_ECHO=False

# Application URLs
FRONTEND_URL=https://myhibachichef.com
ADMIN_URL=https://admin.mysticdatanode.net
API_URL=https://mhapi.mysticdatanode.net

# CORS
CORS_ORIGINS=https://myhibachichef.com,https://admin.mysticdatanode.net,https://www.myhibachichef.com

# Rate Limiting (production - strict)
RATE_LIMIT_PUBLIC_PER_MINUTE=20
RATE_LIMIT_AUTH_PER_MINUTE=60
RATE_LIMIT_ADMIN_PER_MINUTE=200
RATE_LIMIT_AI_PER_MINUTE=30

# OpenAI
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7

# Email
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_FROM_EMAIL=cs@myhibachichef.com
SMTP_FROM_NAME=MyHibachi Customer Service

# RingCentral
RC_SERVER_URL=https://platform.ringcentral.com
RC_BUSINESS_PHONE_NUMBER=+19167408768

# Sentry
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Feature Flags (all OFF by default in production)
FEATURE_FLAG_AI_BOOKING_ASSISTANT=false
FEATURE_FLAG_TRAVEL_FEE_V2=false
FEATURE_FLAG_NEW_PRICING_ENGINE=false
FEATURE_FLAG_CELERY_OUTBOX=true
FEATURE_FLAG_ADVANCED_ANALYTICS=false
EOF

    chown -R "${VPS_USER}:${VPS_USER}" "${BACKEND_DIR}"
    chmod 600 "${BACKEND_DIR}/.env"

    log "✓ Production .env created"
}

# =============================================================================
# STEP 7: Setup GSM Secret Fetcher
# =============================================================================
setup_gsm_fetcher() {
    log "Creating GSM secret fetcher module..."

    mkdir -p "${BACKEND_DIR}/src/core"

    cat > "${BACKEND_DIR}/src/core/secrets.py" <<'EOF'
"""
Google Secret Manager Integration
Fetches secrets at runtime from GSM
"""
import os
import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# Check if GSM should be used
USE_GSM = os.getenv("USE_GOOGLE_SECRET_MANAGER", "false").lower() == "true"
GCP_PROJECT = os.getenv("GCP_PROJECT", "my-hibachi-crm")

if USE_GSM:
    try:
        from google.cloud import secretmanager
        _client = secretmanager.SecretManagerServiceClient()
    except ImportError:
        logger.warning("google-cloud-secret-manager not installed, falling back to env vars")
        USE_GSM = False
        _client = None
except Exception as e:
    logger.warning(f"Failed to initialize GSM client: {e}")
    USE_GSM = False
    _client = None


@lru_cache(maxsize=100)
def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Fetch a secret from Google Secret Manager or fall back to environment variable.

    Args:
        secret_name: Name of the secret (e.g., "DATABASE_URL")
        default: Default value if secret not found

    Returns:
        Secret value or default
    """
    # First check environment variable
    env_value = os.getenv(secret_name)
    if env_value and env_value != "USE_GOOGLE_SECRET_MANAGER":
        return env_value

    # Try GSM if enabled
    if USE_GSM and _client:
        try:
            name = f"projects/{GCP_PROJECT}/secrets/{secret_name}/versions/latest"
            response = _client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.warning(f"Failed to fetch secret {secret_name} from GSM: {e}")

    return default


# Pre-fetch commonly used secrets
def get_database_url() -> str:
    return get_secret("DATABASE_URL", "")

def get_redis_url() -> str:
    return get_secret("REDIS_URL", "redis://localhost:6379/0")

def get_secret_key() -> str:
    return get_secret("SECRET_KEY", "")

def get_encryption_key() -> str:
    return get_secret("ENCRYPTION_KEY", "")

def get_openai_api_key() -> str:
    return get_secret("OPENAI_API_KEY", "")

def get_stripe_secret_key() -> str:
    return get_secret("STRIPE_SECRET_KEY", "")
EOF

    log "✓ GSM secret fetcher created"
}

# =============================================================================
# STEP 8: Run Database Migrations
# =============================================================================
run_migrations() {
    log "Running database migrations..."

    cd "${BACKEND_DIR}"
    source "${VENV_DIR}/bin/activate"

    # Run alembic migrations
    alembic upgrade head

    deactivate

    log "✓ Database migrations complete"
}

# =============================================================================
# STEP 9: Setup Systemd Services
# =============================================================================
setup_systemd() {
    log "Setting up systemd services..."

    # Copy service template
    cat > /etc/systemd/system/myhibachi-backend@.service <<EOF
[Unit]
Description=MyHibachi Backend API (Instance %i)
After=network.target postgresql.service redis-server.service
Requires=postgresql.service

[Service]
Type=simple
User=${VPS_USER}
Group=${VPS_USER}
WorkingDirectory=${BACKEND_DIR}

# Port based on instance number
Environment="PORT=800%i"
Environment="WORKERS=2"
EnvironmentFile=${BACKEND_DIR}/.env

# Start command - using src.main:app structure
ExecStart=${VENV_DIR}/bin/uvicorn src.main:app \\
    --host 127.0.0.1 \\
    --port 800%i \\
    --workers 2 \\
    --log-level info \\
    --access-log

Restart=always
RestartSec=10s
TimeoutStopSec=30s
KillMode=mixed
KillSignal=SIGTERM

# Resource limits
LimitNOFILE=65536
MemoryLimit=1G
CPUQuota=50%

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # Celery worker service
    cat > /etc/systemd/system/myhibachi-celery.service <<EOF
[Unit]
Description=MyHibachi Celery Worker
After=network.target redis-server.service postgresql.service

[Service]
Type=simple
User=${VPS_USER}
Group=${VPS_USER}
WorkingDirectory=${BACKEND_DIR}
EnvironmentFile=${BACKEND_DIR}/.env

ExecStart=${VENV_DIR}/bin/celery -A src.core.celery_app worker \\
    --loglevel=info \\
    --concurrency=4

Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF

    # Celery beat (scheduler)
    cat > /etc/systemd/system/myhibachi-celery-beat.service <<EOF
[Unit]
Description=MyHibachi Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=simple
User=${VPS_USER}
Group=${VPS_USER}
WorkingDirectory=${BACKEND_DIR}
EnvironmentFile=${BACKEND_DIR}/.env

ExecStart=${VENV_DIR}/bin/celery -A src.core.celery_app beat \\
    --loglevel=info

Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload

    # Enable services
    systemctl enable myhibachi-backend@1.service
    systemctl enable myhibachi-backend@2.service
    systemctl enable myhibachi-celery.service
    systemctl enable myhibachi-celery-beat.service

    log "✓ Systemd services configured"
}

# =============================================================================
# STEP 10: Setup Nginx
# =============================================================================
setup_nginx() {
    log "Setting up Nginx..."

    # Create upstream config
    cat > /etc/nginx/conf.d/myhibachi-upstream.conf <<EOF
upstream myhibachi_backend {
    least_conn;
    server 127.0.0.1:8001 max_fails=2 fail_timeout=30s weight=3;
    server 127.0.0.1:8002 max_fails=2 fail_timeout=30s weight=2 backup;
    keepalive 32;
}
EOF

    # Test nginx configuration
    nginx -t

    # Reload nginx
    systemctl reload nginx

    log "✓ Nginx configured"
}

# =============================================================================
# STEP 11: Start Services
# =============================================================================
start_services() {
    log "Starting all services..."

    # Start backend instances
    systemctl start myhibachi-backend@1.service
    sleep 5
    systemctl start myhibachi-backend@2.service

    # Start Celery
    systemctl start myhibachi-celery.service
    systemctl start myhibachi-celery-beat.service

    log "✓ All services started"
}

# =============================================================================
# STEP 12: Verify Deployment
# =============================================================================
verify_deployment() {
    log "Verifying deployment..."

    echo ""
    info "Service Status:"
    echo "  Backend @1: $(systemctl is-active myhibachi-backend@1.service)"
    echo "  Backend @2: $(systemctl is-active myhibachi-backend@2.service)"
    echo "  Celery:     $(systemctl is-active myhibachi-celery.service)"
    echo "  Beat:       $(systemctl is-active myhibachi-celery-beat.service)"

    echo ""
    info "Health Checks:"

    # Check backend health
    for port in 8001 8002; do
        response=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${port}/health" || echo "000")
        if [ "$response" == "200" ]; then
            echo "  Port ${port}: ✓ OK (HTTP ${response})"
        else
            echo "  Port ${port}: ✗ FAILED (HTTP ${response})"
        fi
    done

    echo ""
    log "=================================="
    log "DEPLOYMENT COMPLETE!"
    log "=================================="
    echo ""
    info "Next Steps:"
    echo "  1. Configure SSL with Plesk Let's Encrypt"
    echo "  2. Point DNS to this VPS IP"
    echo "  3. Test: curl https://mhapi.mysticdatanode.net/health"
    echo ""
    info "Useful Commands:"
    echo "  View logs:    journalctl -u myhibachi-backend@1 -f"
    echo "  Restart:      systemctl restart myhibachi-backend@1"
    echo "  Deploy:       bash /usr/local/bin/deploy_myhibachi.sh"
    echo ""
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================
main() {
    echo ""
    log "=============================================="
    log "MyHibachi Backend VPS Deployment"
    log "=============================================="
    echo ""

    check_prerequisites
    setup_database
    setup_redis
    setup_code
    setup_python
    create_env_file
    setup_gsm_fetcher
    run_migrations
    setup_systemd
    setup_nginx
    start_services
    verify_deployment
}

# Run main function
main "$@"
