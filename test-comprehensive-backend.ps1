# Comprehensive Backend Testing Script
# Tests analytics endpoints, review endpoints, and all major API categories

$baseUrl = "http://localhost:8000"
$passCount = 0
$failCount = 0
$warnCount = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int[]]$ExpectedCodes = @(200, 401, 404, 405),
        [string]$Method = "GET"
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method $Method -UseBasicParsing -ErrorAction Stop
        $code = $response.StatusCode
        
        if ($code -in $ExpectedCodes) {
            Write-Host "   $Name " -ForegroundColor Green -NoNewline
            Write-Host "($code)" -ForegroundColor Gray
            $script:passCount++
            return $true
        } else {
            Write-Host "    $Name " -ForegroundColor Yellow -NoNewline
            Write-Host "($code - unexpected)" -ForegroundColor Gray
            $script:warnCount++
            return $false
        }
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        
        if ($code -in $ExpectedCodes) {
            Write-Host "   $Name " -ForegroundColor Green -NoNewline
            Write-Host "($code)" -ForegroundColor Gray
            $script:passCount++
            return $true
        } elseif ($code -eq 500) {
            Write-Host "   $Name " -ForegroundColor Red -NoNewline
            Write-Host "(500 - INTERNAL ERROR)" -ForegroundColor Red
            Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Gray
            $script:failCount++
            return $false
        } else {
            Write-Host "    $Name " -ForegroundColor Yellow -NoNewline
            Write-Host "($code)" -ForegroundColor Gray
            $script:warnCount++
            return $false
        }
    }
}

Write-Host "`n COMPREHENSIVE BACKEND TESTING`n" -ForegroundColor Cyan

# Test 1: Analytics Endpoints (Fixed async/await)
Write-Host " Analytics Endpoints (6 endpoints):" -ForegroundColor Cyan
Test-Endpoint "Overview" "$baseUrl/api/admin/analytics/overview"
Test-Endpoint "Leads" "$baseUrl/api/admin/analytics/leads"
Test-Endpoint "Newsletter" "$baseUrl/api/admin/analytics/newsletter"
Test-Endpoint "Funnel" "$baseUrl/api/admin/analytics/funnel"
Test-Endpoint "Lead Scoring" "$baseUrl/api/admin/analytics/lead-scoring"
Test-Endpoint "Engagement" "$baseUrl/api/admin/analytics/engagement-trends"

# Test 2: Review Moderation Endpoints (Missing table?)
Write-Host "`n Review Moderation Endpoints (7 endpoints):" -ForegroundColor Cyan
Test-Endpoint "Pending Reviews" "$baseUrl/api/admin/review-moderation/pending-reviews"
Test-Endpoint "Stats" "$baseUrl/api/admin/review-moderation/stats"
Test-Endpoint "Approval Log" "$baseUrl/api/admin/review-moderation/approval-log/1"
Test-Endpoint "Approve (POST)" "$baseUrl/api/admin/review-moderation/approve-review/1" @(200, 401, 404, 405) "POST"
Test-Endpoint "Reject (POST)" "$baseUrl/api/admin/review-moderation/reject-review/1" @(200, 401, 404, 405) "POST"
Test-Endpoint "Hold (POST)" "$baseUrl/api/admin/review-moderation/hold-review/1" @(200, 401, 404, 405) "POST"
Test-Endpoint "Bulk Action (POST)" "$baseUrl/api/admin/review-moderation/bulk-action" @(200, 401, 404, 405, 422) "POST"

# Test 3: Lead Management
Write-Host "`n Lead Management Endpoints:" -ForegroundColor Cyan
Test-Endpoint "Get Leads" "$baseUrl/api/leads/leads"
Test-Endpoint "Lead Details" "$baseUrl/api/leads/leads/1"
Test-Endpoint "Public Lead Capture" "$baseUrl/api/v1/public/leads" @(200, 405, 422) "POST"

# Test 4: Newsletter
Write-Host "`n Newsletter Endpoints:" -ForegroundColor Cyan
Test-Endpoint "Subscribers" "$baseUrl/api/newsletter/newsletter/subscribers"
Test-Endpoint "Campaigns" "$baseUrl/api/newsletter/newsletter/campaigns"

# Test 5: Stations
Write-Host "`n Station Management:" -ForegroundColor Cyan
Test-Endpoint "Get Stations" "$baseUrl/api/stations/"
Test-Endpoint "Station Details" "$baseUrl/api/stations/1"

# Test 6: Customer Reviews
Write-Host "`n Customer Review System:" -ForegroundColor Cyan
Test-Endpoint "Submit Review" "$baseUrl/api/customer-reviews/submit-review" @(200, 405, 422) "POST"
Test-Endpoint "Public Reviews" "$baseUrl/api/customer-reviews/reviews"

# Test 7: AI Chat
Write-Host "`n AI Chat Endpoints:" -ForegroundColor Cyan
Test-Endpoint "AI Chat" "$baseUrl/api/v1/ai/chat" @(200, 405, 422) "POST"
Test-Endpoint "Chat Sessions" "$baseUrl/api/v1/ai/sessions"

# Test 8: Unified Inbox
Write-Host "`n Unified Inbox:" -ForegroundColor Cyan
Test-Endpoint "Messages" "$baseUrl/v1/inbox/messages"
Test-Endpoint "Unread Count" "$baseUrl/v1/inbox/unread-count"

# Test 9: Health Checks
Write-Host "`n  Health Endpoints:" -ForegroundColor Cyan
Test-Endpoint "Basic Health" "$baseUrl/health" @(200)
Test-Endpoint "Detailed Health" "$baseUrl/api/v1/health/detailed"
Test-Endpoint "Liveness" "$baseUrl/api/health/live" @(200)
Test-Endpoint "Readiness" "$baseUrl/api/health/ready" @(200)
Test-Endpoint "Startup" "$baseUrl/api/health/startup" @(200)

# Test 10: Payment Calculator
Write-Host "`n Payment Calculator:" -ForegroundColor Cyan
Test-Endpoint "Calculate Payment" "$baseUrl/api/v1/calculator/calculate" @(200, 405, 422) "POST"

# Summary
Write-Host "`n TEST SUMMARY" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host " Passed:  $passCount" -ForegroundColor Green
Write-Host "  Warnings: $warnCount" -ForegroundColor Yellow
Write-Host " Failed:  $failCount" -ForegroundColor Red

$total = $passCount + $warnCount + $failCount
$passRate = [math]::Round(($passCount / $total) * 100, 1)

Write-Host "`nPass Rate: $passRate%" -ForegroundColor $(if ($passRate -ge 90) { "Green" } elseif ($passRate -ge 70) { "Yellow" } else { "Red" })

if ($failCount -gt 0) {
    Write-Host "`n CRITICAL: $failCount endpoint(s) returning 500 errors!" -ForegroundColor Red
    Write-Host "   These need immediate attention before production." -ForegroundColor Red
} elseif ($warnCount -gt 0) {
    Write-Host "`n  $warnCount endpoint(s) returned unexpected codes (may be OK)" -ForegroundColor Yellow
} else {
    Write-Host "`n All endpoints responding as expected!" -ForegroundColor Green
}

Write-Host ""

