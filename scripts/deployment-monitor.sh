#!/bin/bash
# 🚀 My Hibachi Deployment Monitor & Health Check System
# Monitors all three applications and their dependencies

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs/deployment"
HEALTH_CHECK_TIMEOUT=30

# Create log directory
mkdir -p "$LOG_DIR"

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "$timestamp [$level] $message" | tee -a "$LOG_DIR/deployment-monitor.log"
}

info() { log "INFO" "${BLUE}$*${NC}"; }
success() { log "SUCCESS" "${GREEN}$*${NC}"; }
warning() { log "WARNING" "${YELLOW}$*${NC}"; }
error() { log "ERROR" "${RED}$*${NC}"; }

# Banner
print_banner() {
    echo -e "${PURPLE}"
    echo "=============================================================================="
    echo "🚀 MY HIBACHI DEPLOYMENT MONITOR"
    echo "=============================================================================="
    echo -e "${NC}"
    echo "🕐 $(date)"
    echo "📍 Environment: ${ENVIRONMENT:-production}"
    echo "📂 Project Root: $PROJECT_ROOT"
    echo ""
}

# Health check functions
check_url() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    local timeout="${4:-$HEALTH_CHECK_TIMEOUT}"
    
    info "Checking $name at $url"
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$url"); then
        if [[ "$response" == "$expected_status" ]]; then
            success "✅ $name: HTTP $response (OK)"
            return 0
        else
            error "❌ $name: HTTP $response (Expected: $expected_status)"
            return 1
        fi
    else
        error "❌ $name: Connection failed (timeout: ${timeout}s)"
        return 1
    fi
}

check_api_health() {
    local base_url="$1"
    local app_name="$2"
    
    info "🔍 Checking $app_name API health..."
    
    # Basic health check
    if ! check_url "$app_name Health" "$base_url/health" "200"; then
        return 1
    fi
    
    # Configuration health check  
    if ! check_url "$app_name Config" "$base_url/health/config" "200"; then
        warning "⚠️ $app_name configuration health check failed (non-critical)"
    fi
    
    # API version check
    if response=$(curl -s --max-time 10 "$base_url/health/config"); then
        if app_version=$(echo "$response" | jq -r '.api_version // empty'); then
            if [[ -n "$app_version" ]]; then
                success "📋 $app_name Version: $app_version"
            fi
        fi
        
        if environment=$(echo "$response" | jq -r '.environment // empty'); then
            if [[ -n "$environment" ]]; then
                info "🌍 $app_name Environment: $environment"
            fi
        fi
    fi
    
    return 0
}

# Application monitoring functions
monitor_customer_frontend() {
    info "🛍️ Monitoring Customer Website (Next.js)"
    
    local urls=(
        "https://myhibachichef.com"
        "https://myhibachichef.com/api/health"
    )
    
    local failed=0
    for url in "${urls[@]}"; do
        if ! check_url "Customer Site" "$url"; then
            ((failed++))
        fi
    done
    
    if [[ $failed -eq 0 ]]; then
        success "✅ Customer Website: All endpoints healthy"
        return 0
    else
        error "❌ Customer Website: $failed/${{#urls[@]}} endpoints failed"
        return 1
    fi
}

monitor_admin_panel() {
    info "👥 Monitoring Admin Panel (Next.js)"
    
    local urls=(
        "https://admin.mysticdatanode.net"
        "https://admin.mysticdatanode.net/api/health"
    )
    
    local failed=0
    for url in "${urls[@]}"; do
        if ! check_url "Admin Panel" "$url"; then
            ((failed++))
        fi
    done
    
    if [[ $failed -eq 0 ]]; then
        success "✅ Admin Panel: All endpoints healthy"
        return 0
    else
        error "❌ Admin Panel: $failed/${#urls[@]} endpoints failed"
        return 1
    fi
}

monitor_backend_api() {
    info "🔧 Monitoring Backend API (FastAPI)"
    
    # Determine backend URL based on environment
    local backend_url="${BACKEND_URL:-https://api.myhibachichef.com}"
    
    if ! check_api_health "$backend_url" "Backend API"; then
        return 1
    fi
    
    # Additional FastAPI-specific checks
    info "🔍 Running FastAPI-specific health checks..."
    
    # Check OpenAPI docs
    if ! check_url "API Docs" "$backend_url/docs" "200"; then
        warning "⚠️ API documentation not accessible (non-critical)"
    fi
    
    # Check metrics endpoint (if available)
    if check_url "Metrics" "$backend_url/metrics" "200" 5; then
        success "📊 Metrics endpoint available"
    fi
    
    success "✅ Backend API: All critical endpoints healthy"
    return 0
}

