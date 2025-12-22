#!/bin/bash
# =============================================================================
# Akaunting Installation Script for MyHibachi VPS
# =============================================================================
# Run this script on the VPS after upgrade completes.
# Prerequisites: Docker, docker-compose installed
#
# Usage:
#   scp docker/akaunting/* root@108.175.12.154:/opt/akaunting/
#   ssh root@108.175.12.154
#   cd /opt/akaunting
#   chmod +x install.sh
#   ./install.sh

set -e

echo "================================================"
echo "  MyHibachi Akaunting Installation"
echo "================================================"

# =============================================================================
# Configuration
# =============================================================================
AKAUNTING_DIR="/opt/akaunting"
DB_NAME="akaunting"
DB_USER="akaunting_user"
# Generate secure password if not provided
DB_PASSWORD="${AKAUNTING_DB_PASSWORD:-$(openssl rand -base64 32)}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# =============================================================================
# Pre-flight Checks
# =============================================================================
echo -e "\n${YELLOW}[1/8] Pre-flight checks...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker not found. Installing...${NC}"
    dnf install -y docker
    systemctl enable docker
    systemctl start docker
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}docker-compose not found. Installing...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo -e "${GREEN}✓ Docker and docker-compose ready${NC}"

# =============================================================================
# Create Directory Structure
# =============================================================================
echo -e "\n${YELLOW}[2/8] Creating directory structure...${NC}"

mkdir -p $AKAUNTING_DIR/{modules,logos,backups}
cd $AKAUNTING_DIR

echo -e "${GREEN}✓ Directories created${NC}"

# =============================================================================
# Create PostgreSQL Database
# =============================================================================
echo -e "\n${YELLOW}[3/8] Creating PostgreSQL database...${NC}"

# Check if database already exists
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo -e "${YELLOW}Database $DB_NAME already exists. Skipping creation.${NC}"
else
    # Create database and user
    sudo -u postgres psql << EOF
-- Create user
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';

-- Create database
CREATE DATABASE $DB_NAME OWNER $DB_USER;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Connect to database and set up extensions
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
EOF

    echo -e "${GREEN}✓ Database created: $DB_NAME${NC}"
    echo -e "${GREEN}✓ User created: $DB_USER${NC}"
fi

# =============================================================================
# Create Environment File
# =============================================================================
echo -e "\n${YELLOW}[4/8] Creating environment file...${NC}"

if [ ! -f "$AKAUNTING_DIR/.env" ]; then
    cat > $AKAUNTING_DIR/.env << EOF
# Akaunting Environment Configuration
# Generated: $(date)

# Database
DB_HOST=host.docker.internal
AKAUNTING_DB_USER=$DB_USER
AKAUNTING_DB_PASSWORD=$DB_PASSWORD

# Application
APP_URL=https://accounting.mysticdatanode.net
APP_DEBUG=false
APP_ENV=production
EOF
    echo -e "${GREEN}✓ Environment file created${NC}"
    echo -e "${YELLOW}  Database password: $DB_PASSWORD${NC}"
    echo -e "${YELLOW}  (Save this password securely!)${NC}"
else
    echo -e "${YELLOW}.env file already exists. Skipping.${NC}"
fi

# =============================================================================
# Update Cloudflare Tunnel Config
# =============================================================================
echo -e "\n${YELLOW}[5/8] Updating Cloudflare tunnel config...${NC}"

# Backup existing config
cp /etc/cloudflared/config.yml /etc/cloudflared/config.yml.backup.$(date +%Y%m%d)

# Check if accounting entry exists
if grep -q "accounting.mysticdatanode.net" /etc/cloudflared/config.yml; then
    echo -e "${YELLOW}Accounting route already in tunnel config${NC}"
else
    # Add accounting route before the catch-all
    sed -i '/- service: http_status:404/i\  # Accounting (Akaunting)\n  - hostname: accounting.mysticdatanode.net\n    service: http://localhost:9000\n    originRequest:\n      noTLSVerify: true\n' /etc/cloudflared/config.yml
    echo -e "${GREEN}✓ Added accounting route to tunnel config${NC}"
fi

# =============================================================================
# Copy Docker Compose File
# =============================================================================
echo -e "\n${YELLOW}[6/8] Setting up Docker Compose...${NC}"

# If docker-compose.yml not already copied, create it
if [ ! -f "$AKAUNTING_DIR/docker-compose.yml" ]; then
    echo -e "${RED}docker-compose.yml not found. Please copy from local.${NC}"
    echo -e "Run: scp docker/akaunting/docker-compose.yml root@108.175.12.154:$AKAUNTING_DIR/"
    exit 1
fi

echo -e "${GREEN}✓ docker-compose.yml ready${NC}"

# =============================================================================
# Start Akaunting
# =============================================================================
echo -e "\n${YELLOW}[7/8] Starting Akaunting...${NC}"

cd $AKAUNTING_DIR
docker-compose pull
docker-compose up -d

echo -e "${GREEN}✓ Akaunting containers started${NC}"

# Wait for startup
echo "Waiting for Akaunting to initialize (30 seconds)..."
sleep 30

# =============================================================================
# Restart Cloudflare Tunnel
# =============================================================================
echo -e "\n${YELLOW}[8/8] Restarting Cloudflare tunnel...${NC}"

systemctl restart cloudflared
sleep 5

# Verify tunnel
if cloudflared tunnel list | grep -q "82034f96"; then
    echo -e "${GREEN}✓ Cloudflare tunnel running${NC}"
else
    echo -e "${RED}Warning: Cloudflare tunnel may not be running${NC}"
fi

# =============================================================================
# Summary
# =============================================================================
echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Access Akaunting at:"
echo "  https://accounting.mysticdatanode.net"
echo ""
echo "Setup Wizard Credentials (create on first access):"
echo "  Database Host: host.docker.internal"
echo "  Database Name: $DB_NAME"
echo "  Database User: $DB_USER"
echo "  Database Password: $DB_PASSWORD"
echo ""
echo "Next Steps:"
echo "  1. Complete the Akaunting setup wizard"
echo "  2. Create companies for each station:"
echo "     - My Hibachi Austin (AUS)"
echo "     - My Hibachi Dallas (DFW)"
echo "     - My Hibachi Houston (HOU)"
echo "     - My Hibachi Bay Area (CA-FREMONT-001)"
echo "  3. Configure tax rates per state"
echo "  4. Create API token: Settings → API → Create Token"
echo "  5. Save API token to Google Secret Manager"
echo ""
echo "Useful Commands:"
echo "  docker-compose logs -f akaunting  # View logs"
echo "  docker-compose restart            # Restart"
echo "  docker-compose down               # Stop"
echo ""
