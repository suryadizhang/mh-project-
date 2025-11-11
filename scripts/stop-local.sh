#!/bin/bash
# =============================================================================
# MyHibachi Local Services Stop Script
# =============================================================================

set -e

echo "🛑 Stopping MyHibachi Local Services"
echo "======================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to stop service by PID file
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            print_status "Stopping $service_name (PID: $pid)..."
            kill "$pid"
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "Force killing $service_name..."
                kill -9 "$pid"
            fi
            print_success "$service_name stopped"
        else
            print_warning "$service_name was not running"
        fi
        rm -f "$pid_file"
    else
        print_warning "No PID file found for $service_name"
    fi
}

# Stop all services
stop_service "API Server" ".api.pid"
stop_service "Customer Frontend" ".customer.pid"
stop_service "Admin Frontend" ".admin.pid"

# Kill any remaining processes on our ports
print_status "Checking for remaining processes..."

ports=(3000 3001 8000 8001)
for port in "${ports[@]}"; do
    if lsof -ti:$port >/dev/null 2>&1; then
        print_status "Killing processes on port $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
done

# Clean up service files
rm -f .services.json

print_success "🎉 All services stopped successfully!"
echo "======================================================"