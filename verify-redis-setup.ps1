# ============================================================================
# REDIS & SCHEDULE VERIFICATION SCRIPT
# ============================================================================
# Checks if Redis server is running and libraries are installed
# ============================================================================

Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host (" " * 76) -NoNewline -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan
Write-Host "  REDIS & SCHEDULE VERIFICATION" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host (" " * 76) -NoNewline -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# ============================================================================
# CHECK 1: Python Libraries
# ============================================================================

Write-Host "[CHECK 1] Python Libraries" -ForegroundColor Cyan
Write-Host ""

Write-Host "  Checking 'redis' library..." -NoNewline
try {
    $redisVersion = python -c "import redis; print(redis.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✅ INSTALLED (v$redisVersion)" -ForegroundColor Green
    } else {
        Write-Host " ❌ NOT INSTALLED" -ForegroundColor Red
        Write-Host "    Fix: pip install redis" -ForegroundColor Yellow
        $allGood = $false
    }
}
catch {
    Write-Host " ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    $allGood = $false
}

Write-Host "  Checking 'schedule' library..." -NoNewline
try {
    $scheduleVersion = python -c "import schedule; print(schedule.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✅ INSTALLED (v$scheduleVersion)" -ForegroundColor Green
    } else {
        Write-Host " ❌ NOT INSTALLED" -ForegroundColor Red
        Write-Host "    Fix: pip install schedule" -ForegroundColor Yellow
        $allGood = $false
    }
}
catch {
    Write-Host " ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    $allGood = $false
}

Write-Host ""

# ============================================================================
# CHECK 2: Redis Server
# ============================================================================

Write-Host "[CHECK 2] Redis Server" -ForegroundColor Cyan
Write-Host ""

Write-Host "  Checking if Redis/Memurai is running..." -NoNewline

# Check Windows Service
$redisService = Get-Service -Name "Redis*","Memurai*" -ErrorAction SilentlyContinue | Where-Object {$_.Status -eq "Running"}

if ($redisService) {
    Write-Host " ✅ RUNNING" -ForegroundColor Green
    Write-Host "    Service: $($redisService.Name)" -ForegroundColor Gray
    Write-Host "    Status: $($redisService.Status)" -ForegroundColor Gray
} else {
    Write-Host " ❌ NOT RUNNING" -ForegroundColor Red
    Write-Host ""
    Write-Host "    Redis/Memurai service not found or not running." -ForegroundColor Yellow
    Write-Host "    Options:" -ForegroundColor Yellow
    Write-Host "      1. Install Memurai: https://www.memurai.com/get-memurai" -ForegroundColor Gray
    Write-Host "      2. Or use Docker: docker run -d -p 6379:6379 redis:7-alpine" -ForegroundColor Gray
    Write-Host "      3. Or install via WSL2: sudo apt install redis-server" -ForegroundColor Gray
    $allGood = $false
}

Write-Host ""

# ============================================================================
# CHECK 3: Redis Connection Test
# ============================================================================

Write-Host "[CHECK 3] Redis Connection Test" -ForegroundColor Cyan
Write-Host ""

Write-Host "  Testing connection to localhost:6379..." -NoNewline

$testScript = @"
import redis
try:
    r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
    if r.ping():
        print('CONNECTED')
        exit(0)
    else:
        print('NO_RESPONSE')
        exit(1)
except redis.ConnectionError as e:
    print(f'CONNECTION_REFUSED: {e}')
    exit(1)
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
"@

$result = python -c $testScript 2>&1
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0 -and $result -eq "CONNECTED") {
    Write-Host " ✅ SUCCESS" -ForegroundColor Green
    Write-Host "    Redis is accessible at localhost:6379" -ForegroundColor Gray
} elseif ($result -like "*CONNECTION_REFUSED*") {
    Write-Host " ❌ CONNECTION REFUSED" -ForegroundColor Red
    Write-Host "    Redis server is not running on port 6379." -ForegroundColor Yellow
    Write-Host "    Start Redis/Memurai service or install it." -ForegroundColor Yellow
    $allGood = $false
} else {
    Write-Host " ❌ FAILED" -ForegroundColor Red
    Write-Host "    Error: $result" -ForegroundColor Yellow
    $allGood = $false
}

