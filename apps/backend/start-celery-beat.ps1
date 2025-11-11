#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start Celery Beat scheduler

.DESCRIPTION
    Starts Celery Beat scheduler for periodic tasks including:
    - Metric collection backup (every 5 min)
    - Rule verification (every 2 min)
    - Health checks (every 10 min)
    - Data cleanup (every hour)
    - Statistics aggregation (every hour)

.EXAMPLE
    .\start-celery-beat.ps1
#>

# Configuration
$LOG_LEVEL = "info"
$SCHEDULER = "redis"  # Use Redis as scheduler backend

Write-Host "⏰ Starting Celery Beat Scheduler..." -ForegroundColor Green
Write-Host ""

# Check if we're in the backend directory
if (-not (Test-Path "src\workers\celery_config.py")) {
    Write-Host "❌ Error: Must run from apps/backend directory" -ForegroundColor Red
    exit 1
}

# Check Redis connection
Write-Host "🔍 Checking Redis connection..." -ForegroundColor Yellow
try {
    $redisTest = python -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping(); print('OK')" 2>&1
    if ($redisTest -like "*OK*") {
        Write-Host "✓ Redis connection successful" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis connection failed" -ForegroundColor Red
        Write-Host "   Make sure Redis is running on localhost:6379" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Error checking Redis: $_" -ForegroundColor Red
    exit 1
}

# Check required packages
Write-Host "🔍 Checking required packages..." -ForegroundColor Yellow
$packages = @("celery", "redis", "celery-redbeat")
foreach ($package in $packages) {
    $installed = pip show $package 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $package installed" -ForegroundColor Green
    } else {
        Write-Host "⚠ $package not found. Installing..." -ForegroundColor Yellow
        pip install $package
    }
}

Write-Host ""
Write-Host "📋 Scheduled Tasks:" -ForegroundColor Cyan
Write-Host "   collect-metrics-backup     : Every 5 minutes" -ForegroundColor White
Write-Host "   verify-rules               : Every 2 minutes" -ForegroundColor White
Write-Host "   monitoring-health-check    : Every 10 minutes" -ForegroundColor White
Write-Host "   cleanup-monitoring-data    : Every hour" -ForegroundColor White
Write-Host "   aggregate-monitoring-stats : Every hour" -ForegroundColor White
Write-Host ""

# Set working directory
Set-Location src

# Start Celery Beat
Write-Host "🎯 Starting Celery Beat scheduler..." -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Run Celery Beat
try {
    celery -A workers.celery_config beat `
        --loglevel=$LOG_LEVEL `
        --scheduler=redbeat.RedBeatScheduler
} catch {
    # Fallback to default scheduler if redbeat not available
    Write-Host "⚠ RedBeat scheduler not available, using default..." -ForegroundColor Yellow
    celery -A workers.celery_config beat `
        --loglevel=$LOG_LEVEL
} finally {
    Set-Location ..
    Write-Host ""
    Write-Host "✓ Beat scheduler stopped" -ForegroundColor Green
}
