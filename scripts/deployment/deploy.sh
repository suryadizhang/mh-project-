#!/bin/bash

# =============================================================================
# My Hibachi Chef CRM - Unified API Deployment Script for Plesk VPS
# =============================================================================

set -e  # Exit on any error

# Configuration
API_DIR="/var/www/vhosts/api.myhibachichef.com/myhibachi-api"
VENV_DIR="$API_DIR/venv"
SERVICE_NAME="myhibachi-api"
NGINX_CONF_SOURCE="infrastructure/nginx/api.myhibachichef.com.conf"
SYSTEMD_SERVICE_SOURCE="infrastructure/systemd/myhibachi-api.service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root or with sudo
check_permissions() {
    log "Checking permissions..."
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root or with sudo"
        exit 1
    fi
    success "Running with appropriate permissions"
}

# Backup current deployment
backup_current() {
    log "Creating backup of current deployment..."
    if [ -d "$API_DIR" ]; then
        BACKUP_DIR="/var/backups/myhibachi-api-$(date +%Y%m%d-%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # Backup application files
        if [ -d "$API_DIR/src" ]; then
            cp -r "$API_DIR/src" "$BACKUP_DIR/"
        fi
        
        # Backup environment file
        if [ -f "$API_DIR/.env" ]; then
            cp "$API_DIR/.env" "$BACKUP_DIR/"
        fi
        
        # Backup logs
        if [ -d "$API_DIR/logs" ]; then
            cp -r "$API_DIR/logs" "$BACKUP_DIR/"
        fi
        
        success "Backup created at $BACKUP_DIR"
    else
        warning "No existing deployment found to backup"
    fi
}

# Setup directory structure
setup_directories() {
    log "Setting up directory structure..."
    
    # Create main directory
    mkdir -p "$API_DIR"
    mkdir -p "$API_DIR/logs"
    mkdir -p "$API_DIR/uploads"
    
    # Set ownership
    chown -R www-data:www-data "$API_DIR"
    
    success "Directory structure created"
}

