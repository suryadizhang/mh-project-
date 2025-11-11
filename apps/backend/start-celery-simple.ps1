#!/usr/bin/env pwsh
# Start Celery services for development

$ErrorActionPreference = "Stop"

Write-Host "Starting MyHibachi Celery Services..." -ForegroundColor Cyan
Write-Host ""

# Get the backend directory
$BackendDir = "C:\Users\surya\projects\MH webapps\apps\backend"
Set-Location $BackendDir

# Check if Redis is running
Write-Host "Checking Redis connection..." -ForegroundColor Yellow
try {
    $redisTest = redis-cli ping
    if ($redisTest -eq "PONG") {
        Write-Host "Redis is running" -ForegroundColor Green
    } else {
        Write-Host "Redis is not running. Please start Redis first." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Failed to connect to Redis" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting Celery services in separate windows..." -ForegroundColor Cyan

# 1. Start Celery Worker
Write-Host "1. Launching Celery Worker..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$BackendDir'; .\venv\Scripts\Activate.ps1; Write-Host 'Celery Worker Started' -ForegroundColor Green; celery -A src.workers.celery_config worker -l info --pool=solo"
)

Start-Sleep -Seconds 3

# 2. Start Celery Beat
Write-Host "2. Launching Celery Beat Scheduler..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$BackendDir'; .\venv\Scripts\Activate.ps1; Write-Host 'Celery Beat Scheduler Started' -ForegroundColor Green; celery -A src.workers.celery_config beat -l info"
)

Start-Sleep -Seconds 3

# 3. Start Flower Monitoring
Write-Host "3. Launching Flower Monitoring Dashboard..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$BackendDir'; .\venv\Scripts\Activate.ps1; Write-Host 'Flower Monitoring Dashboard Started' -ForegroundColor Green; Write-Host 'Access at: http://localhost:5555' -ForegroundColor Cyan; celery -A src.workers.celery_config flower --port=5555"
)

Write-Host ""
Write-Host "All Celery services started!" -ForegroundColor Green
Write-Host ""
Write-Host "Services Running:" -ForegroundColor Cyan
Write-Host "  Worker:  Processing background tasks" -ForegroundColor White
Write-Host "  Beat:    Scheduling periodic tasks" -ForegroundColor White
Write-Host "  Flower:  http://localhost:5555" -ForegroundColor White
Write-Host ""
Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "  - View real-time task execution in Flower UI" -ForegroundColor White
Write-Host "  - Check worker logs for SMS/call operations" -ForegroundColor White
Write-Host "  - Close all windows to stop services" -ForegroundColor White
Write-Host ""
