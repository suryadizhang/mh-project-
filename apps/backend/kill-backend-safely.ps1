# Safe Backend Process Killer
# Kills any zombie Python processes on port 8000

Write-Host "`n=== Safely Killing Backend Processes ===" -ForegroundColor Cyan

# Find processes using port 8000
$connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($connections) {
    $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    
    Write-Host "Found $($processIds.Count) process(es) on port 8000" -ForegroundColor Yellow
    
    foreach ($processId in $processIds) {
        try {
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "  Killing PID $processId ($($process.ProcessName))..." -ForegroundColor Yellow
                Stop-Process -Id $processId -Force -ErrorAction Stop
                Write-Host "  ✅ Killed PID $processId" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  PID $processId doesn't exist (zombie process)" -ForegroundColor DarkYellow
                # For zombie processes, we may need to wait for OS to clean up
            }
        } catch {
            $errorMsg = $_.Exception.Message
            Write-Host "  ❌ Failed to kill PID $processId : $errorMsg" -ForegroundColor Red
        }
    }
    
    # Wait for OS to release the port
    Write-Host "`nWaiting 3 seconds for port to be released..." -ForegroundColor Gray
    Start-Sleep -Seconds 3
    
    # Verify port is free
    $stillUsed = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($stillUsed) {
        Write-Host "⚠️  Port 8000 still in use! May need system reboot or wait longer." -ForegroundColor Red
        Write-Host "   Try running this script again in 30 seconds." -ForegroundColor Yellow
    } else {
        Write-Host "✅ Port 8000 is now free!" -ForegroundColor Green
    }
} else {
    Write-Host "✅ Port 8000 is already free" -ForegroundColor Green
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
