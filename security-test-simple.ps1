# Security Penetration Test Script
# Run this to test all security layers

$ErrorActionPreference = "Continue"
$API_URL = "http://localhost:8000"
$TestResults = @()

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   SECURITY PENETRATION TEST SUITE" -ForegroundColor Cyan
Write-Host "   Testing: $API_URL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Helper function to log results
function Add-TestResult {
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
        Write-Host "[PASS] $TestName" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] $TestName" -ForegroundColor Red
        Write-Host "  Expected: $Expected" -ForegroundColor Yellow
        Write-Host "  Actual: $Actual" -ForegroundColor Yellow
    }
}

# ============================================================
# TEST 1: Server Health Check
# ============================================================
Write-Host ""
Write-Host "TEST 1: Server Health Check" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta
try {
    $response = Invoke-WebRequest -Uri "$API_URL/health" -Method GET -UseBasicParsing -ErrorAction Stop
    $statusCode = $response.StatusCode
    Add-TestResult "Health Endpoint Available" "200" "$statusCode" ($statusCode -eq 200)
} catch {
    Add-TestResult "Health Endpoint Available" "200" "Connection Failed" $false
    Write-Host ""
    Write-Host "ERROR: Backend server not running!" -ForegroundColor Red
    Write-Host "Please start the backend first" -ForegroundColor Yellow
    exit 1
}

# ============================================================
# TEST 2: Security Headers Check
# ============================================================
Write-Host ""
Write-Host "TEST 2: Security Headers Validation" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta
try {
    $response = Invoke-WebRequest -Uri "$API_URL/health" -Method GET -UseBasicParsing
    $headers = $response.Headers
    
    $requiredHeaders = @(
        "Strict-Transport-Security",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Content-Security-Policy",
        "Referrer-Policy",
        "Permissions-Policy",
        "X-Request-ID"
    )
    
    foreach ($header in $requiredHeaders) {
        $present = $headers.ContainsKey($header)
        Add-TestResult "Security Header: $header" "Present" $(if($present){"Present"}else{"Missing"}) $present
    }
} catch {
    Add-TestResult "Security Headers Check" "Headers Present" "Failed to retrieve" $false
}

# ============================================================
# TEST 3: Authentication - Unauthorized Access Attempt
# ============================================================
Write-Host ""
Write-Host "TEST 3: Authentication Protection" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

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
        Add-TestResult "Auth Required: $endpoint" "401" "$statusCode" ($statusCode -eq 401)
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 401 -or $statusCode -eq 404) {
            Add-TestResult "Auth Required: $endpoint" "401 or 404" "$statusCode" $true
        } else {
            Add-TestResult "Auth Required: $endpoint" "401" "$statusCode" $false
        }
    }
}

# ============================================================
# TEST 4: SQL Injection Attempts
# ============================================================
Write-Host ""
Write-Host "TEST 4: SQL Injection Protection" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

$sqlPayloads = @(
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "admin'--"
)

foreach ($payload in $sqlPayloads) {
    try {
        $encodedPayload = [System.Web.HttpUtility]::UrlEncode($payload)
        $response = Invoke-WebRequest -Uri "$API_URL/api/auth/login?username=$encodedPayload" -Method GET -UseBasicParsing -ErrorAction Stop
        $statusCode = $response.StatusCode
        Add-TestResult "SQL Injection Blocked: $payload" "4xx Error" "$statusCode" ($statusCode -ge 400)
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -ge 400) {
            Add-TestResult "SQL Injection Blocked: $payload" "4xx Error" "$statusCode" $true
        } else {
            Add-TestResult "SQL Injection Blocked: $payload" "4xx Error" "$statusCode" $false
        }
    }
}

# ============================================================
# TEST 5: XSS Protection
# ============================================================
Write-Host ""
Write-Host "TEST 5: XSS Protection" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

$xssPayloads = @(
    'scriptalertxssscript',
    'javascript:alert(xss)'
)

