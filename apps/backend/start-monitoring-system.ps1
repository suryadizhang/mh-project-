#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start complete monitoring system (all components)

.DESCRIPTION
    Starts all monitoring system components:
    1. Celery Worker (for monitoring tasks)
    2. Celery Beat (for scheduled tasks)
    3. ThresholdMonitor (real-time push monitoring)
    
    Uses PowerShell jobs to run all components in parallel.

.EXAMPLE
    .\start-monitoring-system.ps1
    
.EXAMPLE
    .\start-monitoring-system.ps1 -StopAll  # Stop all monitoring jobs
#>

param(
    [switch]$StopAll
)

$ErrorActionPreference = "Stop"

# Job names
$WORKER_JOB = "MonitoringWorker"
$BEAT_JOB = "MonitoringBeat"
$MONITOR_JOB = "ThresholdMonitor"

# Stop all monitoring jobs
if ($StopAll) {
    Write-Host "🛑 Stopping all monitoring jobs..." -ForegroundColor Yellow
    
    $jobs = Get-Job | Where-Object { $_.Name -in @($WORKER_JOB, $BEAT_JOB, $MONITOR_JOB) }
    
    if ($jobs) {
        $jobs | Stop-Job
        $jobs | Remove-Job -Force
        Write-Host "✓ All monitoring jobs stopped" -ForegroundColor Green
    } else {
        Write-Host "   No monitoring jobs found" -ForegroundColor Gray
    }
    
    exit 0
}

Write-Host "🚀 Starting Complete Monitoring System" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
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
        Write-Host "✓ Redis is running" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis connection failed" -ForegroundColor Red
        Write-Host "   Please start Redis first" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}

# Check for existing jobs
Write-Host "🔍 Checking for existing monitoring jobs..." -ForegroundColor Yellow
$existingJobs = Get-Job | Where-Object { $_.Name -in @($WORKER_JOB, $BEAT_JOB, $MONITOR_JOB) }

if ($existingJobs) {
    Write-Host "⚠ Found existing monitoring jobs:" -ForegroundColor Yellow
    $existingJobs | Format-Table Name, State, HasMoreData
    
    $response = Read-Host "Stop existing jobs and start fresh? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        $existingJobs | Stop-Job
        $existingJobs | Remove-Job -Force
        Write-Host "✓ Existing jobs stopped" -ForegroundColor Green
    } else {
        Write-Host "❌ Cancelled" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "📋 Starting Components:" -ForegroundColor Cyan
Write-Host "   1. Celery Worker (monitoring queue)" -ForegroundColor White
Write-Host "   2. Celery Beat (scheduled tasks)" -ForegroundColor White
Write-Host "   3. ThresholdMonitor (real-time)" -ForegroundColor White
Write-Host ""

# Start Celery Worker
Write-Host "🎯 Starting Celery Worker..." -ForegroundColor Green
$workerJob = Start-Job -Name $WORKER_JOB -ScriptBlock {
    Set-Location $using:PWD
    Set-Location src
    celery -A workers.celery_config worker `
        --hostname="monitoring_worker@%h" `
        --queues=monitoring `
        --loglevel=info `
        --pool=solo `
        --max-tasks-per-child=100 `
        --without-gossip `
        --without-mingle `
        --without-heartbeat
}

Start-Sleep -Seconds 2
if ($workerJob.State -eq "Running") {
    Write-Host "✓ Celery Worker started (Job ID: $($workerJob.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start Celery Worker" -ForegroundColor Red
    Receive-Job $workerJob
    exit 1
}

# Start Celery Beat
Write-Host "🎯 Starting Celery Beat..." -ForegroundColor Green
$beatJob = Start-Job -Name $BEAT_JOB -ScriptBlock {
    Set-Location $using:PWD
    Set-Location src
    celery -A workers.celery_config beat `
        --loglevel=info
}

Start-Sleep -Seconds 2
if ($beatJob.State -eq "Running") {
    Write-Host "✓ Celery Beat started (Job ID: $($beatJob.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start Celery Beat" -ForegroundColor Red
    Receive-Job $beatJob
    exit 1
}

# Start ThresholdMonitor
Write-Host "🎯 Starting ThresholdMonitor..." -ForegroundColor Green
$monitorJob = Start-Job -Name $MONITOR_JOB -ScriptBlock {
    Set-Location $using:PWD
    Set-Location src
    python -m monitoring.cli start
}

Start-Sleep -Seconds 2
if ($monitorJob.State -eq "Running") {
    Write-Host "✓ ThresholdMonitor started (Job ID: $($monitorJob.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start ThresholdMonitor" -ForegroundColor Red
    Receive-Job $monitorJob
    exit 1
}

Write-Host ""
Write-Host "✅ All monitoring components started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Monitoring System Status:" -ForegroundColor Cyan
Get-Job | Where-Object { $_.Name -in @($WORKER_JOB, $BEAT_JOB, $MONITOR_JOB) } | Format-Table Name, State, HasMoreData

Write-Host ""
Write-Host "📝 Management Commands:" -ForegroundColor Cyan
Write-Host "   Get-Job                              # List all jobs" -ForegroundColor White
Write-Host "   Receive-Job -Name $WORKER_JOB   # View worker output" -ForegroundColor White
Write-Host "   Receive-Job -Name $BEAT_JOB     # View beat output" -ForegroundColor White
Write-Host "   Receive-Job -Name $MONITOR_JOB  # View monitor output" -ForegroundColor White
Write-Host "   Stop-Job -Name $WORKER_JOB      # Stop worker" -ForegroundColor White
Write-Host "   .\start-monitoring-system.ps1 -StopAll  # Stop all" -ForegroundColor White
Write-Host ""
Write-Host "🔍 Monitoring CLI:" -ForegroundColor Cyan
Write-Host "   cd src" -ForegroundColor White
Write-Host "   python -m monitoring.cli stats       # View statistics" -ForegroundColor White
Write-Host "   python -m monitoring.cli violations  # View violations" -ForegroundColor White
Write-Host "   python -m monitoring.cli health      # Health check" -ForegroundColor White
Write-Host ""
Write-Host "💡 The monitoring system is now running in the background!" -ForegroundColor Yellow
Write-Host "   Jobs will continue running even if you close this window." -ForegroundColor Gray
Write-Host ""
