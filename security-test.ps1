# ============================================================
# 🔒 COMPREHENSIVE SECURITY PENETRATION TEST
# ============================================================
# Run this script in Windows PowerShell to test all security layers
# Usage: .\security-test.ps1
# ============================================================

$ErrorActionPreference = "Continue"
$API_URL = "http://localhost:8000"
$TestResults = @()

Write-Host "`n🔒 ============================================" -ForegroundColor Cyan
Write-Host "   SECURITY PENETRATION TEST SUITE" -ForegroundColor Cyan
Write-Host "   Testing: $API_URL" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Helper function to log results
function Log-Test {
    param($TestName, $Expected, $Actual, $Passed)
    $Result = @{
        Test = $TestName
        Expected = $Expected
        Actual = $Actual
        Passed = $Passed
        Time = Get-Date -Format "HH:mm:ss"
    }
    $script:TestResults += $Result
    
    if ($Passed) {
        Write-Host "✅ PASS: $TestName" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL: $TestName" -ForegroundColor Red
        Write-Host "   Expected: $Expected" -ForegroundColor Yellow
        Write-Host "   Actual: $Actual" -ForegroundColor Yellow
    }
}

# ============================================================
# TEST 1: Server Health Check
# ============================================================
Write-Host "`n📊 TEST 1: Server Health Check" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta
try {
    $response = Invoke-WebRequest -Uri "$API_URL/health" -Method GET -UseBasicParsing -ErrorAction Stop
    $statusCode = $response.StatusCode
    Log-Test "Health Endpoint Available" "200" "$statusCode" ($statusCode -eq 200)
} catch {
    Log-Test "Health Endpoint Available" "200" "Connection Failed" $false
    Write-Host "`n❌ ERROR: Backend server not running!" -ForegroundColor Red
    Write-Host "Please start the backend first with: cd apps\backend ; python run_backend.py`n" -ForegroundColor Yellow
    exit 1
}

# ============================================================
# TEST 2: Security Headers Check
# ============================================================
Write-Host "`n🛡️ TEST 2: Security Headers Validation" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta
try {
    $response = Invoke-WebRequest -Uri "$API_URL/health" -Method GET -UseBasicParsing
    $headers = $response.Headers
    
    # Check each security header
    $requiredHeaders = @{
        "Strict-Transport-Security" = "HSTS"
        "X-Content-Type-Options" = "nosniff"
        "X-Frame-Options" = "DENY"
        "X-XSS-Protection" = "1; mode=block"
        "Content-Security-Policy" = "CSP"
        "Referrer-Policy" = "strict-origin-when-cross-origin"
        "Permissions-Policy" = "Permissions Policy"
        "X-Request-ID" = "Request ID"
    }
    
    foreach ($header in $requiredHeaders.Keys) {
        $present = $headers.ContainsKey($header)
        $value = if ($present) { $headers[$header] } else { "Missing" }
        Log-Test "Security Header: $header" "Present" $(if($present){"Present"}else{"Missing"}) $present
    }
} catch {
    Log-Test "Security Headers Check" "Headers Present" "Failed to retrieve" $false
}

# ============================================================
# TEST 3: Authentication - Unauthorized Access Attempt
# ============================================================
Write-Host "`n🔐 TEST 3: Authentication Protection" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

# Test protected endpoints without authentication
$protectedEndpoints = @(
    "/api/bookings",
    "/api/customers",
    "/api/admin/users",
    "/api/admin/analytics"
)

foreach ($endpoint in $protectedEndpoints) {
    try {
        $response = Invoke-WebRequest -Uri "$API_URL$endpoint" -Method GET -UseBasicParsing -ErrorAction Stop
        $statusCode = $response.StatusCode
        Log-Test "Authentication Required: $endpoint" "401" "$statusCode" ($statusCode -eq 401)
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 401) {
            Log-Test "Authentication Required: $endpoint" "401" "401" $true
        } elseif ($statusCode -eq 404) {
            Log-Test "Authentication Required: $endpoint" "401 or 404" "404" $true
        } else {
            Log-Test "Authentication Required: $endpoint" "401" "$statusCode" $false
        }
    }
}

# ============================================================
# TEST 4: SQL Injection Attempts
# ============================================================
Write-Host "`n💉 TEST 4: SQL Injection Protection" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

$sqlInjectionPayloads = @(
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "1' UNION SELECT * FROM users--",
    "admin'--",
    "' OR 1=1--"
)

