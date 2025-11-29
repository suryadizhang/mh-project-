# My Hibachi - GSM Secrets Creation PowerShell Script (TEMPLATE)
# ================================================================
# INSTRUCTIONS:
# 1. Copy this file to: create-gsm-secrets-win.ps1
# 2. Replace all <PLACEHOLDER> values with real credentials
# 3. NEVER commit the real file to git!
# ================================================================

$PROJECT_ID = "my-hibachi-crm"
$GCLOUD = "C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

Write-Host "🚀 Creating all 23 secrets for My Hibachi..." -ForegroundColor Green

# ================================================================
# Global Secrets (Shared across all services)
# ================================================================
Write-Host "Creating global secrets..." -ForegroundColor Yellow

echo "1" | & $GCLOUD secrets create prod-global-CONFIG_VERSION --data-file=- --project=$PROJECT_ID
echo "<STRIPE_SECRET_KEY>" | & $GCLOUD secrets create prod-global-STRIPE_SECRET_KEY --data-file=- --project=$PROJECT_ID
echo "<OPENAI_API_KEY>" | & $GCLOUD secrets create prod-global-OPENAI_API_KEY --data-file=- --project=$PROJECT_ID
echo "<GOOGLE_MAPS_SERVER_KEY>" | & $GCLOUD secrets create prod-global-GOOGLE_MAPS_SERVER_KEY --data-file=- --project=$PROJECT_ID

# ================================================================
# Backend Secrets
# ================================================================
Write-Host "Creating backend secrets..." -ForegroundColor Yellow

# Generate random keys (keep these as-is)
$jwtSecret = openssl rand -hex 32
$encryptionKey = openssl rand -hex 32

echo $jwtSecret | & $GCLOUD secrets create prod-backend-api-JWT_SECRET --data-file=- --project=$PROJECT_ID
echo $encryptionKey | & $GCLOUD secrets create prod-backend-api-ENCRYPTION_KEY --data-file=- --project=$PROJECT_ID
echo "<DATABASE_URL>" | & $GCLOUD secrets create prod-backend-api-DB_URL --data-file=- --project=$PROJECT_ID
echo "redis://localhost:6379/0" | & $GCLOUD secrets create prod-backend-api-REDIS_URL --data-file=- --project=$PROJECT_ID
echo "<RINGCENTRAL_CLIENT_ID>" | & $GCLOUD secrets create prod-backend-api-RC_CLIENT_ID --data-file=- --project=$PROJECT_ID
echo "<RINGCENTRAL_CLIENT_SECRET>" | & $GCLOUD secrets create prod-backend-api-RC_CLIENT_SECRET --data-file=- --project=$PROJECT_ID
echo "<DEEPGRAM_API_KEY>" | & $GCLOUD secrets create prod-backend-api-DEEPGRAM_API_KEY --data-file=- --project=$PROJECT_ID
echo "<SMTP_PASSWORD>" | & $GCLOUD secrets create prod-backend-api-SMTP_PASSWORD --data-file=- --project=$PROJECT_ID
echo "<GMAIL_APP_PASSWORD>" | & $GCLOUD secrets create prod-backend-api-GMAIL_APP_PASSWORD --data-file=- --project=$PROJECT_ID

# ================================================================
# Frontend Web Secrets
# ================================================================
Write-Host "Creating frontend web secrets..." -ForegroundColor Yellow

echo "https://mhapi.mysticdatanode.net" | & $GCLOUD secrets create prod-frontend-web-NEXT_PUBLIC_API_URL --data-file=- --project=$PROJECT_ID
echo "https://myhibachichef.com" | & $GCLOUD secrets create prod-frontend-web-NEXT_PUBLIC_APP_URL --data-file=- --project=$PROJECT_ID
echo "<STRIPE_PUBLISHABLE_KEY>" | & $GCLOUD secrets create prod-frontend-web-NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY --data-file=- --project=$PROJECT_ID
echo "<GOOGLE_MAPS_API_KEY>" | & $GCLOUD secrets create prod-frontend-web-NEXT_PUBLIC_GOOGLE_MAPS_API_KEY --data-file=- --project=$PROJECT_ID
echo "<BUSINESS_PHONE>" | & $GCLOUD secrets create prod-frontend-web-NEXT_PUBLIC_BUSINESS_PHONE --data-file=- --project=$PROJECT_ID
echo "<BUSINESS_EMAIL>" | & $GCLOUD secrets create prod-frontend-web-NEXT_PUBLIC_BUSINESS_EMAIL --data-file=- --project=$PROJECT_ID
echo "<ZELLE_EMAIL>" | & $GCLOUD secrets create prod-frontend-web-NEXT_PUBLIC_ZELLE_EMAIL --data-file=- --project=$PROJECT_ID

# ================================================================
# Frontend Admin Secrets
# ================================================================
Write-Host "Creating frontend admin secrets..." -ForegroundColor Yellow

echo "https://mhapi.mysticdatanode.net" | & $GCLOUD secrets create prod-frontend-admin-NEXT_PUBLIC_API_URL --data-file=- --project=$PROJECT_ID
echo "https://admin.mysticdatanode.net" | & $GCLOUD secrets create prod-frontend-admin-NEXT_PUBLIC_APP_URL --data-file=- --project=$PROJECT_ID
echo "<STRIPE_PUBLISHABLE_KEY>" | & $GCLOUD secrets create prod-frontend-admin-NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY --data-file=- --project=$PROJECT_ID

Write-Host "✅ All 23 secrets created successfully!" -ForegroundColor Green
Write-Host "🧪 Testing access to first secret..." -ForegroundColor Blue
& $GCLOUD secrets versions access latest --secret="prod-global-CONFIG_VERSION" --project=$PROJECT_ID

Write-Host "🎉 Bulk upload complete!" -ForegroundColor Green
