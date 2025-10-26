# 🚀 DEPLOYMENT EXECUTION SCRIPT
# Run this step-by-step to deploy the Customer Review & QR Tracking System

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MY HIBACHI CHEF - DEPLOYMENT SCRIPT" -ForegroundColor Cyan
Write-Host "Customer Review & QR Tracking System" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"
$baseDir = "C:\Users\surya\projects\MH webapps"

# Phase 1: Pre-Flight Checks
Write-Host "`n[PHASE 1] Pre-Flight Checks..." -ForegroundColor Yellow

Set-Location $baseDir

# Check if virtual environment exists
if (-Not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Virtual environment found" -ForegroundColor Green

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Cyan
& ".\.venv\Scripts\Activate.ps1"

# Check Python version
$pythonVersion = & python --version
Write-Host "✅ $pythonVersion" -ForegroundColor Green

# Check if dependencies are installed
Write-Host "`nChecking Python dependencies..." -ForegroundColor Cyan
$dependencies = @("fastapi", "sqlalchemy", "alembic", "user-agents")
foreach ($dep in $dependencies) {
    $installed = & python -c "import $($dep.Replace('-', '_')); print('installed')" 2>$null
    if ($installed -eq "installed") {
        Write-Host "✅ $dep installed" -ForegroundColor Green
    } else {
        Write-Host "❌ $dep NOT installed" -ForegroundColor Red
        Write-Host "Installing missing dependencies..." -ForegroundColor Yellow
        Set-Location "$baseDir\apps\backend"
        & pip install -r requirements.txt
        break
    }
}

# Check Node.js and frontend dependencies
Write-Host "`nChecking Node.js dependencies..." -ForegroundColor Cyan
Set-Location "$baseDir\apps\customer"

$nodeVersion = & node --version 2>$null
if ($nodeVersion) {
    Write-Host "✅ Node.js $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Node.js not found!" -ForegroundColor Red
    exit 1
}

$packageCheck = & npm list framer-motion react-confetti --depth=0 2>&1
if ($packageCheck -match "framer-motion@" -and $packageCheck -match "react-confetti@") {
    Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some frontend dependencies missing, installing..." -ForegroundColor Yellow
    & npm install
}

# Phase 2: Database Backup
Write-Host "`n[PHASE 2] Database Backup..." -ForegroundColor Yellow

$backupDate = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "$baseDir\backups\backup_pre_reviews_$backupDate.sql"

Write-Host "`n⚠️  IMPORTANT: Backup your database before proceeding!" -ForegroundColor Yellow
Write-Host "Backup location: $backupFile" -ForegroundColor Cyan

$backup = Read-Host "`nHave you backed up your database? (yes/no)"
if ($backup -ne "yes") {
    Write-Host "`n❌ Please backup your database first!" -ForegroundColor Red
    Write-Host "`nBackup command example:" -ForegroundColor Yellow
    Write-Host "pg_dump -U postgres -d myhibachi -F c -b -v -f '$backupFile'" -ForegroundColor Cyan
    exit 1
}

Write-Host "✅ Database backup confirmed" -ForegroundColor Green

# Phase 3: Run Database Migrations
Write-Host "`n[PHASE 3] Database Migrations..." -ForegroundColor Yellow

Set-Location "$baseDir\apps\backend"

Write-Host "`nChecking current migration status..." -ForegroundColor Cyan
& alembic current

Write-Host "`n⚠️  About to run migrations 004 and 005:" -ForegroundColor Yellow
Write-Host "  - Migration 004: Customer Review System (feedback schema)" -ForegroundColor Cyan
Write-Host "  - Migration 005: QR Code Tracking (marketing schema)" -ForegroundColor Cyan

$migrate = Read-Host "`nProceed with migrations? (yes/no)"
if ($migrate -ne "yes") {
    Write-Host "`n❌ Migration cancelled" -ForegroundColor Red
    exit 1
}

Write-Host "`nRunning migrations..." -ForegroundColor Cyan
try {
    & alembic upgrade head
    Write-Host "✅ Migrations completed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Migration failed: $_" -ForegroundColor Red
    Write-Host "`nRollback command:" -ForegroundColor Yellow
    Write-Host "alembic downgrade -1" -ForegroundColor Cyan
    exit 1
}

# Verify tables created
Write-Host "`nVerifying database schema..." -ForegroundColor Cyan
$verification = & python -c @"
from sqlalchemy import create_engine, inspect
from api.app.config import settings

engine = create_engine(settings.database_url.replace('postgresql+asyncpg', 'postgresql'))
inspector = inspect(engine)

try:
    feedback_tables = inspector.get_table_names(schema='feedback')
    marketing_tables = inspector.get_table_names(schema='marketing')
    
    if 'customer_reviews' in feedback_tables and 'qr_codes' in marketing_tables:
        print('SUCCESS')
    else:
        print('MISSING_TABLES')
except Exception as e:
    print(f'ERROR: {e}')
"@

if ($verification -eq "SUCCESS") {
    Write-Host "✅ Database schema verified" -ForegroundColor Green
} else {
    Write-Host "❌ Schema verification failed: $verification" -ForegroundColor Red
    exit 1
}

# Phase 4: Backend Testing
Write-Host "`n[PHASE 4] Backend Testing..." -ForegroundColor Yellow

Write-Host "`nStarting backend server for testing..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server after testing`n" -ForegroundColor Yellow

$testServer = Read-Host "Start backend server for testing? (yes/no)"
if ($testServer -eq "yes") {
    Write-Host "`nStarting server on http://localhost:8000..." -ForegroundColor Cyan
    Write-Host "Visit http://localhost:8000/docs to test endpoints" -ForegroundColor Yellow
    Write-Host "Press Ctrl+C when done testing`n" -ForegroundColor Yellow
    
    & uvicorn api.app.main:app --reload --port 8000
}

# Phase 5: Frontend Build
Write-Host "`n[PHASE 5] Frontend Build..." -ForegroundColor Yellow

Set-Location "$baseDir\apps\customer"

Write-Host "`nBuilding production frontend..." -ForegroundColor Cyan
try {
    & npm run build
    Write-Host "✅ Frontend build successful!" -ForegroundColor Green
} catch {
    Write-Host "❌ Frontend build failed: $_" -ForegroundColor Red
    exit 1
}

# Phase 6: Final Checklist
Write-Host "`n[PHASE 6] Final Checklist..." -ForegroundColor Yellow

$checklist = @(
    "Environment variables configured in .env",
    "RingCentral SMS credentials set",
    "YELP_REVIEW_URL and GOOGLE_REVIEW_URL configured",
    "Customer review worker cron job scheduled",
    "SSL certificates installed for production",
    "DNS records pointing to new deployment",
    "Monitoring/alerting configured (Sentry, etc.)",
    "Backup strategy in place"
)

Write-Host "`nPre-Deployment Checklist:" -ForegroundColor Cyan
foreach ($item in $checklist) {
    Write-Host "  ☐ $item" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT PREPARATION COMPLETE!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Review the checklist above" -ForegroundColor Cyan
Write-Host "2. Test all endpoints at http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "3. Test frontend at http://localhost:3000" -ForegroundColor Cyan
Write-Host "4. Deploy to production when ready" -ForegroundColor Cyan
Write-Host "5. Monitor logs for the first 24 hours`n" -ForegroundColor Cyan

Write-Host "📚 Documentation:" -ForegroundColor Yellow
Write-Host "  - PRE_DEPLOYMENT_CHECKLIST.md (comprehensive guide)" -ForegroundColor Cyan
Write-Host "  - CUSTOMER_REVIEW_SYSTEM_COMPLETE.md (review system docs)" -ForegroundColor Cyan
Write-Host "  - QR_CODE_TRACKING_COMPLETE.md (QR tracking docs)`n" -ForegroundColor Cyan

Write-Host "🎉 Ready to deploy!" -ForegroundColor Green