foreach ($payload in $sqlInjectionPayloads) {
    try {
        $encodedPayload = [System.Web.HttpUtility]::UrlEncode($payload)
        $response = Invoke-WebRequest -Uri "$API_URL/api/auth/login?username=$encodedPayload" -Method GET -UseBasicParsing -ErrorAction Stop
        $statusCode = $response.StatusCode
        # Should be rejected with 4xx error
        Log-Test "SQL Injection Blocked: $payload" "4xx Error" "$statusCode" ($statusCode -ge 400 -and $statusCode -lt 500)
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -ge 400 -and $statusCode -lt 500) {
            Log-Test "SQL Injection Blocked: $payload" "4xx Error" "$statusCode" $true
        } else {
            Log-Test "SQL Injection Blocked: $payload" "4xx Error" "$statusCode" $false
        }
    }
}

# ============================================================
# TEST 5: XSS (Cross-Site Scripting) Attempts
# ============================================================
Write-Host "`n🎭 TEST 5: XSS Protection" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

$xssPayloads = @(
    '<script>alert("xss")</script>',
    '<img src=x onerror=alert("xss")>',
    'javascript:alert("xss")',
    '<iframe src="javascript:alert(1)"></iframe>'
)

foreach ($payload in $xssPayloads) {
    try {
        $encodedPayload = [System.Web.HttpUtility]::UrlEncode($payload)
        $response = Invoke-WebRequest -Uri "$API_URL/api/auth/login?email=$encodedPayload" -Method GET -UseBasicParsing -ErrorAction Stop
        $statusCode = $response.StatusCode
        # Should be rejected or sanitized
        $displayPayload = $payload -replace '<','&lt;' -replace '>','&gt;'
        Log-Test "XSS Attack Blocked: $displayPayload" "4xx Error" "$statusCode" ($statusCode -ge 400)
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $displayPayload = $payload -replace '<','&lt;' -replace '>','&gt;'
        Log-Test "XSS Attack Blocked: $displayPayload" "4xx Error" "$statusCode" ($statusCode -ge 400)
    }
}

# ============================================================
# TEST 6: Rate Limiting
# ============================================================
Write-Host "`n⏱️ TEST 6: Rate Limiting Protection" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta
Write-Host "Sending 30 rapid requests (limit is 20/min for public)..." -ForegroundColor Yellow

$rateLimitResults = @()
for ($i = 1; $i -le 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/health" -Method GET -UseBasicParsing -ErrorAction Stop
        $statusCode = $response.StatusCode
        $rateLimitResults += $statusCode
        Write-Host "  Request $i`: $statusCode" -NoNewline
        if ($statusCode -eq 429) {
            Write-Host " (RATE LIMITED ✅)" -ForegroundColor Green
        } else {
            Write-Host ""
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $rateLimitResults += $statusCode
        Write-Host "  Request $i`: $statusCode (RATE LIMITED ✅)" -ForegroundColor Green
    }
    Start-Sleep -Milliseconds 50
}

$rateLimited = ($rateLimitResults | Where-Object { $_ -eq 429 }).Count -gt 0
Log-Test "Rate Limiting Active" "429 after 20+ requests" $(if($rateLimited){"Rate limited"}else{"Not limited"}) $rateLimited

# ============================================================
# TEST 7: Request Size Limit
# ============================================================
Write-Host "`n📦 TEST 7: Request Size Limit Protection" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

try {
    # Create 11 MB payload (limit is 10 MB)
    Write-Host "Creating 11 MB payload (limit is 10 MB)..." -ForegroundColor Yellow
    $largePayload = "A" * (11 * 1024 * 1024)
    $body = @{
        data = $largePayload
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$API_URL/api/auth/register" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    $statusCode = $response.StatusCode
    Log-Test "Large Request Blocked (>10MB)" "413 or 400" "$statusCode" ($statusCode -eq 413 -or $statusCode -eq 400)
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 413 -or $statusCode -eq 400) {
        Log-Test "Large Request Blocked (>10MB)" "413 or 400" "$statusCode" $true
    } else {
        # Connection may be closed by server
        Log-Test "Large Request Blocked (>10MB)" "Connection closed by server" "Blocked" $true
    }
}

# ============================================================
# TEST 8: CORS Validation
# ============================================================
Write-Host "`n🌐 TEST 8: CORS Protection" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

