#!/usr/bin/env bash
# My Hibachi Secret Rotation Script
# Usage: ./rotate-secret.sh prod-global-STRIPE_SECRET_KEY

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

usage() {
    cat << EOF
My Hibachi Secret Rotation Tool

Usage: $0 [OPTIONS] <SECRET_ID>

Examples:
  $0 prod-global-STRIPE_SECRET_KEY
  $0 prod-backend-api-DB_URL
  $0 --interactive prod-global-OPENAI_API_KEY
  $0 --from-file secrets.json prod-global-CONFIG_VERSION

Arguments:
  SECRET_ID       GSM secret ID (format: {env}-{service}-{KEY_NAME})

Options:
  -i, --interactive     Prompt for new value interactively
  -f, --from-file FILE  Read new value from file
  -e, --env ENV         Override environment detection (dev/stg/prod)
  -v, --verify          Verify rotation by testing secret access
  --dry-run             Show what would be done without making changes
  --backup              Create backup of old secret version
  -h, --help            Show this help

Supported Secret Patterns:
  prod-global-*         Global secrets (Stripe, OpenAI, Maps, etc.)
  prod-backend-api-*    Backend API secrets (DB, JWT, etc.)
  prod-backend-ai-*     AI backend secrets (Vector DB, etc.)
  prod-frontend-web-*   Customer frontend secrets
  prod-frontend-admin-* Admin frontend secrets

Environment Setup Required:
  - gcloud CLI installed and authenticated
  - GCP_PROJECT_ID environment variable set
  - Appropriate GSM permissions

Examples of Common Rotations:
  # Rotate Stripe secret key
  $0 --interactive prod-global-STRIPE_SECRET_KEY
  
  # Rotate database URL
  $0 prod-backend-api-DB_URL
  
  # Rotate OpenAI API key
  $0 prod-global-OPENAI_API_KEY
  
  # Increment config version (triggers reload)
  $0 prod-global-CONFIG_VERSION

EOF
}

# Parse command line arguments
INTERACTIVE=false
FROM_FILE=""
VERIFY=false
DRY_RUN=false
BACKUP=false
OVERRIDE_ENV=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--interactive)
            INTERACTIVE=true
            shift
            ;;
        -f|--from-file)
            FROM_FILE="$2"
            shift 2
            ;;
        -e|--env)
            OVERRIDE_ENV="$2"
            shift 2
            ;;
        -v|--verify)
            VERIFY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --backup)
            BACKUP=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*|--*)
            log_error "Unknown option $1"
            usage
            exit 1
            ;;
        *)
            SECRET_ID="$1"
            shift
            ;;
    esac
done

# Validate inputs
if [[ -z "${SECRET_ID:-}" ]]; then
    log_error "SECRET_ID is required"
    usage
    exit 1
fi

if [[ -z "${GCP_PROJECT_ID:-}" ]]; then
    log_error "GCP_PROJECT_ID environment variable must be set"
    exit 1
fi

# Validate secret ID format
if [[ ! "$SECRET_ID" =~ ^(dev|stg|prod)-(global|backend-api|backend-ai|frontend-web|frontend-admin)-[A-Z_]+$ ]]; then
    log_error "Invalid secret ID format: $SECRET_ID"
    log_error "Expected format: {env}-{service}-{KEY_NAME}"
    log_error "Example: prod-global-STRIPE_SECRET_KEY"
    exit 1
fi

# Extract components from secret ID
IFS='-' read -ra PARTS <<< "$SECRET_ID"
ENV="${PARTS[0]}"
SERVICE="${PARTS[1]}"
KEY_NAME="${PARTS[2]}"

# Override environment if specified
if [[ -n "$OVERRIDE_ENV" ]]; then
    ENV="$OVERRIDE_ENV"
fi

log_info "Starting rotation for secret: $SECRET_ID"
log_info "Environment: $ENV"
log_info "Service: $SERVICE"  
log_info "Key: $KEY_NAME"

# Check if secret exists
log_info "Checking if secret exists in GSM..."
if ! gcloud secrets describe "$SECRET_ID" --project="$GCP_PROJECT_ID" &>/dev/null; then
    log_error "Secret $SECRET_ID does not exist in project $GCP_PROJECT_ID"
    log_info "Create it first with: gcloud secrets create $SECRET_ID --project=$GCP_PROJECT_ID"
    exit 1
fi

# Backup current version if requested
if [[ "$BACKUP" == "true" ]]; then
    log_info "Creating backup of current secret version..."
    BACKUP_DIR="$PROJECT_ROOT/backups/secrets/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    if gcloud secrets versions access latest --secret="$SECRET_ID" --project="$GCP_PROJECT_ID" > "$BACKUP_DIR/${SECRET_ID}.backup" 2>/dev/null; then
        log_success "Backup saved to: $BACKUP_DIR/${SECRET_ID}.backup"
    else
        log_warning "Could not create backup (secret may be empty)"
    fi
fi

# Get new secret value
NEW_VALUE=""

if [[ -n "$FROM_FILE" ]]; then
    log_info "Reading new value from file: $FROM_FILE"
    if [[ ! -f "$FROM_FILE" ]]; then
        log_error "File not found: $FROM_FILE"
        exit 1
    fi
    NEW_VALUE="$(cat "$FROM_FILE")"
    
