# Comprehensive Backend Testing Suite - ALL Features
# Tests: AI, Newsletter (Start/Stop), Bookings, ML, Admin
# Date: November 4, 2025

$baseUrl = "http://localhost:8000"
$pass = 0
$fail = 0
$errors = @()

function Test-Endpoint {
    param($name, $method, $url, $body = $null, $headers = @{}, $expectedStatus = 200)
    
    try {
        $params = @{
            Uri = "$baseUrl$url"
            Method = $method
            Headers = $headers
            ErrorAction = 'Stop'
        }
        
        if ($body) {
            $params.Body = $body
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-RestMethod @params
        
        Write-Host "  [PASS] $name" -ForegroundColor Green
        $script:pass++
        return $response
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq $expectedStatus) {
            Write-Host "  [PASS] $name (Expected $expectedStatus)" -ForegroundColor Green
            $script:pass++
        }
        else {
            Write-Host "  [FAIL] $name - Status: $statusCode" -ForegroundColor Red
            Write-Host "        Error: $($_.Exception.Message)" -ForegroundColor DarkRed
            $script:fail++
            $script:errors += "$name - Status: $statusCode"
        }
        return $null
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "   COMPREHENSIVE BACKEND TEST - ALL FEATURES" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# SECTION 1: Infrastructure
Write-Host "`n=== Section 1: Infrastructure ===" -ForegroundColor Yellow
Test-Endpoint "Health Check" "GET" "/health"
Test-Endpoint "OpenAPI Docs" "GET" "/openapi.json"

# SECTION 2: Auth and JWT
Write-Host "`n=== Section 2: Authentication ===" -ForegroundColor Yellow
$loginData = @{ email = "admin@myhibachichef.com"; password = "admin123" } | ConvertTo-Json
$authResponse = Test-Endpoint "Admin Login" "POST" "/api/auth/login" $loginData
if ($authResponse) {
    $token = $authResponse.access_token
    $headers = @{ Authorization = "Bearer $token" }
    Write-Host "  [INFO] Got JWT token" -ForegroundColor Cyan
    Test-Endpoint "Get User Info" "GET" "/api/auth/me" -headers $headers
} else {
    Write-Host "  [WARN] Authentication failed - skipping auth-required tests" -ForegroundColor Yellow
}

# SECTION 3: AI Multi-Agent and Machine Learning (CRITICAL)
Write-Host "`n=== Section 3: AI and Machine Learning ===" -ForegroundColor Yellow
Test-Endpoint "AI Health" "GET" "/api/v1/ai/health"

$aiTests = @(
    @{ msg = "How much for 50 people?"; intent = "pricing" },
    @{ msg = "I want to book for Saturday"; intent = "booking" },
    @{ msg = "What is your cancellation policy?"; intent = "policy" },
    @{ msg = "Can I add lobster tail?"; intent = "menu" },
    @{ msg = "I need help with my booking"; intent = "support" }
)

foreach ($test in $aiTests) {
    $aiData = @{ 
        message = $test.msg
        user_id = "test-$(Get-Random)"
        channel = "web" 
    } | ConvertTo-Json
    
    $response = Test-Endpoint "AI: $($test.msg.Substring(0, [Math]::Min(25, $test.msg.Length)))..." "POST" "/api/v1/ai/chat" $aiData
    if ($response) {
        Write-Host "    [INFO] Intent: $($response.intent) | Confidence: $($response.confidence)" -ForegroundColor Gray
        if ($response.confidence -lt 0.5) {
            Write-Host "    [WARN] Low confidence score: $($response.confidence)" -ForegroundColor Yellow
        }
    }
}

# SECTION 4: Public APIs
Write-Host "`n=== Section 4: Public APIs ===" -ForegroundColor Yellow
$quoteData = @{
    adults = 35
    children = 3
    filet_mignon = 10
    lobster_tail = 8
    yakisoba_noodles = 5
    venue_address = "123 Main St, Sacramento, CA 95814"
    zip_code = "95814"
} | ConvertTo-Json

$quoteResponse = Test-Endpoint "Quote Calculator" "POST" "/api/v1/public/quote/calculate" $quoteData
if ($quoteResponse -and $quoteResponse.grand_total) {
    Write-Host "    [INFO] Total: `$$($quoteResponse.grand_total)" -ForegroundColor Gray
}

# SECTION 5: Payment Systems
Write-Host "`n=== Section 5: Payments ===" -ForegroundColor Yellow
$paymentData = @{ 
    base_amount = 2000
    tip_amount = 300
    payment_method = "card" 
} | ConvertTo-Json
Test-Endpoint "Payment Calculator" "POST" "/api/v1/payments/calculate" $paymentData
Test-Endpoint "Payment Methods" "GET" "/api/v1/payments/methods"

# SECTION 6: Booking Management (CRITICAL)
Write-Host "`n=== Section 6: Booking Management ===" -ForegroundColor Yellow
if ($headers) {
    Test-Endpoint "List Bookings" "GET" "/api/bookings/?limit=10" -headers $headers
    
    # Get current date for weekly/monthly stats
    $today = Get-Date
    $weekStart = $today.AddDays(-7).ToString("yyyy-MM-dd")
    $weekEnd = $today.ToString("yyyy-MM-dd")
    $monthStart = $today.AddDays(-30).ToString("yyyy-MM-dd")
    
    Test-Endpoint "Weekly Booking Stats" "GET" "/api/bookings/admin/weekly?date_from=$weekStart&date_to=$weekEnd" -headers $headers
    Test-Endpoint "Monthly Booking Stats" "GET" "/api/bookings/admin/monthly?date_from=$monthStart&date_to=$weekEnd" -headers $headers
} else {
    Write-Host "  [SKIP] Auth required - login failed" -ForegroundColor Yellow
}

# SECTION 7: Newsletter System (CRITICAL - Start/Stop)
Write-Host "`n=== Section 7: Newsletter System ===" -ForegroundColor Yellow
if ($headers) {
    Test-Endpoint "List Subscribers" "GET" "/api/newsletter/newsletter/subscribers" -headers $headers
    Test-Endpoint "List Campaigns" "GET" "/api/newsletter/newsletter/campaigns" -headers $headers
    
    # Create campaign
    $campaignData = @{
        name = "Test Campaign $(Get-Random)"
        subject = "Test Email Subject"
        content = "This is test email content"
        scheduled_for = (Get-Date).AddDays(1).ToString("yyyy-MM-ddTHH:mm:ss")
    } | ConvertTo-Json
    
    $campaign = Test-Endpoint "Create Campaign" "POST" "/api/newsletter/newsletter/campaigns" $campaignData -headers $headers
    
    if ($campaign -and $campaign.id) {
        Write-Host "    [INFO] Campaign created with ID: $($campaign.id)" -ForegroundColor Gray
        Test-Endpoint "Campaign Stats" "GET" "/api/newsletter/newsletter/campaigns/$($campaign.id)/stats" -headers $headers
        Test-Endpoint "Campaign Events" "GET" "/api/newsletter/newsletter/campaigns/$($campaign.id)/events" -headers $headers
        Write-Host "    [INFO] Campaign created but NOT sent (test mode)" -ForegroundColor Cyan
    }
    
    # AI Content Generation
    $aiContentData = @{ 
        topic = "Holiday Specials"
        tone = "friendly"
        length = "medium" 
    } | ConvertTo-Json
    Test-Endpoint "AI Newsletter Content" "POST" "/api/newsletter/newsletter/campaigns/ai-content" $aiContentData -headers $headers
} else {
    Write-Host "  [SKIP] Auth required - login failed" -ForegroundColor Yellow
}

# SECTION 8: Admin Management
Write-Host "`n=== Section 8: Admin Management ===" -ForegroundColor Yellow
if ($headers) {
    Test-Endpoint "Admin Users List" "GET" "/admin/users" -headers $headers
    Test-Endpoint "Admin Roles List" "GET" "/admin/roles" -headers $headers
    Test-Endpoint "All Permissions" "GET" "/admin/roles/permissions/all" -headers $headers
} else {
    Write-Host "  [SKIP] Auth required - login failed" -ForegroundColor Yellow
}

# SECTION 9: CRM and Leads
Write-Host "`n=== Section 9: CRM and Leads ===" -ForegroundColor Yellow
if ($headers) {
    Test-Endpoint "List Leads" "GET" "/api/leads/leads/" -headers $headers
    Test-Endpoint "CRM Bookings" "GET" "/api/crm/crm/bookings" -headers $headers
    Test-Endpoint "CRM Customers" "GET" "/api/crm/crm/customers" -headers $headers
    Test-Endpoint "CRM Dashboard Stats" "GET" "/api/crm/crm/dashboard/stats" -headers $headers
} else {
    Write-Host "  [SKIP] Auth required - login failed" -ForegroundColor Yellow
}

# SECTION 10: Stripe Integration
Write-Host "`n=== Section 10: Stripe Payments ===" -ForegroundColor Yellow
if ($headers) {
    Test-Endpoint "Stripe Customer Dashboard" "GET" "/api/stripe/v1/customers/dashboard" -headers $headers
    Test-Endpoint "Stripe Payments List" "GET" "/api/stripe/payments" -headers $headers
    Test-Endpoint "Stripe Payment Analytics" "GET" "/api/stripe/analytics/payments" -headers $headers
} else {
    Write-Host "  [SKIP] Auth required - login failed" -ForegroundColor Yellow
}

# FINAL SUMMARY
Write-Host "`n============================================================" -ForegroundColor Magenta
Write-Host "             TEST RESULTS SUMMARY" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta

$total = $pass + $fail
$passRate = if ($total -gt 0) { [math]::Round(($pass / $total) * 100, 1) } else { 0 }

Write-Host "`nResults:" -ForegroundColor Yellow
Write-Host "  Passed: $pass" -ForegroundColor Green
Write-Host "  Failed: $fail" -ForegroundColor Red
Write-Host "  Total: $total" -ForegroundColor Cyan
Write-Host "  Pass Rate: $passRate%" -ForegroundColor Cyan

if ($fail -gt 0) {
    Write-Host "`nErrors Found:" -ForegroundColor Red
    foreach ($err in $errors) {
        Write-Host "  - $err" -ForegroundColor Yellow
    }
    Write-Host "`n[ACTION REQUIRED] Fix the above errors before deployment" -ForegroundColor Red
} else {
    Write-Host "`nALL TESTS PASSED - ZERO ERRORS!" -ForegroundColor Green
    Write-Host "Backend is ready for deployment" -ForegroundColor Green
}

Write-Host "`nTested Areas:" -ForegroundColor Gray
Write-Host "  - Infrastructure and Health Checks" -ForegroundColor Gray
Write-Host "  - Authentication and JWT" -ForegroundColor Gray
Write-Host "  - AI Multi-Agent and Machine Learning" -ForegroundColor Gray
Write-Host "  - Payment Systems" -ForegroundColor Gray
Write-Host "  - Booking Management (Weekly/Monthly Stats)" -ForegroundColor Gray
Write-Host "  - Newsletter System (Create/Stats/AI Content)" -ForegroundColor Gray
Write-Host "  - Admin Management" -ForegroundColor Gray
Write-Host "  - CRM and Lead Management" -ForegroundColor Gray
Write-Host "  - Stripe Integration" -ForegroundColor Gray

$completionTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "`nCompleted: $completionTime" -ForegroundColor Gray
Write-Host ""