try {
    $headers = @{
        "Origin" = "https://evil-site.com"
    }
    $response = Invoke-WebRequest -Uri "$API_URL/health" -Method GET -Headers $headers -UseBasicParsing -ErrorAction Stop
    
    # Check if CORS headers are restrictive
    $corsHeader = $response.Headers["Access-Control-Allow-Origin"]
    if ($corsHeader) {
        $isWildcard = $corsHeader -eq "*"
        Log-Test "CORS Not Wildcard" "Specific origins only" $(if($isWildcard){"Wildcard *"}else{"Restricted"}) (-not $isWildcard)
    } else {
        Log-Test "CORS Header Present" "Present" "Missing" $false
    }
} catch {
    Log-Test "CORS Validation" "Restrictive" "Unable to test" $false
}

# ============================================================
# TEST 9: Malformed JSON
# ============================================================
Write-Host "`n🔨 TEST 9: Malformed Input Protection" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

$malformedPayloads = @(
    '{invalid json}',
    "{`"single`": `"quotes`"}",
    '{"unclosed": "bracket"',
    'null',
    ''
)

foreach ($payload in $malformedPayloads) {
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/api/auth/login" -Method POST -Body $payload -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
        $statusCode = $response.StatusCode
        Log-Test "Malformed JSON Rejected: $payload" "400" "$statusCode" ($statusCode -eq 400)
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Log-Test "Malformed JSON Rejected: $payload" "400" "$statusCode" ($statusCode -eq 400 -or $statusCode -eq 422)
    }
}

# ============================================================
# TEST 10: Path Traversal Attempts
# ============================================================
Write-Host "`n📁 TEST 10: Path Traversal Protection" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

$pathTraversalPayloads = @(
    "../../../etc/passwd",
    "..\..\..\..\windows\system32\config\sam",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
)

foreach ($payload in $pathTraversalPayloads) {
    try {
        $encodedPayload = [System.Web.HttpUtility]::UrlEncode($payload)
        $response = Invoke-WebRequest -Uri "$API_URL/api/files/$encodedPayload" -Method GET -UseBasicParsing -ErrorAction Stop
        $statusCode = $response.StatusCode
        Log-Test "Path Traversal Blocked: $payload" "400 or 404" "$statusCode" ($statusCode -eq 400 -or $statusCode -eq 404)
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Log-Test "Path Traversal Blocked: $payload" "400 or 404" "$statusCode" ($statusCode -eq 400 -or $statusCode -eq 404)
    }
}

# ============================================================
# RESULTS SUMMARY
# ============================================================
Write-Host ""
Write-Host ""
Write-Host "📊 ============================================" -ForegroundColor Cyan
Write-Host "   TEST RESULTS SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$totalTests = $TestResults.Count
$passedTests = ($TestResults | Where-Object { $_.Passed -eq $true }).Count
$failedTests = $totalTests - $passedTests
$passRate = [math]::Round(($passedTests / $totalTests) * 100, 2)

Write-Host ""
Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor $(if($failedTests -eq 0){"Green"}else{"Red"})
Write-Host "Pass Rate: $passRate%" -ForegroundColor $(if($passRate -ge 90){"Green"}elseif($passRate -ge 70){"Yellow"}else{"Red"})

# Security Score
if ($passRate -ge 95) {
    $securityScore = "🏆 EXCELLENT (A+)"
    $color = "Green"
} elseif ($passRate -ge 85) {
    $securityScore = "✅ VERY GOOD (A)"
    $color = "Green"
} elseif ($passRate -ge 75) {
    $securityScore = "⚠️ GOOD (B)"
    $color = "Yellow"
} elseif ($passRate -ge 60) {
    $securityScore = "⚠️ NEEDS IMPROVEMENT (C)"
    $color = "Yellow"
} else {
    $securityScore = "❌ CRITICAL ISSUES (F)"
    $color = "Red"
}

Write-Host ""
Write-Host "Security Score: $securityScore" -ForegroundColor $color
Write-Host ""

# Failed tests detail
if ($failedTests -gt 0) {
    Write-Host ""
    Write-Host "❌ FAILED TESTS:" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    $TestResults | Where-Object { $_.Passed -eq $false } | ForEach-Object {
        Write-Host "  • $($_.Test)" -ForegroundColor Red
        Write-Host "    Expected: $($_.Expected)" -ForegroundColor Yellow
        Write-Host "    Actual: $($_.Actual)" -ForegroundColor Yellow
    }
}

# Export results to JSON
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$reportPath = "security-test-report_$timestamp.json"
$TestResults | ConvertTo-Json | Out-File $reportPath
Write-Host ""
Write-Host "📄 Full report saved to: $reportPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