Write-Host ""

# ============================================================================
# CHECK 4: Cache Service Test
# ============================================================================

Write-Host "[CHECK 4] Backend Cache Service Test" -ForegroundColor Cyan
Write-Host ""

Write-Host "  Testing cache service initialization..." -NoNewline

$cacheTestScript = @"
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

async def test_cache():
    try:
        from core.cache import CacheService
        redis_url = 'redis://localhost:6379/0'
        cache = CacheService(redis_url)
        await asyncio.wait_for(cache.connect(), timeout=3.0)
        print('CACHE_OK')
        await cache.disconnect()
        return 0
    except asyncio.TimeoutError:
        print('CACHE_TIMEOUT')
        return 1
    except Exception as e:
        print(f'CACHE_ERROR: {e}')
        return 1

sys.exit(asyncio.run(test_cache()))
"@

cd "c:\Users\surya\projects\MH webapps\apps\backend"
$cacheResult = python -c $cacheTestScript 2>&1
$cacheExitCode = $LASTEXITCODE

if ($cacheExitCode -eq 0 -and $cacheResult -eq "CACHE_OK") {
    Write-Host " ✅ SUCCESS" -ForegroundColor Green
    Write-Host "    Cache service can connect to Redis" -ForegroundColor Gray
} elseif ($cacheResult -like "*CACHE_TIMEOUT*") {
    Write-Host " ⚠️  TIMEOUT" -ForegroundColor Yellow
    Write-Host "    Cache service timed out (Redis may not be running)" -ForegroundColor Yellow
    $allGood = $false
} else {
    Write-Host " ❌ FAILED" -ForegroundColor Red
    Write-Host "    Error: $cacheResult" -ForegroundColor Yellow
    $allGood = $false
}

Write-Host ""

# ============================================================================
# FINAL SUMMARY
# ============================================================================

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host (" " * 76) -NoNewline -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan
Write-Host "  VERIFICATION SUMMARY" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host (" " * 76) -NoNewline -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan
Write-Host ""

if ($allGood) {
    Write-Host "  🎉 ALL CHECKS PASSED!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Your backend is ready to run WITHOUT warnings:" -ForegroundColor Green
    Write-Host "    ✅ Redis library installed" -ForegroundColor Green
    Write-Host "    ✅ Schedule library installed" -ForegroundColor Green
    Write-Host "    ✅ Redis server running" -ForegroundColor Green
    Write-Host "    ✅ Cache service working" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Next steps:" -ForegroundColor Cyan
    Write-Host "    1. Start backend: python run_backend.py" -ForegroundColor Gray
    Write-Host "    2. Look for ✅ messages instead of ⚠️  warnings" -ForegroundColor Gray
    Write-Host "    3. Run comprehensive tests" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "  ⚠️  SOME CHECKS FAILED" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  What's working:" -ForegroundColor Cyan
    if ($redisVersion) {
        Write-Host "    ✅ Redis library installed" -ForegroundColor Green
    }
    if ($scheduleVersion) {
        Write-Host "    ✅ Schedule library installed" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "  What needs fixing:" -ForegroundColor Cyan
    if (-not $redisService) {
        Write-Host "    ❌ Redis server not running" -ForegroundColor Red
        Write-Host "       → Install Memurai: https://www.memurai.com/get-memurai" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "  Current status:" -ForegroundColor Cyan
    Write-Host "    Your backend will still work, but you'll see warnings:" -ForegroundColor Yellow
    Write-Host "      ⚠️  Cache service connection timeout" -ForegroundColor Yellow
    Write-Host "      ⚠️  Rate limiter connection timeout" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  These warnings are OK for development, but installing Redis" -ForegroundColor Gray
    Write-Host "  will give you better performance and production-like testing." -ForegroundColor Gray
    Write-Host ""
}

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host (" " * 76) -NoNewline -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan
Write-Host ""
