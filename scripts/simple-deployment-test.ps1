# Simple Deployment Test
Write-Host "🧪 Testing Deployment Readiness..." -ForegroundColor Cyan
Write-Host ""

$passed = 0
$total = 0

# Test 1: Project structure
Write-Host "🔍 Checking project structure..." -ForegroundColor Yellow
$total++
if ((Test-Path "apps\customer") -and (Test-Path "apps\admin") -and (Test-Path "apps\backend")) {
    Write-Host "  ✅ All app directories exist" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ❌ Missing app directories" -ForegroundColor Red
}

# Test 2: Scripts exist  
Write-Host "🔍 Checking monitoring scripts..." -ForegroundColor Yellow
$total++
if ((Test-Path "scripts\deployment-monitor.sh") -and (Test-Path "scripts\deployment-monitor.ps1")) {
    Write-Host "  ✅ Monitoring scripts exist" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ❌ Missing monitoring scripts" -ForegroundColor Red
}

# Test 3: GSM integration
Write-Host "🔍 Checking GSM integration..." -ForegroundColor Yellow
$total++
if (Test-Path "apps\backend\src\config\gsm_config.py") {
    Write-Host "  ✅ GSM config file exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ❌ Missing GSM config" -ForegroundColor Red
}

# Test 4: Workflows
Write-Host "🔍 Checking GitHub workflows..." -ForegroundColor Yellow
$total++
if ((Test-Path ".github\workflows\ci-deploy.yml") -and (Test-Path ".github\workflows\deployment-testing.yml")) {
    Write-Host "  ✅ Deployment workflows exist" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ❌ Missing workflow files" -ForegroundColor Red
}

# Test 5: Security
Write-Host "🔍 Checking .gitignore security..." -ForegroundColor Yellow
$total++
$gitignoreContent = Get-Content ".gitignore" -ErrorAction SilentlyContinue
if ($gitignoreContent -and ($gitignoreContent -match "secret" -or $gitignoreContent -match "gsm")) {
    Write-Host "  ✅ .gitignore has secret protections" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ❌ .gitignore missing secret protections" -ForegroundColor Red
}

# Summary
Write-Host ""
Write-Host "=" * 50 -ForegroundColor Cyan
Write-Host "📊 RESULTS: $passed/$total tests passed" -ForegroundColor Cyan

if ($passed -eq $total) {
    Write-Host "🎉 DEPLOYMENT READY!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Test monitoring: .\scripts\deployment-monitor.ps1 -Mode quick"
    Write-Host "  2. Run GitHub Actions: deployment-testing.yml" 
    Write-Host "  3. Deploy: ci-deploy.yml"
    exit 0
} elseif ($passed -ge ($total * 0.8)) {
    Write-Host "⚠️  MOSTLY READY (minor issues)" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "❌ NOT READY (critical issues)" -ForegroundColor Red
    exit 1
}
