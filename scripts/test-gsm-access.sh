#!/usr/bin/env bash
# Test script to verify GSM access
# Run this after setting up secrets in Google Cloud Console

set -euo pipefail

echo "🧪 Testing Google Secret Manager Access"
echo "======================================"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check authentication
echo "🔐 Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
    echo "❌ Not authenticated with gcloud"
    echo "Run: gcloud auth login"
    exit 1
fi

echo "✅ Authentication OK"

# Get project ID
PROJECT_ID="${GCP_PROJECT_ID:-}"
if [[ -z "$PROJECT_ID" ]]; then
    PROJECT_ID="$(gcloud config get-value project 2>/dev/null || echo "")"
fi

if [[ -z "$PROJECT_ID" ]]; then
    echo "❌ No GCP project set"
    echo "Set with: export GCP_PROJECT_ID=your-project-id"
    echo "Or run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "🏗️ Using project: $PROJECT_ID"

# Test secrets we expect to exist
TEST_SECRETS=(
    "prod-global-CONFIG_VERSION"
    "prod-global-STRIPE_SECRET_KEY"
    "prod-global-OPENAI_API_KEY"
    "prod-backend-api-JWT_SECRET"
    "prod-backend-api-DB_URL"
    "prod-frontend-web-NEXT_PUBLIC_API_URL"
)

echo ""
echo "📡 Testing secret access..."

success_count=0
total_count=${#TEST_SECRETS[@]}

for secret in "${TEST_SECRETS[@]}"; do
    echo -n "Testing $secret... "
    
    if gcloud secrets versions access latest --secret="$secret" --project="$PROJECT_ID" >/dev/null 2>&1; then
        echo "✅ OK"
        ((success_count++))
    else
        echo "❌ FAILED"
        echo "   Create this secret in Google Cloud Console:"
        echo "   Name: $secret"
        echo "   Value: [your-secret-value]"
    fi
done

echo ""
echo "📊 Results: $success_count/$total_count secrets accessible"

if [[ $success_count -eq $total_count ]]; then
    echo "🎉 All secrets are accessible! GSM setup is complete."
    echo ""
    echo "Next steps:"
    echo "1. Run the service test: cd tests/production && python quick_service_test.py"
    echo "2. Test variable management: visit /superadmin/variables"
    echo "3. Try secret rotation: ./scripts/rotate-secret.sh --interactive prod-global-CONFIG_VERSION"
elif [[ $success_count -gt 0 ]]; then
    echo "⚠️ Partial setup complete. Create the missing secrets above."
else
    echo "❌ No secrets found. Create secrets in Google Cloud Console first."
    echo ""
    echo "Secret naming pattern:"
    echo "  prod-global-*         (shared secrets)"
    echo "  prod-backend-api-*    (backend secrets)"  
    echo "  prod-frontend-web-*   (customer frontend)"
    echo "  prod-frontend-admin-* (admin frontend)"
fi

echo ""
echo "🔗 Manage secrets at:"
echo "https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