elif [[ "$INTERACTIVE" == "true" ]]; then
    log_info "Enter new value for $SECRET_ID:"
    
    # Special handling for different secret types
    case "$KEY_NAME" in
        *PASSWORD*|*SECRET*|*KEY*)
            echo -n "New value (hidden): "
            read -s NEW_VALUE
            echo
            ;;
        CONFIG_VERSION)
            # Auto-increment config version
            CURRENT_VERSION="$(gcloud secrets versions access latest --secret="$SECRET_ID" --project="$GCP_PROJECT_ID" 2>/dev/null || echo "0")"
            NEW_VERSION=$((CURRENT_VERSION + 1))
            log_info "Current CONFIG_VERSION: $CURRENT_VERSION"
            log_info "New CONFIG_VERSION will be: $NEW_VERSION"
            read -p "Proceed with increment? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Rotation cancelled"
                exit 0
            fi
            NEW_VALUE="$NEW_VERSION"
            ;;
        *)
            echo -n "New value: "
            read NEW_VALUE
            ;;
    esac
else
    log_error "Must specify either --interactive or --from-file"
    exit 1
fi

# Validate new value
if [[ -z "$NEW_VALUE" ]]; then
    log_error "New value cannot be empty"
    exit 1
fi

# Show what will be done
if [[ "$DRY_RUN" == "true" ]]; then
    log_info "DRY RUN - Would perform these actions:"
    log_info "1. Add new version to secret: $SECRET_ID"
    log_info "2. New value length: ${#NEW_VALUE} characters"
    if [[ "$VERIFY" == "true" ]]; then
        log_info "3. Verify secret access"
    fi
    log_info "4. Trigger config reload (if CONFIG_VERSION)"
    exit 0
fi

# Rotate the secret
log_info "Adding new version to secret: $SECRET_ID"

# Create temporary file for secret value
TMP_FILE="$(mktemp)"
trap "rm -f '$TMP_FILE'" EXIT

echo -n "$NEW_VALUE" > "$TMP_FILE"

if gcloud secrets versions add "$SECRET_ID" --data-file="$TMP_FILE" --project="$GCP_PROJECT_ID"; then
    log_success "Secret rotated successfully: $SECRET_ID"
else
    log_error "Failed to rotate secret: $SECRET_ID"
    exit 1
fi

# Verify the rotation if requested
if [[ "$VERIFY" == "true" ]]; then
    log_info "Verifying secret access..."
    sleep 2  # Give GSM a moment to propagate
    
    if RETRIEVED_VALUE="$(gcloud secrets versions access latest --secret="$SECRET_ID" --project="$GCP_PROJECT_ID" 2>/dev/null)"; then
        if [[ "$RETRIEVED_VALUE" == "$NEW_VALUE" ]]; then
            log_success "Verification passed: secret value matches"
        else
            log_error "Verification failed: retrieved value doesn't match"
            exit 1
        fi
    else
        log_error "Verification failed: could not retrieve secret"
        exit 1
    fi
fi

# Auto-increment CONFIG_VERSION if this was a critical secret
CRITICAL_SECRETS=("STRIPE_SECRET_KEY" "OPENAI_API_KEY" "DB_URL" "JWT_SECRET")
for critical in "${CRITICAL_SECRETS[@]}"; do
    if [[ "$KEY_NAME" == "$critical" ]]; then
        log_info "Critical secret changed, incrementing CONFIG_VERSION..."
        CONFIG_VERSION_SECRET="${ENV}-global-CONFIG_VERSION"
        
        if "$0" --interactive "$CONFIG_VERSION_SECRET"; then
            log_success "CONFIG_VERSION incremented"
        else
            log_warning "Failed to increment CONFIG_VERSION - you may need to do this manually"
        fi
        break
    fi
done

# Show post-rotation instructions
cat << EOF

${GREEN}✅ Secret rotation completed successfully!${NC}

Secret: $SECRET_ID
Project: $GCP_PROJECT_ID
Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

📋 Next Steps:
EOF

case "$SERVICE" in
    "backend-api"|"backend-ai")
        echo "1. 🔄 Backend services will reload config automatically (if CONFIG_VERSION changed)"
        echo "2. 🔍 Monitor logs: docker logs my-hibachi-backend"
        echo "3. 🧪 Test API endpoints to verify functionality"
        ;;
    "frontend-web"|"frontend-admin")
        echo "1. 🚀 Trigger GitHub Action: sync-gsm-to-vercel.yml" 
        echo "2. 🌐 Verify Vercel deployment: vercel env ls"
        echo "3. 🧪 Test frontend functionality"
        ;;
    "global")
        echo "1. 🔄 All services will reload (CONFIG_VERSION updated)"
        echo "2. 🔍 Monitor all service logs"
        echo "3. 🧪 Test critical workflows end-to-end"
        ;;
esac

echo "4. 🗑️  Consider deactivating old secret version after verification"
echo "5. 📊 Update documentation/runbook with rotation details"
echo ""
echo "🔍 Monitor secret usage:"
echo "   gcloud secrets versions list $SECRET_ID --project=$GCP_PROJECT_ID"
echo ""
echo "🗑️  Disable old version (after testing):"
echo "   gcloud secrets versions disable [VERSION] --secret=$SECRET_ID --project=$GCP_PROJECT_ID"

log_success "Rotation completed!"
