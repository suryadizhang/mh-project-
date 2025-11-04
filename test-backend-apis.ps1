# 🧪 Backend API Comprehensive Test Script
# Run this script to test ALL backend APIs systematically

Write-Host "`n🎯 COMPREHENSIVE BACKEND API TEST SUITE" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"
$testResults = @()
$totalTests = 0
$passedTests = 0
$failedTests = 0

# Test result tracking function
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Body = @{},
        [hashtable]$Headers = @{ "Content-Type" = "application/json" },
        [int]$ExpectedStatus = 200
    )
    
    $script:totalTests++
    Write-Host "`n🧪 Testing: $Name" -ForegroundColor Yellow
    
    try {
        $params = @{
            Uri = "$baseUrl$Endpoint"
            Method = $Method
            Headers = $Headers
            TimeoutSec = 30
        }
        
        if ($Body.Count -gt 0) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params -ErrorAction Stop
        
        Write-Host "  ✅ PASS: $Name" -ForegroundColor Green
        $script:passedTests++
        $script:testResults += [PSCustomObject]@{
            Test = $Name
            Status = "PASS"
            Details = "Status 200 OK"
        }
        return $response
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq $ExpectedStatus) {
            Write-Host "  ✅ PASS: $Name (Expected $ExpectedStatus)" -ForegroundColor Green
            $script:passedTests++
            $script:testResults += [PSCustomObject]@{
                Test = $Name
                Status = "PASS"
                Details = "Expected status $ExpectedStatus"
            }
        }
        else {
            Write-Host "  ❌ FAIL: $Name" -ForegroundColor Red
            Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Red
            $script:failedTests++
            $script:testResults += [PSCustomObject]@{
                Test = $Name
                Status = "FAIL"
                Details = $_.Exception.Message
            }
        }
        return $null
    }
}

# ====================
# Phase 1: Health Checks
# ====================
Write-Host "`n`n📋 PHASE 1: HEALTH CHECKS" -ForegroundColor Magenta
Write-Host "==========================" -ForegroundColor Magenta

Test-Endpoint -Name "Basic Health Check" -Method GET -Endpoint "/api/health"
Test-Endpoint -Name "Kubernetes Health Check" -Method GET -Endpoint "/api/v1/health"
Test-Endpoint -Name "Comprehensive Monitoring" -Method GET -Endpoint "/api/v1/health/comprehensive"

# ====================
# Phase 2: Public APIs (No Auth)
# ====================
Write-Host "`n`n📋 PHASE 2: PUBLIC APIs (NO AUTH REQUIRED)" -ForegroundColor Magenta
Write-Host "===========================================" -ForegroundColor Magenta

# Test Public Quote Calculator
$quoteRequest = @{
    adults = 2
    children = 0
    salmon = 0
    scallops = 0
    filet_mignon = 0
    lobster_tail = 0
    third_proteins = 0
    yakisoba_noodles = 0
    extra_fried_rice = 0
    extra_vegetables = 0
    edamame = 0
    gyoza = 0
    venue_address = "1600 Amphitheatre Parkway, Mountain View, CA"
    zip_code = "94043"
}
$quoteResponse = Test-Endpoint -Name "Public Quote Calculation" -Method POST -Endpoint "/api/v1/public/quote/calculate" -Body $quoteRequest

if ($quoteResponse) {
    Write-Host "     Base Total: `$$($quoteResponse.base_total)" -ForegroundColor Cyan
    Write-Host "     Grand Total: `$$($quoteResponse.grand_total)" -ForegroundColor Cyan
    if ($quoteResponse.travel_info) {
        Write-Host "     Travel Distance: $($quoteResponse.travel_info.distance_miles) miles" -ForegroundColor Cyan
        Write-Host "     Travel Fee: `$$($quoteResponse.travel_info.travel_fee)" -ForegroundColor Cyan
    }
}

# Test Public Lead Capture
$leadRequest = @{
    name = "Test Customer"
    email = "test@example.com"
    phone = "+19167408768"
    event_date = "2025-12-01"
    guest_count = 20
    message = "Test lead from API testing"
}
Test-Endpoint -Name "Public Lead Capture" -Method POST -Endpoint "/api/v1/public/leads" -Body $leadRequest

# ====================
# Phase 3: OpenAPI Documentation
# ====================
Write-Host "`n`n📋 PHASE 3: API DOCUMENTATION" -ForegroundColor Magenta
Write-Host "==============================" -ForegroundColor Magenta

Test-Endpoint -Name "OpenAPI Schema" -Method GET -Endpoint "/openapi.json"
Write-Host "`n  📄 API Docs available at: $baseUrl/docs" -ForegroundColor Cyan

# ====================
# Phase 4: List Available Endpoints
# ====================
Write-Host "`n`n📋 PHASE 4: DISCOVERING AVAILABLE ENDPOINTS" -ForegroundColor Magenta
Write-Host "===========================================" -ForegroundColor Magenta

try {
    $openapi = Invoke-RestMethod -Uri "$baseUrl/openapi.json" -Method GET
    
    Write-Host "`n  📊 Total Endpoints: $($openapi.paths.PSObject.Properties.Count)" -ForegroundColor Green
    
    # Group by prefix
    $endpoints = @{}
    foreach ($path in $openapi.paths.PSObject.Properties) {
        $pathName = $path.Name
        $prefix = ($pathName -split '/')[1..2] -join '/'
        if (-not $endpoints.ContainsKey($prefix)) {
            $endpoints[$prefix] = @()
        }
        $endpoints[$prefix] += $pathName
    }
    
    Write-Host "`n  📂 Endpoint Groups:" -ForegroundColor Yellow
    foreach ($group in ($endpoints.Keys | Sort-Object)) {
        Write-Host "     /$group - $($endpoints[$group].Count) endpoints" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "  ⚠️ Could not retrieve OpenAPI schema" -ForegroundColor Yellow
}

# ====================
# Test Summary
# ====================
Write-Host "`n`n📊 TEST SUMMARY" -ForegroundColor Magenta
Write-Host "================" -ForegroundColor Magenta
Write-Host "  Total Tests: $totalTests" -ForegroundColor Cyan
Write-Host "  Passed: $passedTests" -ForegroundColor Green
Write-Host "  Failed: $failedTests" -ForegroundColor $(if($failedTests -gt 0){"Red"}else{"Green"})
Write-Host "  Success Rate: $([math]::Round(($passedTests/$totalTests)*100, 2))%" -ForegroundColor Cyan

# Display detailed results
Write-Host "`n📋 DETAILED RESULTS:" -ForegroundColor Yellow
$testResults | Format-Table -AutoSize

# Save results to file
$testResults | Export-Csv -Path "api_test_results_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv" -NoTypeInformation
Write-Host "`n💾 Results saved to: api_test_results_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv" -ForegroundColor Green

# ====================
# Next Steps
# ====================
Write-Host "`n`n🚀 NEXT STEPS:" -ForegroundColor Magenta
Write-Host "==============" -ForegroundColor Magenta
Write-Host "  1. Review failed tests above" -ForegroundColor Yellow
Write-Host "  2. Test authenticated endpoints (requires auth token)" -ForegroundColor Yellow
Write-Host "  3. Test database operations (CRUD)" -ForegroundColor Yellow
Write-Host "  4. Test AI features" -ForegroundColor Yellow
Write-Host "  5. Test payment integrations" -ForegroundColor Yellow
Write-Host "  6. Test social media webhooks" -ForegroundColor Yellow

Write-Host "`n✅ Basic API testing complete!" -ForegroundColor Green
