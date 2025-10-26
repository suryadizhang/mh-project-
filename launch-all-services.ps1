# 🚀 Launch All Services - Production Testing Script
# Run this to open 3 separate terminal windows for Backend, Customer, Admin

Write-Host "🚀 My Hibachi Chef - Production Testing Launcher" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$workspaceRoot = "C:\Users\surya\projects\MH webapps"

# Terminal 1: Backend API (Port 8000)
Write-Host "📡 Launching Terminal 1: Backend API (Port 8000)..." -ForegroundColor Green
$backend = @"
Set-Location '$workspaceRoot\apps\backend'
Write-Host '🔧 Backend API Server' -ForegroundColor Cyan
Write-Host '==================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Activating Python virtual environment...' -ForegroundColor Yellow
& '$workspaceRoot\.venv\Scripts\Activate.ps1'
Write-Host ''
Write-Host 'Starting uvicorn server on port 8000...' -ForegroundColor Yellow
Write-Host 'API Docs: http://localhost:8000/docs' -ForegroundColor Magenta
Write-Host 'Health: http://localhost:8000/api/health' -ForegroundColor Magenta
Write-Host ''
uvicorn api.app.main:app --reload --port 8000 --host 0.0.0.0
"@
Start-Process pwsh -ArgumentList "-NoExit", "-Command", $backend

Start-Sleep -Seconds 2

# Terminal 2: Customer Frontend (Port 3000)
Write-Host "🌐 Launching Terminal 2: Customer Frontend (Port 3000)..." -ForegroundColor Green
$customer = @"
Set-Location '$workspaceRoot\apps\customer'
Write-Host '👥 Customer Frontend' -ForegroundColor Cyan
Write-Host '==================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Starting Next.js development server...' -ForegroundColor Yellow
Write-Host 'Homepage: http://localhost:3000' -ForegroundColor Magenta
Write-Host 'Review Test: http://localhost:3000/review/test-id' -ForegroundColor Magenta
Write-Host 'QR Redirect: http://localhost:3000/contact.html' -ForegroundColor Magenta
Write-Host ''
npm run dev
"@
Start-Process pwsh -ArgumentList "-NoExit", "-Command", $customer

Start-Sleep -Seconds 2

# Terminal 3: Admin Frontend (Port 3001)
Write-Host "👨‍💼 Launching Terminal 3: Admin Frontend (Port 3001)..." -ForegroundColor Green
$admin = @"
Set-Location '$workspaceRoot\apps\admin'
Write-Host '⚙️ Admin Frontend' -ForegroundColor Cyan
Write-Host '==================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Starting Next.js development server...' -ForegroundColor Yellow
Write-Host 'Dashboard: http://localhost:3001' -ForegroundColor Magenta
Write-Host ''
npm run dev
"@
Start-Process pwsh -ArgumentList "-NoExit", "-Command", $admin

Write-Host ""
Write-Host "✅ All 3 terminals launched!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Quick Reference:" -ForegroundColor Yellow
Write-Host "  Backend API:       http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Customer Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  Admin Frontend:    http://localhost:3001" -ForegroundColor White
Write-Host ""
Write-Host "⏱️ Please wait 10-15 seconds for all services to start..." -ForegroundColor Yellow
Write-Host ""
Write-Host "🧪 Testing Checklist:" -ForegroundColor Cyan
Write-Host "  [ ] Backend health check: http://localhost:8000/api/health" -ForegroundColor White
Write-Host "  [ ] Customer homepage loads" -ForegroundColor White
Write-Host "  [ ] Admin dashboard loads" -ForegroundColor White
Write-Host "  [ ] Test review page: http://localhost:3000/review/test-id" -ForegroundColor White
Write-Host "  [ ] Test QR redirect: http://localhost:3000/contact.html" -ForegroundColor White
Write-Host ""
Write-Host "📄 Full details in: PRODUCTION_READINESS_REPORT.md" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop all services (close each terminal window)" -ForegroundColor Gray
