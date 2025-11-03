# Test AI Chat Feature with 100% Database Confidence
Write-Host "`n========== AI CHAT FEATURE TESTING ==========`n" -ForegroundColor Cyan

# Test 1: Payment Methods
Write-Host "Test 1: Payment Methods Query" -ForegroundColor Yellow
$body1 = @{
    message = "What payment methods do you accept?"
} | ConvertTo-Json

try {
    $response1 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/ai/chat" -Method POST -Body $body1 -ContentType "application/json"
    Write-Host "Response: $($response1.response)" -ForegroundColor Green
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host "`n---`n"

# Test 2: Booking Information
Write-Host "Test 2: Booking Information Query" -ForegroundColor Yellow
$body2 = @{
    message = "How do I book a hibachi chef for my event?"
} | ConvertTo-Json

try {
    $response2 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/ai/chat" -Method POST -Body $body2 -ContentType "application/json"
    Write-Host "Response: $($response2.response)" -ForegroundColor Green
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host "`n---`n"

# Test 3: Admin Features
Write-Host "Test 3: Admin Features Query" -ForegroundColor Yellow
$body3 = @{
    message = "What admin features are available in the dashboard?"
} | ConvertTo-Json

try {
    $response3 = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/ai/chat" -Method POST -Body $body3 -ContentType "application/json"
    Write-Host "Response: $($response3.response)" -ForegroundColor Green
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host "`n========== AI CHAT TESTING COMPLETE ==========`n" -ForegroundColor Cyan
