# 🧪 E2E Testing Quick Start Script
# This script helps you run E2E tests for MyHibachi

Write-Host "🍤 MyHibachi E2E Testing Suite" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if service is running
function Test-ServiceRunning {
    param($Port, $ServiceName)
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$Port" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Menu
Write-Host "Select test mode:" -ForegroundColor Yellow
Write-Host "1. Quick Smoke Tests (Frontend only - 2 min)" -ForegroundColor Green
Write-Host "2. Integration Tests (Frontend + Backend - 10 min)" -ForegroundColor Green
Write-Host "3. Full E2E Tests (All services - 30 min)" -ForegroundColor Green
Write-Host "4. Production Tests (Test live site)" -ForegroundColor Green
Write-Host "5. Run Playwright UI (Interactive)" -ForegroundColor Green
Write-Host ""

$choice = Read-Host "Enter your choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host "`n🏃 Running Quick Smoke Tests..." -ForegroundColor Cyan
        Write-Host "Services needed: Customer Frontend only" -ForegroundColor Gray
        Write-Host ""
        
        # Check if customer frontend is running
        if (-not (Test-ServiceRunning -Port 3000 -ServiceName "Customer Frontend")) {
            Write-Host "❌ Customer frontend not running on port 3000" -ForegroundColor Red
            Write-Host "   Start it with: npm run dev:customer" -ForegroundColor Yellow
            exit 1
        }
        
        Write-Host "✅ Customer frontend is running" -ForegroundColor Green
        Write-Host ""
        
        npx playwright test --grep @smoke
    }
    
    "2" {
        Write-Host "`n🏃 Running Integration Tests..." -ForegroundColor Cyan
        Write-Host "Services needed: Frontend + Backend + Database" -ForegroundColor Gray
        Write-Host ""
        
        # Check services
        $servicesOk = $true
        
        if (-not (Test-ServiceRunning -Port 3000 -ServiceName "Customer Frontend")) {
            Write-Host "❌ Customer frontend not running" -ForegroundColor Red
            $servicesOk = $false
        } else {
            Write-Host "✅ Customer frontend running" -ForegroundColor Green
        }
        
        if (-not (Test-ServiceRunning -Port 8000 -ServiceName "Backend API")) {
            Write-Host "❌ Backend API not running" -ForegroundColor Red
            $servicesOk = $false
        } else {
            Write-Host "✅ Backend API running" -ForegroundColor Green
        }
        
        if (-not $servicesOk) {
            Write-Host "`n💡 Start services with: docker-compose up -d" -ForegroundColor Yellow
            exit 1
        }
        
        Write-Host ""
        npx playwright test --grep "@booking|@admin" --grep-invert @realtime
    }
    
    "3" {
        Write-Host "`n🏃 Running Full E2E Tests..." -ForegroundColor Cyan
        Write-Host "Services needed: All (Frontend, Backend, Redis, Celery)" -ForegroundColor Gray
        Write-Host ""
        
        Write-Host "Checking services..." -ForegroundColor Yellow
        
        # Check all services
        $services = @(
            @{Port=3000; Name="Customer Frontend"},
            @{Port=3001; Name="Admin Frontend"},
            @{Port=8000; Name="Backend API"}
        )
        
        $allRunning = $true
        foreach ($service in $services) {
            if (Test-ServiceRunning -Port $service.Port -ServiceName $service.Name) {
                Write-Host "✅ $($service.Name) running" -ForegroundColor Green
            } else {
                Write-Host "❌ $($service.Name) not running" -ForegroundColor Red
                $allRunning = $false
            }
        }
        
        if (-not $allRunning) {
            Write-Host "`n💡 Start all services with: docker-compose up -d" -ForegroundColor Yellow
            Write-Host "   Or use: .\launch-all-services.ps1" -ForegroundColor Yellow
            exit 1
        }
        
        Write-Host ""
        Write-Host "🧪 Running all E2E tests..." -ForegroundColor Cyan
        npx playwright test
    }
    
    "4" {
        Write-Host "`n🌐 Running Production Tests..." -ForegroundColor Cyan
        
        $prodUrl = Read-Host "Enter production URL (e.g., https://myhibachichef.com)"
        
        if ([string]::IsNullOrWhiteSpace($prodUrl)) {
            Write-Host "❌ No URL provided" -ForegroundColor Red
            exit 1
        }
        
        Write-Host ""
        Write-Host "Testing: $prodUrl" -ForegroundColor Yellow
        
        $env:BASE_URL = $prodUrl
        npx playwright test --config=playwright.prod.config.ts --grep "@smoke|@critical"
    }
    
    "5" {
        Write-Host "`n🎬 Launching Playwright UI..." -ForegroundColor Cyan
        Write-Host ""
        Write-Host "This will open an interactive test UI in your browser" -ForegroundColor Gray
        Write-Host "You can click on tests to run them and see results" -ForegroundColor Gray
        Write-Host ""
        
        npx playwright test --ui
    }
    
    default {
        Write-Host "❌ Invalid choice" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✨ Tests completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 View detailed report:" -ForegroundColor Cyan
Write-Host "   npx playwright show-report" -ForegroundColor Yellow
