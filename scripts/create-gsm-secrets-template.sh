#!/bin/bash

# My Hibachi - GSM Secrets Creation Template Script
# This is a TEMPLATE file - replace ALL placeholder values with real secrets
# Run: bash scripts/create-gsm-secrets-template.sh

PROJECT_ID="my-hibachi-crm"
GCLOUD="/path/to/gcloud"  # Update this path

echo "🚀 Creating all secrets for My Hibachi with TEMPLATE values..."
echo "⚠️ IMPORTANT: Replace all placeholder values with real secrets before running!"

# Global Secrets (Shared across all services)
echo "Creating global secrets..."
"$GCLOUD" secrets create prod-global-CONFIG_VERSION --data-file=<(echo -n "1") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-global-STRIPE_SECRET_KEY --data-file=<(echo -n "sk_test_YOUR_STRIPE_SECRET_KEY_HERE") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-global-OPENAI_API_KEY --data-file=<(echo -n "sk-proj-YOUR_OPENAI_API_KEY_HERE") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-global-GOOGLE_MAPS_SERVER_KEY --data-file=<(echo -n "AIza_YOUR_GOOGLE_MAPS_SERVER_KEY_HERE") --project=$PROJECT_ID

# Backend Secrets (API & Database)
echo "Creating backend secrets..."
"$GCLOUD" secrets create prod-backend-api-JWT_SECRET --data-file=<(echo -n "$(openssl rand -hex 32)") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-backend-api-ENCRYPTION_KEY --data-file=<(echo -n "$(openssl rand -hex 32)") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-backend-api-DB_URL --data-file=<(echo -n "postgresql+asyncpg://user:password@host:5432/database") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-backend-api-REDIS_URL --data-file=<(echo -n "redis://localhost:6379/0") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-backend-api-RC_CLIENT_ID --data-file=<(echo -n "YOUR_RINGCENTRAL_CLIENT_ID") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-backend-api-RC_CLIENT_SECRET --data-file=<(echo -n "YOUR_RINGCENTRAL_CLIENT_SECRET") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-backend-api-DEEPGRAM_API_KEY --data-file=<(echo -n "YOUR_DEEPGRAM_API_KEY") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-backend-api-SMTP_PASSWORD --data-file=<(echo -n "YOUR_SMTP_PASSWORD") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-backend-api-GMAIL_APP_PASSWORD --data-file=<(echo -n "YOUR_GMAIL_APP_PASSWORD") --project=$PROJECT_ID

# Frontend Web Secrets
echo "Creating frontend web secrets..."
"$GCLOUD" secrets create prod-frontend-web-NEXT_PUBLIC_API_URL --data-file=<(echo -n "https://api.yourdomain.com") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-frontend-web-NEXT_PUBLIC_APP_URL --data-file=<(echo -n "https://yourdomain.com") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-frontend-web-NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY --data-file=<(echo -n "pk_test_YOUR_STRIPE_PUBLISHABLE_KEY_HERE") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-frontend-web-NEXT_PUBLIC_GOOGLE_MAPS_API_KEY --data-file=<(echo -n "AIza_YOUR_GOOGLE_MAPS_CLIENT_KEY_HERE") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-frontend-web-NEXT_PUBLIC_BUSINESS_PHONE --data-file=<(echo -n "YOUR_BUSINESS_PHONE") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-frontend-web-NEXT_PUBLIC_BUSINESS_EMAIL --data-file=<(echo -n "YOUR_BUSINESS_EMAIL") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-frontend-web-NEXT_PUBLIC_ZELLE_EMAIL --data-file=<(echo -n "YOUR_ZELLE_EMAIL") --project=$PROJECT_ID

# Frontend Admin Secrets
echo "Creating frontend admin secrets..."
"$GCLOUD" secrets create prod-frontend-admin-NEXT_PUBLIC_API_URL --data-file=<(echo -n "https://api.yourdomain.com") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-frontend-admin-NEXT_PUBLIC_APP_URL --data-file=<(echo -n "https://admin.yourdomain.com") --project=$PROJECT_ID
"$GCLOUD" secrets create prod-frontend-admin-NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY --data-file=<(echo -n "pk_test_YOUR_STRIPE_PUBLISHABLE_KEY_HERE") --project=$PROJECT_ID

echo "✅ All secrets created with TEMPLATE values!"
echo "🧪 Testing access to first secret..."
"$GCLOUD" secrets versions access latest --secret="prod-global-CONFIG_VERSION" --project=$PROJECT_ID

echo "🎉 Template setup complete!"
echo ""
echo "⚠️ IMPORTANT NEXT STEPS:"
echo "1. Replace ALL placeholder values with real secrets"
echo "2. Test in development environment first"
echo "3. Update gcloud path at the top of this script"
