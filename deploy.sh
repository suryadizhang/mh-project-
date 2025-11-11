#!/bin/bash

# My Hibachi Production Deployment Script
# This script automates the deployment of the My Hibachi application stack

set -e  # Exit on any error

# Configuration
APP_DIR="/opt/myhibachi"
REPO_URL="https://github.com/yourusername/mh-project-.git"  # Update with actual repo
SERVICE_USER="myhibachi"
BACKUP_DIR="/var/backups/myhibachi"

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

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        exit 1
    fi
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    apt update
    apt install -y \
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
        python3-certbot-nginx \
        curl \
        unzip
    
    systemctl enable docker
    systemctl start docker
    
    success "System dependencies installed"
}

# Create application user
create_user() {
    log "Creating application user..."
    
    if id "$SERVICE_USER" &>/dev/null; then
        warning "User $SERVICE_USER already exists"
    else
        useradd -m -s /bin/bash "$SERVICE_USER"
        usermod -aG docker "$SERVICE_USER"
        success "User $SERVICE_USER created"
    fi
    
    # Create directory structure
    mkdir -p "$APP_DIR"/{config,logs,data,backups}
    mkdir -p "$BACKUP_DIR"
    mkdir -p /var/log/myhibachi
    mkdir -p /var/lib/myhibachi/monitoring
    
    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"
    chown "$SERVICE_USER:$SERVICE_USER" "$BACKUP_DIR"
    chown "$SERVICE_USER:$SERVICE_USER" /var/log/myhibachi
    chown "$SERVICE_USER:$SERVICE_USER" /var/lib/myhibachi/monitoring
    
    success "Directory structure created"
}

# Configure firewall
configure_firewall() {
    log "Configuring firewall..."
    
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80
    ufw allow 443
    ufw --force enable
    
    systemctl enable fail2ban
    systemctl start fail2ban
    
    success "Firewall configured"
}

# Clone repository
clone_repository() {
    log "Cloning repository..."
    
    if [[ -d "$APP_DIR/app" ]]; then
        warning "Application directory already exists, updating..."
        cd "$APP_DIR/app"
        sudo -u "$SERVICE_USER" git pull
    else
        cd "$APP_DIR"
        sudo -u "$SERVICE_USER" git clone "$REPO_URL" app
    fi
    
    success "Repository cloned/updated"
}

# Setup environment
setup_environment() {
    log "Setting up environment..."
    
    if [[ ! -f "$APP_DIR/config/.env" ]]; then
        cp "$APP_DIR/app/myhibachi-backend-fastapi/.env.example" "$APP_DIR/config/.env"
        chown "$SERVICE_USER:$SERVICE_USER" "$APP_DIR/config/.env"
        chmod 600 "$APP_DIR/config/.env"
        
        warning "Environment file created at $APP_DIR/config/.env"
        warning "Please edit this file with your production values before continuing"
        warning "Press Enter when you have configured the environment file..."
        read
    else
        success "Environment file already exists"
    fi
}

# Setup SSL certificates
setup_ssl() {
    read -p "Enter your domain name (e.g., yourdomain.com): " DOMAIN
    
    if [[ -z "$DOMAIN" ]]; then
        warning "No domain provided, skipping SSL setup"
        return
    fi
    
    log "Setting up SSL certificate for $DOMAIN..."
    
    # Create basic nginx configuration for certbot
    cat > /etc/nginx/sites-available/default << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF
    
    nginx -t && systemctl reload nginx
    
    # Get SSL certificate
    certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN"
    
    # Test auto-renewal
    certbot renew --dry-run
    
    success "SSL certificate configured"
}

# Install systemd services
install_services() {
    log "Installing systemd services..."
    
    cp "$APP_DIR/app/ops/systemd/"*.service /etc/systemd/system/
    cp "$APP_DIR/app/ops/systemd/"*.timer /etc/systemd/system/
    
    systemctl daemon-reload
    
    # Enable and start services
    systemctl enable myhibachi-health-monitor.service
    systemctl start myhibachi-health-monitor.service
    
    systemctl enable myhibachi-backup.timer
    systemctl start myhibachi-backup.timer
    
    success "Systemd services installed and started"
}

# Deploy application
deploy_application() {
    log "Deploying application..."
    
    cd "$APP_DIR/app"
    
    # Create production environment file link
    ln -sf "$APP_DIR/config/.env" myhibachi-backend-fastapi/.env
    
    # Build and start services
    sudo -u "$SERVICE_USER" docker compose -f docker-compose.prod.yml build
    sudo -u "$SERVICE_USER" docker compose -f docker-compose.prod.yml up -d
    
    # Wait for services to start
    sleep 30
    
    # Run database migrations
    sudo -u "$SERVICE_USER" docker compose -f docker-compose.prod.yml exec fastapi-backend alembic upgrade head
    
    success "Application deployed"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    cd "$APP_DIR/app"
    
    # Check service status
    sudo -u "$SERVICE_USER" docker compose -f docker-compose.prod.yml ps
    
    # Check health endpoints
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        success "Backend health check passed"
    else
        error "Backend health check failed"
    fi
    
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        success "Frontend health check passed"
    else
        error "Frontend health check failed"
    fi
    
    # Run system health monitor
    cd "$APP_DIR/app"
    python3 ops/system_health_monitor.py --once
    
    success "Deployment verification completed"
}

# Create admin user
create_admin_user() {
    log "Creating admin user..."
    
    read -p "Enter admin email: " ADMIN_EMAIL
    read -s -p "Enter admin password: " ADMIN_PASSWORD
    echo
    
    cd "$APP_DIR/app"
    sudo -u "$SERVICE_USER" docker compose -f docker-compose.prod.yml exec fastapi-backend python -c "
from app.auth import create_admin_user
create_admin_user('$ADMIN_EMAIL', '$ADMIN_PASSWORD')
print('Admin user created successfully')
"
    
    success "Admin user created"
}

# Main deployment function
main() {
    log "Starting My Hibachi deployment..."
    
    check_root
    install_dependencies
    create_user
    configure_firewall
    clone_repository
    setup_environment
    setup_ssl
    install_services
    deploy_application
    verify_deployment
    create_admin_user
    
    success "Deployment completed successfully!"
    
    echo ""
    echo "Next steps:"
    echo "1. Configure your domain DNS to point to this server"
    echo "2. Review and adjust environment variables in $APP_DIR/config/.env"
    echo "3. Set up monitoring and alerting"
    echo "4. Configure backup storage (AWS S3, etc.)"
    echo "5. Test all functionality"
    echo ""
    echo "Useful commands:"
    echo "  - Check service status: systemctl status myhibachi-health-monitor"
    echo "  - View application logs: cd $APP_DIR/app && docker compose -f docker-compose.prod.yml logs -f"
    echo "  - Run health check: cd $APP_DIR/app && python3 ops/system_health_monitor.py --once"
    echo "  - Manual backup: cd $APP_DIR/app && python3 ops/backup_db.py"
}

# Run main function
main "$@"