# Test Script for Role Switching Feature
# Tests the SUPER_ADMIN role switching functionality

$baseUrl = "http://localhost:8000"
$token = "dev-super-admin-token-2025-for-testing-only"
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

Write-Host "🧪 Testing Role Switching Feature" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "📋 Test 1: Health Check" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Write-Host "✅ Backend is healthy" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Backend health check failed" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 2: Get Available Roles
Write-Host "📋 Test 2: Get Available Roles" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/dev/available-roles" -Headers $headers -Method Get
    Write-Host "✅ Available roles retrieved" -ForegroundColor Green
    Write-Host "   Current Role: $($response.current_role)" -ForegroundColor Gray
    Write-Host "   Available Roles:" -ForegroundColor Gray
    foreach ($role in $response.available_roles) {
        Write-Host "      - $($role.role): $($role.name)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Failed to get available roles" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Get Current Role
Write-Host "📋 Test 3: Get Current Role (Before Switch)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/dev/current-role" -Headers $headers -Method Get
    Write-Host "✅ Current role retrieved" -ForegroundColor Green
    Write-Host "   Current Role: $($response.current_role)" -ForegroundColor Gray
    Write-Host "   Is Switched: $($response.is_switched)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed to get current role" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Switch to Customer Support Role
Write-Host "📋 Test 4: Switch to Customer Support Role" -ForegroundColor Yellow
$switchBody = @{
    target_role = "customer_support"
    duration_minutes = 60
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/dev/switch-role" -Headers $headers -Method Post -Body $switchBody
    Write-Host "✅ Role switched successfully" -ForegroundColor Green
    Write-Host "   Current Role: $($response.current_role)" -ForegroundColor Gray
    Write-Host "   Original Role: $($response.original_role)" -ForegroundColor Gray
    Write-Host "   Expires At: $($response.expires_at)" -ForegroundColor Gray
    Write-Host "   Message: $($response.message)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed to switch role" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: Verify Role Switch
Write-Host "📋 Test 5: Get Current Role (After Switch)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/dev/current-role" -Headers $headers -Method Get
    Write-Host "✅ Current role retrieved" -ForegroundColor Green
    Write-Host "   Current Role: $($response.current_role)" -ForegroundColor Gray
    Write-Host "   Original Role: $($response.original_role)" -ForegroundColor Gray
    Write-Host "   Is Switched: $($response.is_switched)" -ForegroundColor Gray
    Write-Host "   Time Remaining: $($response.time_remaining_minutes) minutes" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed to get current role" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 6: Switch to Station Manager Role
Write-Host "📋 Test 6: Switch to Station Manager Role" -ForegroundColor Yellow
$switchBody = @{
    target_role = "station_manager"
    duration_minutes = 30
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/dev/switch-role" -Headers $headers -Method Post -Body $switchBody
    Write-Host "✅ Role switched successfully" -ForegroundColor Green
    Write-Host "   Current Role: $($response.current_role)" -ForegroundColor Gray
    Write-Host "   Duration: 30 minutes" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed to switch role" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 7: Restore Original Role
Write-Host "📋 Test 7: Restore Original Role" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/dev/restore-role" -Headers $headers -Method Post
    Write-Host "✅ Role restored successfully" -ForegroundColor Green
    Write-Host "   Restored Role: $($response.restored_role)" -ForegroundColor Gray
    Write-Host "   Message: $($response.message)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed to restore role" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 8: Verify Restoration
Write-Host "📋 Test 8: Get Current Role (After Restore)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/dev/current-role" -Headers $headers -Method Get
    Write-Host "✅ Current role retrieved" -ForegroundColor Green
    Write-Host "   Current Role: $($response.current_role)" -ForegroundColor Gray
    Write-Host "   Is Switched: $($response.is_switched)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed to get current role" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "🎉 Role Switching Tests Complete!" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
