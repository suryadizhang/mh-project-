#!/usr/bin/env pwsh
# =============================================================================
# My Hibachi - Database SSH Tunnel Script
# =============================================================================
# Creates SSH tunnel to VPS PostgreSQL for local development and testing
#
# Usage:
#   .\scripts\start-db-tunnel.ps1           # Start tunnel
#   .\scripts\start-db-tunnel.ps1 -Stop     # Stop tunnel
#   .\scripts\start-db-tunnel.ps1 -Status   # Check status
#
# Architecture:
#   Local (localhost:5433) --> SSH Tunnel --> VPS (localhost:5432)
#                                              |
#                                              v
#                                       myhibachi_staging database
#
# VPS Databases:
#   - myhibachi_staging (for testing/dev) <-- Used by this tunnel
#   - myhibachi_production (NEVER use locally!)
# =============================================================================

param(
  [switch]$Stop,
  [switch]$Status
)

$VPS_IP = "108.175.12.154"
$LOCAL_PORT = 5433
$REMOTE_PORT = 5432
$SSH_USER = "root"

function Get-TunnelProcess {
  Get-Process ssh -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*$LOCAL_PORT*$VPS_IP*"
  }
}

function Test-TunnelRunning {
  $listening = netstat -an | Select-String "127.0.0.1:$LOCAL_PORT.*LISTENING"
  return $listening -ne $null
}

if ($Status) {
  Write-Host "`n=== Database Tunnel Status ===" -ForegroundColor Cyan

  if (Test-TunnelRunning) {
    Write-Host "✅ Tunnel is RUNNING on localhost:$LOCAL_PORT" -ForegroundColor Green
    Write-Host "   VPS: $VPS_IP" -ForegroundColor Gray
    Write-Host "   Database: myhibachi_staging" -ForegroundColor Gray

    # Test actual connection
    try {
      $result = psql -h 127.0.0.1 -p $LOCAL_PORT -U myhibachi_staging_user -d myhibachi_staging -c "SELECT 1;" 2>&1
      if ($result -match "1 row") {
        Write-Host "   Connection: OK" -ForegroundColor Green
      }
    }
    catch {
      Write-Host "   Connection: Unable to verify (psql not available)" -ForegroundColor Yellow
    }
  }
  else {
    Write-Host "❌ Tunnel is NOT running" -ForegroundColor Red
    Write-Host "   Run: .\scripts\start-db-tunnel.ps1" -ForegroundColor Yellow
  }
  exit 0
}

if ($Stop) {
  Write-Host "`n=== Stopping Database Tunnel ===" -ForegroundColor Cyan

  # Kill any SSH processes for this tunnel
  $processes = Get-Process ssh -ErrorAction SilentlyContinue
  $killed = 0
  foreach ($proc in $processes) {
    # Check if this is our tunnel (port 5433)
    try {
      $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
      if ($cmdLine -match "$LOCAL_PORT.*localhost.*$VPS_IP") {
        Stop-Process -Id $proc.Id -Force
        $killed++
      }
    }
    catch {}
  }

  if ($killed -gt 0) {
    Write-Host "✅ Stopped $killed tunnel process(es)" -ForegroundColor Green
  }
  else {
    Write-Host "⚠️ No tunnel process found to stop" -ForegroundColor Yellow
  }
  exit 0
}

# Start tunnel
Write-Host "`n=== Starting Database SSH Tunnel ===" -ForegroundColor Cyan
Write-Host "VPS: $VPS_IP" -ForegroundColor Gray
Write-Host "Local Port: $LOCAL_PORT -> Remote Port: $REMOTE_PORT" -ForegroundColor Gray
Write-Host ""

# Check if already running
if (Test-TunnelRunning) {
  Write-Host "⚠️ Tunnel already running on localhost:$LOCAL_PORT" -ForegroundColor Yellow
  Write-Host "   Use -Stop to stop it first, or -Status to check" -ForegroundColor Gray
  exit 0
}

# Start the tunnel
Write-Host "Starting SSH tunnel..." -ForegroundColor Gray
$sshArgs = "-f -N -L ${LOCAL_PORT}:localhost:${REMOTE_PORT} ${SSH_USER}@${VPS_IP}"
Start-Process -FilePath "ssh" -ArgumentList $sshArgs -NoNewWindow

# Wait for tunnel to establish
Start-Sleep -Seconds 2

# Verify
if (Test-TunnelRunning) {
  Write-Host ""
  Write-Host "✅ SSH tunnel started successfully!" -ForegroundColor Green
  Write-Host ""
  Write-Host "Connection Details:" -ForegroundColor Cyan
  Write-Host "  Host: 127.0.0.1" -ForegroundColor White
  Write-Host "  Port: $LOCAL_PORT" -ForegroundColor White
  Write-Host "  Database: myhibachi_staging" -ForegroundColor White
  Write-Host "  User: myhibachi_staging_user" -ForegroundColor White
  Write-Host ""
  Write-Host "DATABASE_URL=postgresql+asyncpg://myhibachi_staging_user:<STAGING_DB_PASSWORD>@127.0.0.1:${LOCAL_PORT}/myhibachi_staging" -ForegroundColor DarkGray
  Write-Host "(Get password from team lead or .env.local file)" -ForegroundColor DarkGray
  Write-Host ""
  Write-Host "You can now run tests or start the backend." -ForegroundColor Green
}
else {
  Write-Host ""
  Write-Host "❌ Failed to start tunnel" -ForegroundColor Red
  Write-Host "   Check SSH connectivity: ssh ${SSH_USER}@${VPS_IP}" -ForegroundColor Yellow
  exit 1
}