# Database and external service checks
monitor_database() {
    info "🗄️ Monitoring Database Connectivity"
    
    # This would typically connect to the database
    # For now, we'll check if the backend can connect to it
    local backend_url="${BACKEND_URL:-https://api.myhibachichef.com}"
    
    if response=$(curl -s --max-time 10 "$backend_url/health/dependencies" 2>/dev/null); then
        if db_status=$(echo "$response" | jq -r '.dependencies.database.status // empty'); then
            if [[ "$db_status" == "healthy" ]]; then
                success "✅ Database: Connection healthy"
                return 0
            else
                error "❌ Database: Connection unhealthy ($db_status)"
                return 1
            fi
        fi
    fi
    
    warning "⚠️ Database: Health check inconclusive"
    return 1
}

monitor_redis() {
    info "📦 Monitoring Redis Connectivity"
    
    local backend_url="${BACKEND_URL:-https://api.myhibachichef.com}"
    
    if response=$(curl -s --max-time 10 "$backend_url/health/dependencies" 2>/dev/null); then
        if redis_status=$(echo "$response" | jq -r '.dependencies.redis.status // empty'); then
            if [[ "$redis_status" == "healthy" ]]; then
                success "✅ Redis: Connection healthy"
                return 0
            else
                error "❌ Redis: Connection unhealthy ($redis_status)"
                return 1
            fi
        fi
    fi
    
    warning "⚠️ Redis: Health check inconclusive"
    return 1
}

monitor_external_apis() {
    info "🌐 Monitoring External API Dependencies"
    
    local backend_url="${BACKEND_URL:-https://api.myhibachichef.com}"
    
    if response=$(curl -s --max-time 15 "$backend_url/health/dependencies" 2>/dev/null); then
        if apis=$(echo "$response" | jq -r '.dependencies.external_apis // empty'); then
            if [[ -n "$apis" ]]; then
                echo "$apis" | jq -r 'to_entries[] | "\(.key): \(.value.configured)"' | while read -r line; do
                    if [[ "$line" == *"true" ]]; then
                        success "✅ External API $line"
                    else
                        warning "⚠️ External API $line"
                    fi
                done
            fi
        fi
    else
        warning "⚠️ External APIs: Health check inconclusive"
    fi
}

# GSM and secret management monitoring
monitor_gsm_integration() {
    info "🔐 Monitoring GSM Secret Management"
    
    local backend_url="${BACKEND_URL:-https://api.myhibachichef.com}"
    
    if response=$(curl -s --max-time 10 "$backend_url/health/config" 2>/dev/null); then
        if gsm_available=$(echo "$response" | jq -r '.gsm_available // false'); then
            if [[ "$gsm_available" == "true" ]]; then
                if secrets_count=$(echo "$response" | jq -r '.secrets_count // 0'); then
                    success "✅ GSM Integration: $secrets_count secrets loaded"
                    return 0
                fi
            else
                warning "⚠️ GSM Integration: Not available, using environment variables"
                return 1
            fi
        fi
    fi
    
    error "❌ GSM Integration: Health check failed"
    return 1
}

# Deployment status monitoring
check_deployment_status() {
    info "🚀 Checking Recent Deployment Status"
    
    # Check GitHub Actions status (if GitHub CLI is available)
    if command -v gh >/dev/null 2>&1; then
        info "📊 Fetching GitHub Actions status..."
        
        if gh run list --limit 5 --json status,conclusion,workflowName,createdAt 2>/dev/null | \
           jq -r '.[] | "\(.createdAt | split("T")[0]) \(.workflowName): \(.status) (\(.conclusion // "running"))"'; then
            success "✅ GitHub Actions status retrieved"
        else
            warning "⚠️ Could not fetch GitHub Actions status"
        fi
    else
        info "💡 GitHub CLI not available, skipping Actions status"
    fi
}

