#!/bin/bash
# =============================================================================
# Cloudflare Tunnel Setup Script for MyHibachi VPS
# Run this script on your VPS (108.175.12.154)
# =============================================================================

set -e

echo "========================================="
echo "🔒 Cloudflare Tunnel Setup for MyHibachi"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root (sudo)${NC}"
  exit 1
fi

# ===========================================
# Step 1: Install cloudflared
# ===========================================
echo ""
echo -e "${YELLOW}Step 1: Installing cloudflared...${NC}"

if command -v cloudflared &> /dev/null; then
    echo -e "${GREEN}cloudflared is already installed${NC}"
    cloudflared --version
else
    curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    dpkg -i cloudflared.deb
    rm cloudflared.deb
    echo -e "${GREEN}cloudflared installed successfully${NC}"
    cloudflared --version
fi

# ===========================================
# Step 2: Authenticate with Cloudflare
# ===========================================
echo ""
echo -e "${YELLOW}Step 2: Authenticating with Cloudflare...${NC}"
echo "This will open a URL. Copy it and open in your browser to authorize."
echo ""

if [ -f ~/.cloudflared/cert.pem ]; then
    echo -e "${GREEN}Already authenticated (cert.pem exists)${NC}"
else
    cloudflared tunnel login
    echo -e "${GREEN}Authentication successful${NC}"
fi

# ===========================================
# Step 3: Create Tunnel
# ===========================================
echo ""
echo -e "${YELLOW}Step 3: Creating tunnel 'myhibachi'...${NC}"

# Check if tunnel already exists
if cloudflared tunnel list | grep -q "myhibachi"; then
    echo -e "${GREEN}Tunnel 'myhibachi' already exists${NC}"
    TUNNEL_ID=$(cloudflared tunnel list | grep "myhibachi" | awk '{print $1}')
else
    cloudflared tunnel create myhibachi
    TUNNEL_ID=$(cloudflared tunnel list | grep "myhibachi" | awk '{print $1}')
    echo -e "${GREEN}Tunnel created with ID: $TUNNEL_ID${NC}"
fi

echo ""
echo -e "${GREEN}Tunnel ID: $TUNNEL_ID${NC}"
echo "Save this ID - you'll need it!"

# ===========================================
# Step 4: Create Config File
# ===========================================
echo ""
echo -e "${YELLOW}Step 4: Creating tunnel configuration...${NC}"

CRED_FILE=$(ls ~/.cloudflared/*.json 2>/dev/null | head -1)

cat > ~/.cloudflared/config.yml << EOF
# Cloudflare Tunnel Configuration for MyHibachi
tunnel: $TUNNEL_ID
credentials-file: $CRED_FILE

ingress:
  # SSH access for GitHub Actions deployment
  - hostname: ssh.mhapi.mysticdatanode.net
    service: ssh://localhost:22

  # Backend API (production instances)
  - hostname: mhapi.mysticdatanode.net
    service: http://localhost:8001

  # Catch-all rule (required)
  - service: http_status:404
EOF

echo -e "${GREEN}Config file created at ~/.cloudflared/config.yml${NC}"
cat ~/.cloudflared/config.yml

# ===========================================
# Step 5: Create DNS Records
# ===========================================
echo ""
echo -e "${YELLOW}Step 5: Creating DNS records...${NC}"
echo "This will route your domains through the tunnel."
echo ""

cloudflared tunnel route dns myhibachi mhapi.mysticdatanode.net || echo "DNS route may already exist"
cloudflared tunnel route dns myhibachi ssh.mhapi.mysticdatanode.net || echo "DNS route may already exist"

echo -e "${GREEN}DNS records configured${NC}"

# ===========================================
# Step 6: Install as System Service
# ===========================================
echo ""
echo -e "${YELLOW}Step 6: Installing cloudflared as system service...${NC}"

cloudflared service install || echo "Service may already be installed"

systemctl enable cloudflared
systemctl restart cloudflared

echo ""
echo -e "${GREEN}Service status:${NC}"
systemctl status cloudflared --no-pager

# ===========================================
# Step 7: Verify Tunnel
# ===========================================
echo ""
echo -e "${YELLOW}Step 7: Verifying tunnel...${NC}"

sleep 5
cloudflared tunnel info myhibachi

# ===========================================
# Summary
# ===========================================
echo ""
echo "========================================="
echo -e "${GREEN}✅ Cloudflare Tunnel Setup Complete!${NC}"
echo "========================================="
echo ""
echo "Tunnel ID: $TUNNEL_ID"
echo "SSH Hostname: ssh.mhapi.mysticdatanode.net"
echo "API Hostname: mhapi.mysticdatanode.net"
echo ""
echo -e "${YELLOW}NEXT STEPS (do these in Cloudflare Dashboard):${NC}"
echo ""
echo "1. Go to: https://one.dash.cloudflare.com/"
echo "2. Navigate to: Access → Applications → Add Application"
echo "3. Create 'Self-hosted' application:"
echo "   - Name: MyHibachi SSH"
echo "   - Domain: ssh.mhapi.mysticdatanode.net"
echo ""
echo "4. Create Access Policy:"
echo "   - Policy name: GitHub Actions Deploy"
echo "   - Action: Service Auth"
echo "   - Include: Service Token"
echo ""
echo "5. Create Service Token:"
echo "   - Go to: Access → Service Auth → Create Service Token"
echo "   - Name: github-actions-deploy"
echo "   - Duration: 1 year"
echo "   - SAVE THE CLIENT ID AND SECRET!"
echo ""
echo "6. Add to GitHub Secrets:"
echo "   - CF_ACCESS_CLIENT_ID"
echo "   - CF_ACCESS_CLIENT_SECRET"
echo "   - CF_SSH_HOSTNAME: ssh.mhapi.mysticdatanode.net"
echo "   - VPS_USER: root"
echo "   - VPS_DEPLOY_PATH: /var/www/vhosts/mhapi.mysticdatanode.net/backend"
echo ""
echo "========================================="
