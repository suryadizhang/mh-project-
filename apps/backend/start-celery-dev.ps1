#!/usr/bin/env pwsh
# Start all Celery services for development

<#
.SYNOPSIS
    Start Celery Worker, Beat, and Flower monitoring for MyHibachi backend

.DESCRIPTION
    This script launches three processes in separate terminals:
    1. Celery Worker - Executes background tasks (SMS, calls, recordings)
    2. Celery Beat - Schedules periodic tasks (cleanup, archiving)
    3. Flower - Web UI monitoring dashboard at http://localhost:5555

.EXAMPLE
    .\start-celery-dev.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting MyHibachi Celery Services..." -ForegroundColor Cyan
Write-Host ""

# Get the backend directory
$BackendDir = $PSScriptRoot
Set-Location $BackendDir

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "❌ Virtual environment not found. Please run 'python -m venv venv' first." -ForegroundColor Red
    exit 1
}

# Check if Redis is running
Write-Host "📡 Checking Redis connection..." -ForegroundColor Yellow
try {
    $redisTest = python -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping(); print('OK')" 2>&1
    if ($redisTest -notmatch "OK") {
        Write-Host "❌ Redis is not running. Please start Redis first:" -ForegroundColor Red
        Write-Host "   docker run -d -p 6379:6379 redis:alpine" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✅ Redis is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to connect to Redis: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting Celery services in separate windows..." -ForegroundColor Cyan

# 1. Start Celery Worker
Write-Host "1️⃣  Launching Celery Worker..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$BackendDir'; .\venv\Scripts\Activate.ps1; Write-Host '🔨 Celery Worker Started' -ForegroundColor Green; Write-Host 'Waiting for tasks...' -ForegroundColor Cyan; celery -A src.workers.celery_config worker -l info --pool=solo"
) -WindowStyle Normal

Start-Sleep -Seconds 2

# 2. Start Celery Beat
Write-Host "2️⃣  Launching Celery Beat Scheduler..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$BackendDir'; .\venv\Scripts\Activate.ps1; Write-Host '⏰ Celery Beat Scheduler Started' -ForegroundColor Green; Write-Host 'Periodic tasks scheduled:' -ForegroundColor Cyan; Write-Host '  - cleanup_old_recordings: Daily at 2:00 AM' -ForegroundColor White; Write-Host '  - archive_old_recordings: Daily at 3:00 AM' -ForegroundColor White; celery -A src.workers.celery_config beat -l info"
) -WindowStyle Normal

Start-Sleep -Seconds 2

# 3. Start Flower Monitoring
Write-Host "3️⃣  Launching Flower Monitoring Dashboard..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$BackendDir'; .\venv\Scripts\Activate.ps1; Write-Host '🌸 Flower Monitoring Dashboard Started' -ForegroundColor Green; Write-Host 'Access at: http://localhost:5555' -ForegroundColor Cyan; Write-Host 'Press Ctrl+C to stop' -ForegroundColor Yellow; celery -A src.workers.celery_config flower --port=5555"
) -WindowStyle Normal

Write-Host ""
Write-Host "✅ All Celery services started!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Services Running:" -ForegroundColor Cyan
Write-Host "   🔨 Worker:    Processing background tasks" -ForegroundColor White
Write-Host "   ⏰ Beat:      Scheduling periodic tasks" -ForegroundColor White
Write-Host "   🌸 Flower:    http://localhost:5555" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Yellow
Write-Host "   - View real-time task execution in Flower UI" -ForegroundColor White
Write-Host "   - Check worker logs for SMS/call operations" -ForegroundColor White
Write-Host "   - Beat scheduler shows next scheduled task times" -ForegroundColor White
Write-Host "   - Close all windows to stop services" -ForegroundColor White
Write-Host ""
