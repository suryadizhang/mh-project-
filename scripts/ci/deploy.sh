#!/bin/bash
set -euo pipefail

# Deploy component to VPS
# Usage: ./deploy.sh <component> <app_dir>

COMPONENT="${1:-}"
APP_DIR="${2:-/srv/$COMPONENT}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# SSH configuration from environment
SSH_HOST="${SSH_HOST:-}"
SSH_USER="${SSH_USER:-deployer}"
SSH_KEY="${SSH_KEY:-~/.ssh/deploy_key}"
SSH_PORT="${SSH_PORT:-22}"

if [[ -z "$COMPONENT" ]]; then
    echo "Usage: $0 <component> [app_dir]"
    echo "Example: $0 admin /srv/admin"
    exit 1
fi

if [[ -z "$SSH_HOST" ]]; then
    echo "❌ SSH_HOST environment variable is required"
    exit 1
fi

echo "🚀 Deploying $COMPONENT to VPS"
echo "🎯 Target: $SSH_USER@$SSH_HOST:$APP_DIR"
echo "🏷️  Image tag: $IMAGE_TAG"

# Verify package exists
PACKAGE_FILE="${COMPONENT}-${IMAGE_TAG}.tar.gz"
if [[ ! -f "$PACKAGE_FILE" ]]; then
    echo "❌ Package file not found: $PACKAGE_FILE"
    echo "Run extract.sh first to create the deployment package"
    exit 1
fi

# Test SSH connection
echo "🔌 Testing SSH connection..."
if ! ssh -i "$SSH_KEY" -p "$SSH_PORT" -o ConnectTimeout=10 -o BatchMode=yes "$SSH_USER@$SSH_HOST" echo "SSH connection successful"; then
    echo "❌ SSH connection failed"
    exit 1
fi

# Create remote directories
echo "📁 Creating remote directories..."
ssh -i "$SSH_KEY" -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "
    sudo mkdir -p $APP_DIR/{current,backup,releases}
    sudo chown -R $SSH_USER:$SSH_USER $APP_DIR
"

# Upload deployment package
echo "📦 Uploading deployment package..."
scp -i "$SSH_KEY" -P "$SSH_PORT" "$PACKAGE_FILE" "$SSH_USER@$SSH_HOST:$APP_DIR/releases/"

# Deploy on remote server
echo "🔧 Deploying on remote server..."
ssh -i "$SSH_KEY" -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "
    set -euo pipefail
    cd $APP_DIR

    echo '🎯 Starting deployment of $COMPONENT...'

    # Backup current deployment
    if [[ -d current ]]; then
        echo '📋 Backing up current deployment...'
        rm -rf backup
        cp -r current backup
        echo '✅ Current deployment backed up'
    fi

    # Extract new deployment
    echo '📦 Extracting new deployment...'
    cd releases
    tar -xzf '$PACKAGE_FILE'
    cd ..

    # Atomic deployment switch
    echo '🔄 Switching to new deployment...'
    rm -rf current
    mv releases/$COMPONENT current

    # Set permissions
    sudo chown -R $SSH_USER:www-data current/
    sudo chmod -R 755 current/

    # Component-specific deployment steps
    case '$COMPONENT' in
        'admin'|'customer')
            echo '🎨 Deploying Next.js frontend...'

            # Install Node.js dependencies if needed
            if [[ -f current/package.json ]] && command -v npm >/dev/null; then
                cd current && npm ci --production --silent || true
                cd ..
            fi

            # Create/update systemd service
            sudo tee /etc/systemd/system/$COMPONENT.service > /dev/null << EOF
[Unit]
Description=$COMPONENT Frontend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=$APP_DIR/current/app
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=10
Environment=NODE_ENV=production
Environment=PORT=${PORT:-3000}

[Install]
WantedBy=multi-user.target
EOF

            # Reload and restart service
            sudo systemctl daemon-reload
            sudo systemctl enable $COMPONENT
            sudo systemctl restart $COMPONENT

            echo '✅ Next.js frontend deployed and started'
            ;;

        'api'|'ai-api')
            echo '🐍 Deploying Python API...'

            # Set up Python virtual environment
            if command -v python3 >/dev/null; then
                cd current
                python3 -m venv venv
                source venv/bin/activate
                if [[ -f requirements.txt ]]; then
                    pip install --quiet -r requirements.txt
                fi
                deactivate
                cd ..
            fi

            # Determine port based on component
            case '$COMPONENT' in
                'api') PORT=8001 ;;
                'ai-api') PORT=8002 ;;
                *) PORT=8000 ;;
            esac

            # Create/update systemd service
            sudo tee /etc/systemd/system/$COMPONENT.service > /dev/null << EOF
[Unit]
Description=$COMPONENT API Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=$APP_DIR/current/app
Environment=PATH=$APP_DIR/current/venv/bin
ExecStart=$APP_DIR/current/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port $PORT
Restart=always
RestartSec=10
Environment=PYTHONPATH=$APP_DIR/current/app

[Install]
WantedBy=multi-user.target
EOF

            # Reload and restart service
            sudo systemctl daemon-reload
            sudo systemctl enable $COMPONENT
            sudo systemctl restart $COMPONENT

            echo '✅ Python API deployed and started'
            ;;

        *)
            echo '❌ Unknown component type: $COMPONENT'
            exit 1
            ;;
    esac

    # Wait for service to start
    echo '⏳ Waiting for service to start...'
    sleep 10

    # Check service status
    if sudo systemctl is-active --quiet $COMPONENT; then
        echo '✅ Service $COMPONENT is running'
        sudo systemctl status $COMPONENT --no-pager -l
    else
        echo '❌ Service $COMPONENT failed to start'
        sudo systemctl status $COMPONENT --no-pager -l
        sudo journalctl -u $COMPONENT --no-pager -l
        exit 1
    fi

    # Cleanup old releases (keep last 3)
    echo '🧹 Cleaning up old releases...'
    cd releases
    ls -t | tail -n +4 | xargs rm -f

    echo '🎉 Deployment completed successfully!'
"

# Verify deployment
echo "✅ Deployment verification..."
ssh -i "$SSH_KEY" -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "
    echo '📋 Deployment Status:'
    echo 'Component: $COMPONENT'
    echo 'Directory: $APP_DIR'
    echo 'Service Status:'
    sudo systemctl status $COMPONENT --no-pager -l | head -10
    echo ''
    echo 'Recent logs:'
    sudo journalctl -u $COMPONENT --no-pager -l | tail -5
"

echo "🎉 Deployment of $COMPONENT completed successfully!"