# Feature flag monitoring
monitor_feature_flags() {
    info "🚩 Monitoring Feature Flags"
    
    local backend_url="${BACKEND_URL:-https://api.myhibachichef.com}"
    
    # This would require admin authentication in production
    warning "⚠️ Feature flag monitoring requires admin authentication (skipping for now)"
    
    # Placeholder for future implementation
    # if response=$(curl -s --max-time 10 "$backend_url/health/config/detailed" 2>/dev/null); then
    #     if flags=$(echo "$response" | jq -r '.feature_flags.enabled_flags[]? // empty'); then
    #         if [[ -n "$flags" ]]; then
    #             info "🚩 Enabled Feature Flags:"
    #             echo "$flags" | while read -r flag; do
    #                 info "   - $flag"
    #             done
    #         else
    #             info "🚩 No feature flags currently enabled"
    #         fi
    #     fi
    # fi
}

# Main monitoring function
run_health_checks() {
    local failed_checks=0
    local total_checks=0
    
    info "🏥 Starting comprehensive health checks..."
    echo ""
    
    # Frontend applications
    ((total_checks++))
    if ! monitor_customer_frontend; then
        ((failed_checks++))
    fi
    echo ""
    
    ((total_checks++))
    if ! monitor_admin_panel; then
        ((failed_checks++))
    fi
    echo ""
    
    # Backend API
    ((total_checks++))
    if ! monitor_backend_api; then
        ((failed_checks++))
    fi
    echo ""
    
    # Infrastructure
    ((total_checks++))
    if ! monitor_database; then
        ((failed_checks++))
    fi
    echo ""
    
    ((total_checks++))
    if ! monitor_redis; then
        ((failed_checks++))
    fi
    echo ""
    
    # External dependencies
    monitor_external_apis
    echo ""
    
    # Secret management
    monitor_gsm_integration
    echo ""
    
    # Deployment and feature monitoring
    check_deployment_status
    echo ""
    
    monitor_feature_flags
    echo ""
    
    # Summary
    echo -e "${PURPLE}=============================================================================="
    echo "📊 HEALTH CHECK SUMMARY"
    echo -e "==============================================================================${NC}"
    
    local success_rate=$(( (total_checks - failed_checks) * 100 / total_checks ))
    
    if [[ $failed_checks -eq 0 ]]; then
        success "🎉 ALL SYSTEMS HEALTHY ($total_checks/$total_checks checks passed)"
        echo -e "${GREEN}✅ System Status: OPERATIONAL${NC}"
    elif [[ $failed_checks -le 2 ]]; then
        warning "⚠️ MINOR ISSUES DETECTED ($((total_checks - failed_checks))/$total_checks checks passed)"
        echo -e "${YELLOW}⚠️ System Status: DEGRADED PERFORMANCE${NC}"
    else
        error "❌ CRITICAL ISSUES DETECTED ($((total_checks - failed_checks))/$total_checks checks passed)"
        echo -e "${RED}❌ System Status: MAJOR OUTAGE${NC}"
    fi
    
    echo ""
    echo "📈 Overall Health: $success_rate%"
    echo "📅 Check Time: $(date)"
    echo "📝 Detailed logs: $LOG_DIR/deployment-monitor.log"
    
    return $failed_checks
}

# Continuous monitoring mode
continuous_monitor() {
    local interval="${1:-300}"  # Default: 5 minutes
    
    info "🔄 Starting continuous monitoring (interval: ${interval}s)"
    info "Press Ctrl+C to stop"
    
    while true; do
        print_banner
        run_health_checks
        
        echo ""
        info "⏱️ Sleeping for ${interval}s..."
        sleep "$interval"
        clear
    done
}

# Main script logic
main() {
    local mode="${1:-single}"
    local interval="${2:-300}"
    
    print_banner
    
    case "$mode" in
        "single"|"once")
            run_health_checks
            exit $?
            ;;
        "continuous"|"watch")
            continuous_monitor "$interval"
            ;;
        "quick")
            info "🚀 Quick health check mode"
            monitor_customer_frontend
            monitor_admin_panel  
            monitor_backend_api
            ;;
        *)
            echo "Usage: $0 [single|continuous|quick] [interval_seconds]"
            echo ""
            echo "Modes:"
            echo "  single      - Run health checks once (default)"
            echo "  continuous  - Run health checks continuously"
            echo "  quick       - Quick check of main applications only"
            echo ""
            echo "Examples:"
            echo "  $0                    # Single run"
            echo "  $0 continuous 180    # Continuous monitoring every 3 minutes"
            echo "  $0 quick             # Quick check"
            exit 1
            ;;
    esac
}

# Handle interrupts gracefully
trap 'echo -e "\n${YELLOW}🛑 Monitoring stopped by user${NC}"; exit 0' INT TERM

# Run the script
main "$@"
