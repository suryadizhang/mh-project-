#!/bin/bash
# =============================================================================
# MyHibachi Local Development & Testing Deployment Script
# =============================================================================
# This script starts all services locally for comprehensive testing

set -e

echo "🚀 MyHibachi Local Deployment Script"
echo "======================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -d "apps" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within timeout"
    return 1
}

# Install dependencies
print_status "Installing dependencies..."

# Install root dependencies
npm install

# Install API dependencies
print_status "Installing Python API dependencies..."
cd apps/api
pip install -r requirements.txt
cd ../..

# Install customer app dependencies
print_status "Installing customer app dependencies..."
cd apps/customer
npm install
cd ../..

# Install admin app dependencies
print_status "Installing admin app dependencies..."
cd apps/admin
npm install
cd ../..

print_success "All dependencies installed!"

# Check for database
print_status "Checking database connection..."
cd apps/api
if python -c "
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def check_db():
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.begin() as conn:
            await conn.execute('SELECT 1')
        print('Database connection successful')
        return True
    except Exception as e:
        print(f'Database connection failed: {e}')
        return False

result = asyncio.run(check_db())
sys.exit(0 if result else 1)
" 2>/dev/null; then
    print_success "Database connection successful"
else
    print_warning "Database connection failed - make sure PostgreSQL is running"
    print_status "You can start PostgreSQL with: docker-compose up -d db"
fi
cd ../..

# Run database migrations
print_status "Running database migrations..."
cd apps/api
alembic upgrade head
cd ../..

# Check for conflicting processes
print_status "Checking for conflicting processes..."

ports_to_check=(3000 3001 8000 8001)
for port in "${ports_to_check[@]}"; do
    if check_port $port; then
        print_warning "Port $port is already in use. Please stop the conflicting process."
    fi
done

# Start services in background
print_status "Starting all services..."

# Start API server
print_status "Starting FastAPI backend (port 8000)..."
cd apps/api
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../../logs/api.log 2>&1 &
API_PID=$!
echo $API_PID > ../../.api.pid
cd ../..

# Wait for API to be ready
wait_for_service "http://localhost:8000/health" "FastAPI API"

# Start customer frontend
print_status "Starting customer frontend (port 3000)..."
cd apps/customer
nohup npm run dev > ../../logs/customer.log 2>&1 &
CUSTOMER_PID=$!
echo $CUSTOMER_PID > ../../.customer.pid
cd ../..

# Start admin frontend
print_status "Starting admin frontend (port 3001)..."
cd apps/admin
nohup npm run dev -- --port 3001 > ../../logs/admin.log 2>&1 &
ADMIN_PID=$!
echo $ADMIN_PID > ../../.admin.pid
cd ../..

# Wait for frontends to be ready
wait_for_service "http://localhost:3000" "Customer Frontend"
wait_for_service "http://localhost:3001" "Admin Frontend"

# Display service status
echo ""
print_success "🎉 All services started successfully!"
echo "======================================================"
echo ""
echo "📊 Service URLs:"
echo "  • Customer App:     http://localhost:3000"
echo "  • Admin Dashboard:  http://localhost:3001"
echo "  • API Server:       http://localhost:8000"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Health Check:     http://localhost:8000/health"
echo ""
echo "📝 Log Files:"
echo "  • API Logs:         logs/api.log"
echo "  • Customer Logs:    logs/customer.log"
echo "  • Admin Logs:       logs/admin.log"
echo ""
echo "🛑 To stop all services:"
echo "  ./scripts/stop-local.sh"
echo ""

# Save service info
cat > .services.json << EOF
{
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "services": {
    "api": {
      "pid": $API_PID,
      "port": 8000,
      "url": "http://localhost:8000",
      "log": "logs/api.log"
    },
    "customer": {
      "pid": $CUSTOMER_PID,
      "port": 3000,
      "url": "http://localhost:3000",
      "log": "logs/customer.log"
    },
    "admin": {
      "pid": $ADMIN_PID,
      "port": 3001,
      "url": "http://localhost:3001",
      "log": "logs/admin.log"
    }
  }
}
EOF

print_success "Service information saved to .services.json"

# Run basic health checks
print_status "Running basic health checks..."
sleep 5

for url in "http://localhost:8000/health" "http://localhost:3000" "http://localhost:3001"; do
    if curl -s -f "$url" > /dev/null; then
        print_success "✅ $url is responding"
    else
        print_warning "⚠️  $url is not responding"
    fi
done

echo ""
print_success "🚀 Local deployment complete! All services are running."
echo "======================================================"