#!/bin/bash
# MyHibachi Zero-Downtime Deployment Script
# Location: /usr/local/bin/deploy_myhibachi.sh
#
# This script performs a rolling deployment across all backend instances,
# ensuring zero downtime by restarting one instance at a time and verifying
# health before proceeding to the next.
#
# Usage:
#   sudo /usr/local/bin/deploy_myhibachi.sh
#
# Prerequisites:
#   - Git repository configured in backend directory
#   - Python virtual environment at .venv/
#   - Systemd services: myhibachi-backend@1, @2, @3
#
# Exit codes:
#   0 - Success
#   1 - Deployment failed (instance didn't start)
#   2 - Git pull failed
#   3 - Dependency installation failed
#   4 - Migration failed

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Configuration
BACKEND_DIR="/var/www/vhosts/myhibachi.com/backend"
VENV_DIR="$BACKEND_DIR/.venv"
INSTANCES=(1 2 3)
HEALTH_CHECK_ATTEMPTS=10
HEALTH_CHECK_DELAY=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root (use sudo)"
    exit 1
fi

log "Starting zero-downtime deployment for MyHibachi..."

# Step 1: Pull latest code
log "Pulling latest code from repository..."
cd "$BACKEND_DIR"

if ! git pull origin main; then
    error "Git pull failed!"
    exit 2
fi

log "Code updated successfully"

# Step 2: Update dependencies
log "Updating Python dependencies..."
source "$VENV_DIR/bin/activate"

if ! pip install --upgrade -r apps/backend/requirements.txt; then
    error "Failed to install dependencies!"
    deactivate
    exit 3
fi

log "Dependencies updated successfully"

# Step 3: Run database migrations
log "Running database migrations..."
cd apps/backend

if ! alembic upgrade head; then
    error "Database migration failed!"
    cd "$BACKEND_DIR"
    deactivate
    exit 4
fi

cd "$BACKEND_DIR"
deactivate

log "Migrations completed successfully"

# Step 4: Rolling restart of backend instances
log "Starting rolling restart of backend instances..."

for instance in "${INSTANCES[@]}"; do
    log "Restarting instance $instance..."

    # Restart the service
    systemctl restart "myhibachi-backend@$instance.service"

    # Wait for instance to be healthy
    log "Waiting for instance $instance to be healthy..."

    healthy=false
    for attempt in $(seq 1 $HEALTH_CHECK_ATTEMPTS); do
        sleep $HEALTH_CHECK_DELAY

        response=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:800$instance/health" || echo "000")

        if [ "$response" == "200" ]; then
            log "Instance $instance is healthy (HTTP 200)"
            healthy=true
            break
        fi

        warn "Instance $instance not ready yet (attempt $attempt/$HEALTH_CHECK_ATTEMPTS, HTTP $response)"
    done

    if [ "$healthy" = false ]; then
        error "Instance $instance failed to start after $HEALTH_CHECK_ATTEMPTS attempts!"
        error "Check logs: journalctl -u myhibachi-backend@$instance.service -n 50"
        exit 1
    fi

    # Wait additional time before next instance (allows stabilization)
    if [ "$instance" != "${INSTANCES[-1]}" ]; then
        log "Waiting 10 seconds before restarting next instance..."
        sleep 10
    fi
done

# Step 5: Verify all instances are running
log "Verifying all instances are running..."

all_healthy=true
for instance in "${INSTANCES[@]}"; do
    status=$(systemctl is-active "myhibachi-backend@$instance.service")
    if [ "$status" != "active" ]; then
        error "Instance $instance is not active (status: $status)"
        all_healthy=false
    else
        log "Instance $instance: $status ✓"
    fi
done

if [ "$all_healthy" = false ]; then
    error "Some instances are not running!"
    exit 1
fi

# Step 6: Final health check via load balancer
log "Testing load balancer health..."

lb_response=$(curl -s -o /dev/null -w "%{http_code}" "https://myhibachichef.com/health" || echo "000")

if [ "$lb_response" == "200" ]; then
    log "Load balancer health check: OK (HTTP 200) ✓"
else
    warn "Load balancer returned HTTP $lb_response (may need DNS/SSL configuration)"
fi

# Success!
echo ""
log "=================================="
log "Deployment completed successfully!"
log "=================================="
log "All $instance backend instances are running and healthy."
log ""
log "Next steps:"
log "  - Monitor logs: journalctl -u myhibachi-backend@*.service -f"
log "  - Check Nginx access logs: tail -f /var/www/vhosts/myhibachi.com/logs/access_ssl_log"
log "  - Verify load distribution: curl -I https://myhibachichef.com/health | grep X-Backend-Server"
echo ""

exit 0