# Clone or update repository
update_code() {
    log "Updating application code..."
    
    cd "$API_DIR"
    
    if [ -d ".git" ]; then
        log "Updating existing repository..."
        sudo -u www-data git pull origin main
    else
        log "Cloning repository..."
        # Remove any existing files
        rm -rf ./*
        sudo -u www-data git clone https://github.com/suryadizhang/mh-project- .
    fi
    
    success "Code updated successfully"
}

# Setup Python virtual environment
setup_venv() {
    log "Setting up Python virtual environment..."
    
    cd "$API_DIR"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        sudo -u www-data python3.11 -m venv "$VENV_DIR"
    fi
    
    # Activate and upgrade pip
    sudo -u www-data "$VENV_DIR/bin/pip" install --upgrade pip
    
    # Install requirements
    if [ -f "apps/backend/requirements.txt" ]; then
        sudo -u www-data "$VENV_DIR/bin/pip" install -r apps/backend/requirements.txt
    else
        error "Requirements file not found at apps/backend/requirements.txt"
        exit 1
    fi
    
    success "Virtual environment configured"
}

# Setup environment variables
setup_environment() {
    log "Setting up environment variables..."
    
    if [ ! -f "$API_DIR/.env" ]; then
        if [ -f "config/environments/.env.production.template" ]; then
            cp "config/environments/.env.production.template" "$API_DIR/.env"
            warning "Environment template copied. Please update with actual values!"
            warning "Edit $API_DIR/.env with production credentials"
        else
            error "Production environment template not found"
            exit 1
        fi
    else
        log "Environment file already exists, skipping template copy"
    fi
    
    # Set proper permissions
    chmod 600 "$API_DIR/.env"
    chown www-data:www-data "$API_DIR/.env"
    
    success "Environment configuration ready"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    cd "$API_DIR/apps/backend/src"
    
    # Check if alembic is configured
    if [ -f "../alembic.ini" ]; then
        sudo -u www-data "$VENV_DIR/bin/alembic" upgrade head
        success "Database migrations completed"
    else
        warning "Alembic not configured, skipping migrations"
    fi
}

# Install systemd service
install_service() {
    log "Installing systemd service..."
    
    if [ -f "$SYSTEMD_SERVICE_SOURCE" ]; then
        cp "$SYSTEMD_SERVICE_SOURCE" "/etc/systemd/system/$SERVICE_NAME.service"
        systemctl daemon-reload
        systemctl enable "$SERVICE_NAME"
        success "Systemd service installed and enabled"
    else
        error "Systemd service file not found at $SYSTEMD_SERVICE_SOURCE"
        exit 1
    fi
}

# Configure Nginx
configure_nginx() {
    log "Configuring Nginx..."
    
    if [ -f "$NGINX_CONF_SOURCE" ]; then
        # For Plesk, copy to the domain's conf directory
        PLESK_CONF_DIR="/var/www/vhosts/api.myhibachichef.com/conf"
        
        if [ -d "$PLESK_CONF_DIR" ]; then
            cp "$NGINX_CONF_SOURCE" "$PLESK_CONF_DIR/nginx.conf"
            
            # Test nginx configuration
            nginx -t
            if [ $? -eq 0 ]; then
                systemctl reload nginx
                success "Nginx configuration updated and reloaded"
            else
                error "Nginx configuration test failed"
                exit 1
            fi
        else
            warning "Plesk configuration directory not found, manual Nginx setup required"
        fi
    else
        error "Nginx configuration file not found at $NGINX_CONF_SOURCE"
        exit 1
    fi
}

# Start services
start_services() {
    log "Starting services..."
    
    # Start the API service
    systemctl restart "$SERVICE_NAME"
    
    # Wait a moment for startup
    sleep 5
    
    # Check service status
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        success "API service started successfully"
    else
        error "Failed to start API service"
        systemctl status "$SERVICE_NAME"
        exit 1
    fi
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Wait a bit more for the service to fully start
    sleep 10
    
    # Test the health endpoint
    if curl -f -s http://127.0.0.1:8000/health > /dev/null; then
        success "Health check passed - API is responding"
        
        # Test the public endpoint
        if curl -f -s https://api.myhibachichef.com/health > /dev/null; then
            success "Public endpoint health check passed"
        else
            warning "Public endpoint health check failed - check DNS/SSL"
        fi
    else
        error "Health check failed - API is not responding"
        systemctl status "$SERVICE_NAME"
        tail -n 50 "$API_DIR/logs/error.log"
        exit 1
    fi
}

# Display deployment info
show_deployment_info() {
    log "Deployment Information:"
    echo "========================"
    echo "API Directory: $API_DIR"
    echo "Service Name: $SERVICE_NAME"
    echo "Environment File: $API_DIR/.env"
    echo "Logs: $API_DIR/logs/"
    echo "Virtual Environment: $VENV_DIR"
    echo ""
    echo "Endpoints:"
    echo "- Health: https://api.myhibachichef.com/health"
    echo "- API Docs: https://api.myhibachichef.com/docs"
    echo "- Operational: https://api.myhibachichef.com/v1/"
    echo "- AI: https://api.myhibachichef.com/v1/ai/"
    echo "- Webhooks: https://api.myhibachichef.com/webhooks/"
    echo "- WebSockets: wss://api.myhibachichef.com/ws/"
    echo ""
    echo "Rate Limits:"
    echo "- Public: 20 req/min, 1000 req/hour"
    echo "- Admin: 100 req/min, 5000 req/hour"
    echo "- Admin Super: 200 req/min, 10000 req/hour"
    echo "- AI: 10 req/min, 300 req/hour"
    echo ""
    echo "Management Commands:"
    echo "- Check status: systemctl status $SERVICE_NAME"
    echo "- View logs: journalctl -u $SERVICE_NAME -f"
    echo "- Restart: systemctl restart $SERVICE_NAME"
}

# Main deployment function
main() {
    log "Starting My Hibachi Chef CRM Unified API Deployment"
    log "=================================================="
    
    # Pre-deployment checks
    check_permissions
    
    # Stop service if running
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log "Stopping existing service..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    # Deployment steps
    backup_current
    setup_directories
    update_code
    setup_venv
    setup_environment
    run_migrations
    install_service
    configure_nginx
    start_services
    health_check
    
    # Success message
    success "🎉 Deployment completed successfully!"
    show_deployment_info
    
    log "Unified API deployment complete. All operational and AI endpoints are now available at api.myhibachichef.com"
}

# Help function
show_help() {
    echo "My Hibachi Chef CRM - Unified API Deployment Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  --backup-only  Only create backup, don't deploy"
    echo "  --no-backup    Skip backup creation"
    echo "  --health-only  Only run health check"
    echo ""
    echo "Examples:"
    echo "  $0                 # Full deployment"
    echo "  $0 --backup-only   # Just backup current version"
    echo "  $0 --health-only   # Check if API is healthy"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    --backup-only)
        backup_current
        exit 0
        ;;
    --health-only)
        health_check
        exit 0
        ;;
    --no-backup)
        # Continue to main but skip backup
        SKIP_BACKUP=true
        ;;
esac

# Run main deployment
main