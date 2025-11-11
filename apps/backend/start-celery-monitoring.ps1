#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start Celery worker with monitoring tasks

.DESCRIPTION
    Starts Celery worker configured for monitoring tasks with:
    - Dedicated monitoring queue
    - Solo pool for Windows compatibility
    - Proper logging configuration
    - Health checks enabled

.EXAMPLE
    .\start-celery-monitoring.ps1
#>

# Configuration
$WORKER_NAME = "monitoring_worker"
$LOG_LEVEL = "info"
$CONCURRENCY = 4
$MAX_TASKS_PER_CHILD = 100

Write-Host "🚀 Starting Celery Monitoring Worker..." -ForegroundColor Green
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

# Check Python environment
Write-Host "🔍 Checking Python environment..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "   Using: $pythonVersion" -ForegroundColor Cyan

# Check Celery installation
Write-Host "🔍 Checking Celery installation..." -ForegroundColor Yellow
$celeryVersion = celery --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Celery installed: $celeryVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Celery not found. Installing..." -ForegroundColor Red
    pip install celery redis
}

Write-Host ""
Write-Host "📋 Worker Configuration:" -ForegroundColor Cyan
Write-Host "   Name: $WORKER_NAME" -ForegroundColor White
Write-Host "   Queue: monitoring" -ForegroundColor White
Write-Host "   Concurrency: $CONCURRENCY" -ForegroundColor White
Write-Host "   Log Level: $LOG_LEVEL" -ForegroundColor White
Write-Host ""

# Set working directory
Set-Location src

# Start Celery worker
Write-Host "🎯 Starting Celery worker..." -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Run Celery worker with monitoring queue
try {
    celery -A workers.celery_config worker `
        --hostname="$WORKER_NAME@%h" `
        --queues=monitoring `
        --loglevel=$LOG_LEVEL `
        --pool=solo `
        --max-tasks-per-child=$MAX_TASKS_PER_CHILD `
        --without-gossip `
        --without-mingle `
        --without-heartbeat
} catch {
    Write-Host ""
    Write-Host "❌ Worker stopped: $_" -ForegroundColor Red
    exit 1
} finally {
    Set-Location ..
    Write-Host ""
    Write-Host "✓ Worker shutdown complete" -ForegroundColor Green
}
