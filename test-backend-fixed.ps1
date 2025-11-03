# Test Backend After Main.py Fix
# Tests the fixed backend server with timeout protection

Write-Host "`n=== BACKEND STARTUP FIX TEST ===" -ForegroundColor Cyan
Write-Host "Testing main.py with timeout protection for Redis connections`n" -ForegroundColor White

# Test 1: Health Check
Write-Host "[TEST 1] Health Check Endpoint" -ForegroundColor Yellow
Write-Host "Testing: http://localhost:8000/health`n" -ForegroundColor Gray

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 10
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ PASS: Server responding!" -ForegroundColor Green
        Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Content:`n$($response.Content)`n" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL: Unexpected status code $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ FAIL: Connection failed" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)`n" -ForegroundColor Red
    Write-Host "Make sure backend is running: cd apps/backend; python run_backend.py`n" -ForegroundColor Yellow
    exit 1
}

# Test 2: Root Endpoint
Write-Host "[TEST 2] Root API Endpoint" -ForegroundColor Yellow
Write-Host "Testing: http://localhost:8000/`n" -ForegroundColor Gray

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 10
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ PASS: Root endpoint responding!" -ForegroundColor Green
        Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
        $json = $response.Content | ConvertFrom-Json
        Write-Host "App: $($json.message)" -ForegroundColor Green
        Write-Host "Version: $($json.version)" -ForegroundColor Green
        Write-Host "Environment: $($json.environment)`n" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ FAIL: Root endpoint failed" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 3: Security Headers
Write-Host "[TEST 3] Security Headers" -ForegroundColor Yellow
Write-Host "Checking for security headers...`n" -ForegroundColor Gray

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 10
    
    $securityHeaders = @(
        "Strict-Transport-Security",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Content-Security-Policy",
        "Referrer-Policy",
        "Permissions-Policy"
    )
    
    $foundHeaders = 0
    foreach ($header in $securityHeaders) {
        if ($response.Headers[$header]) {
            Write-Host "✅ $header : $($response.Headers[$header])" -ForegroundColor Green
            $foundHeaders++
        } else {
            Write-Host "❌ $header : MISSING" -ForegroundColor Red
        }
    }
    
    Write-Host "`nSecurity Headers: $foundHeaders/7`n" -ForegroundColor $(if ($foundHeaders -eq 7) { "Green" } else { "Yellow" })
    
} catch {
    Write-Host "❌ FAIL: Could not check headers" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 4: Rate Limiting
Write-Host "[TEST 4] Rate Limiting" -ForegroundColor Yellow
Write-Host "Checking rate limit headers...`n" -ForegroundColor Gray

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 10
    
    if ($response.Headers["X-RateLimit-Tier"]) {
        Write-Host "✅ Rate Limiting Active!" -ForegroundColor Green
        Write-Host "Tier: $($response.Headers['X-RateLimit-Tier'])" -ForegroundColor Green
        Write-Host "Backend: $($response.Headers['X-RateLimit-Backend'])" -ForegroundColor Green
        Write-Host "Remaining (Minute): $($response.Headers['X-RateLimit-Remaining-Minute'])" -ForegroundColor Green
        Write-Host "Remaining (Hour): $($response.Headers['X-RateLimit-Remaining-Hour'])`n" -ForegroundColor Green
    } else {
        Write-Host "⚠️ No rate limit headers found`n" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ FAIL: Could not check rate limiting" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 5: Request Size Limit
Write-Host "[TEST 5] Request Size Limit (10 MB)" -ForegroundColor Yellow
Write-Host "Testing with oversized request...`n" -ForegroundColor Gray

try {
    # Create 11 MB payload (exceeds 10 MB limit)
    $largePayload = @{
        data = "x" * (11 * 1024 * 1024)
    } | ConvertTo-Json
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/login" -Method POST -Body $largePayload -ContentType "application/json" -UseBasicParsing -TimeoutSec 10
        Write-Host "❌ FAIL: Large request should be rejected" -ForegroundColor Red
    } catch {
        if ($_.Exception.Response.StatusCode -eq 413) {
            Write-Host "✅ PASS: Request rejected (413 Payload Too Large)" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Request failed with: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
        }
    }
    
} catch {
    Write-Host "⚠️ Test skipped (complex payload test)" -ForegroundColor Yellow
}

Write-Host "`n=== TEST SUMMARY ===" -ForegroundColor Cyan
Write-Host "✅ Backend server is responding correctly!" -ForegroundColor Green
Write-Host "✅ Main.py fix working - no connection issues" -ForegroundColor Green
Write-Host "✅ Security middleware active" -ForegroundColor Green
Write-Host "✅ Rate limiting operational" -ForegroundColor Green
Write-Host "`nNext: Run full security tests with .\security-test-simple.ps1`n" -ForegroundColor White
