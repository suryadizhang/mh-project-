# 🚀 Quick Start Commands - October 30, 2025

## Start Backend Server

```powershell
cd "c:\Users\surya\projects\MH webapps\apps\backend"
python run_backend.py
```

**Expected Output:**
```
✅ Added Python path
🚀 Starting FastAPI backend server...
📡 Server: http://localhost:8000
📚 API docs: http://localhost:8000/docs
❤️  Health: http://localhost:8000/health
```

---

## Run Tests

### Quick Health Check Test
```powershell
cd "c:\Users\surya\projects\MH webapps\apps\backend"
python test_server.py
```

### Full Test Suite (when ready)
```powershell
cd "c:\Users\surya\projects\MH webapps\apps\backend"
pytest tests/ -v
```

---

## Check Health Endpoints

### Basic Health
```powershell
Invoke-RestMethod http://localhost:8000/health | ConvertTo-Json
```

### Liveness Probe
```powershell
Invoke-RestMethod http://localhost:8000/api/health/live | ConvertTo-Json
```

### Readiness Probe  
```powershell
Invoke-RestMethod http://localhost:8000/api/health/ready | ConvertTo-Json
```

### Existing V1 Health Checks
```powershell
# Readiness
Invoke-RestMethod http://localhost:8000/api/v1/health/readiness | ConvertTo-Json

# Liveness
Invoke-RestMethod http://localhost:8000/api/v1/health/liveness | ConvertTo-Json

# Detailed
Invoke-RestMethod http://localhost:8000/api/v1/health/detailed | ConvertTo-Json
```

---

## Test Rate Limiting

### Test Public Rate Limit (5 req/min)
```powershell
1..6 | ForEach-Object {
    Write-Host "`n=== Request $_ ===" -ForegroundColor Cyan
    try {
        Invoke-RestMethod http://localhost:8000/api/bookings
    } catch {
        Write-Host "Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
        $_.ErrorDetails.Message | ConvertFrom-Json | ConvertTo-Json
    }
}
```

### Check Rate Limit Headers
```powershell
$response = Invoke-WebRequest http://localhost:8000/api/bookings
$response.Headers | Format-Table
```

---

## Admin Error Dashboard

### List All Errors (requires admin token)
```powershell
$token = "your-admin-jwt-token"
Invoke-RestMethod -Uri "http://localhost:8000/api/admin/error-logs" `
    -Headers @{ "Authorization" = "Bearer $token" } | ConvertTo-Json -Depth 5
```

### Get Error Statistics
```powershell
$token = "your-admin-jwt-token"
Invoke-RestMethod -Uri "http://localhost:8000/api/admin/error-logs/statistics/overview" `
    -Headers @{ "Authorization" = "Bearer $token" } | ConvertTo-Json
```

### Export Errors to CSV
```powershell
$token = "your-admin-jwt-token"
Invoke-WebRequest -Uri "http://localhost:8000/api/admin/error-logs/export/csv" `
    -Headers @{ "Authorization" = "Bearer $token" } `
    -OutFile "error_logs.csv"

# View the file
Get-Content error_logs.csv | Select-Object -First 10
```

---

## Database Management

### Apply Migrations
```powershell
cd "c:\Users\surya\projects\MH webapps\apps\backend"
alembic upgrade head
```

### Check Current Migration
```powershell
alembic current
```

### Create New Migration
```powershell
alembic revision --autogenerate -m "Description of changes"
```

### Rollback Last Migration
```powershell
alembic downgrade -1
```

---

## API Documentation

### Open Swagger UI
```powershell
Start-Process "http://localhost:8000/docs"
```

### Open ReDoc
```powershell
Start-Process "http://localhost:8000/redoc"
```

---

## Server Management

### Stop Server (if running in terminal)
Press `Ctrl+C` in the terminal running the server

### Check if Server is Running
```powershell
Test-NetConnection -ComputerName localhost -Port 8000
```

### Find Process Using Port 8000
```powershell
netstat -ano | findstr :8000
```

### Kill Process on Port 8000
```powershell
# Find PID from above command, then:
taskkill /PID <process-id> /F
```

---

## Troubleshooting

### Check Logs
```powershell
# Server logs are printed to terminal
# Database logs:
Get-Content "c:\Users\surya\projects\MH webapps\apps\backend\logs\app.log" -Tail 50
```

### Verify Environment Variables
```powershell
cd "c:\Users\surya\projects\MH webapps\apps\backend"
$env:DATABASE_URL
$env:REDIS_URL
$env:TWILIO_ACCOUNT_SID
```

### Test Database Connection
```powershell
cd "c:\Users\surya\projects\MH webapps\apps\backend\src"
python -c "from api.app.database import engine; print('Database OK')"
```

### Install Redis (Optional)
```powershell
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or check if installed
redis-cli ping
```

---

## Performance Testing

### Apache Bench (if installed)
```powershell
ab -n 1000 -c 10 http://localhost:8000/health
```

### PowerShell Load Test
```powershell
$start = Get-Date
1..100 | ForEach-Object -Parallel {
    Invoke-RestMethod http://localhost:8000/health
} -ThrottleLimit 10
$end = Get-Date
Write-Host "Total time: $(($end - $start).TotalSeconds) seconds"
```

---

## Git Operations

### Check Status
```powershell
git status
```

### Commit Changes
```powershell
git add .
git commit -m "feat: implement rate limiting, structured logging, and health checks"
```

### Create Branch for Today's Work
```powershell
git checkout -b feature/oct-30-implementation
```

---

## Quick Reference Links

- **Implementation Details**: IMPLEMENTATION_COMPLETE_OCT_30_2025.md
- **Quick Reference**: QUICK_REFERENCE_OCT_30_2025.md  
- **Testing Guide**: TESTING_GUIDE_OCT_30_2025.md
- **Final Summary**: FINAL_SUMMARY_OCT_30_2025.md
- **Audit Report**: COMPREHENSIVE_ONE_WEEK_AUDIT_REPORT.md

---

## Most Common Commands

```powershell
# Start server
cd apps/backend ; python run_backend.py

# Run tests
cd apps/backend ; python test_server.py

# Check health
Invoke-RestMethod http://localhost:8000/health

# View API docs
Start-Process http://localhost:8000/docs

# Apply migrations
cd apps/backend ; alembic upgrade head
```

---

**Quick Start Guide Created**: October 30, 2025  
**Status**: ✅ READY TO USE