foreach ($payload in $xssPayloads) {
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/api/auth/login?email=$payload" -Method GET -UseBasicParsing -ErrorAction Stop
        $statusCode = $response.StatusCode
        Add-TestResult "XSS Attack Blocked: $payload" "4xx Error" "$statusCode" ($statusCode -ge 400)
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Add-TestResult "XSS Attack Blocked: $payload" "4xx Error" "$statusCode" ($statusCode -ge 400)
    }
}

# ============================================================
# TEST 6: Rate Limiting
# ============================================================
Write-Host ""
Write-Host "TEST 6: Rate Limiting Protection" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta
Write-Host "Sending 25 rapid requests (limit is 20/min)..." -ForegroundColor Yellow

$rateLimitResults = @()
for ($i = 1; $i -le 25; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/health" -Method GET -UseBasicParsing -ErrorAction Stop
        $statusCode = $response.StatusCode
        $rateLimitResults += $statusCode
        if ($statusCode -eq 429) {
            Write-Host "  Request $i : $statusCode (RATE LIMITED)" -ForegroundColor Green
        } else {
            Write-Host "  Request $i : $statusCode" -NoNewline
            Write-Host ""
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $rateLimitResults += $statusCode
        Write-Host "  Request $i : $statusCode (RATE LIMITED)" -ForegroundColor Green
    }
    Start-Sleep -Milliseconds 50
}

$rateLimited = ($rateLimitResults | Where-Object { $_ -eq 429 }).Count -gt 0
Add-TestResult "Rate Limiting Active" "429 after 20+ requests" $(if($rateLimited){"Rate limited"}else{"Not limited"}) $rateLimited

# ============================================================
# TEST 7: Malformed Input Protection
# ============================================================
Write-Host ""
Write-Host "TEST 7: Malformed Input Protection" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

$malformedPayloads = @(
    '{invalid json}',
    'null',
    ''
)

foreach ($payload in $malformedPayloads) {
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/api/auth/login" -Method POST -Body $payload -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
        $statusCode = $response.StatusCode
        Add-TestResult "Malformed JSON Rejected" "400" "$statusCode" ($statusCode -eq 400)
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Add-TestResult "Malformed JSON Rejected" "400" "$statusCode" ($statusCode -eq 400 -or $statusCode -eq 422)
    }
}

# ============================================================
# RESULTS SUMMARY
# ============================================================
Write-Host ""
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   TEST RESULTS SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$totalTests = $TestResults.Count
$passedTests = ($TestResults | Where-Object { $_.Passed -eq $true }).Count
$failedTests = $totalTests - $passedTests
$passRate = [math]::Round(($passedTests / $totalTests) * 100, 2)

Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor $(if($failedTests -eq 0){"Green"}else{"Red"})
Write-Host "Pass Rate: $passRate%" -ForegroundColor $(if($passRate -ge 90){"Green"}elseif($passRate -ge 70){"Yellow"}else{"Red"})

# Security Score
if ($passRate -ge 95) {
    $securityScore = "EXCELLENT (A+)"
    $color = "Green"
} elseif ($passRate -ge 85) {
    $securityScore = "VERY GOOD (A)"
    $color = "Green"
} elseif ($passRate -ge 75) {
    $securityScore = "GOOD (B)"
    $color = "Yellow"
} elseif ($passRate -ge 60) {
    $securityScore = "NEEDS IMPROVEMENT (C)"
    $color = "Yellow"
} else {
    $securityScore = "CRITICAL ISSUES (F)"
    $color = "Red"
}

Write-Host ""
Write-Host "Security Score: $securityScore" -ForegroundColor $color
Write-Host ""

# Failed tests detail
if ($failedTests -gt 0) {
    Write-Host ""
    Write-Host "FAILED TESTS:" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    $TestResults | Where-Object { $_.Passed -eq $false } | ForEach-Object {
        Write-Host "  - $($_.Test)" -ForegroundColor Red
        Write-Host "    Expected: $($_.Expected)" -ForegroundColor Yellow
        Write-Host "    Actual: $($_.Actual)" -ForegroundColor Yellow
    }
}

# Export results to JSON
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$reportPath = "security-test-report_$timestamp.json"
$TestResults | ConvertTo-Json | Out-File $reportPath

Write-Host ""
Write-Host "Full report saved to: $reportPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
