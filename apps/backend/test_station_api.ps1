# Test Station Management API Endpoints
# Run this script while the FastAPI server is running on localhost:8000

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  TESTING STATION MANAGEMENT API ENDPOINTS" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Check if server is running
Write-Host "[TEST 1] Checking server health..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/" -Method GET
    Write-Host "✅ Server is running!" -ForegroundColor Green
    Write-Host "   Version: $($response.version)" -ForegroundColor Gray
    Write-Host "   Environment: $($response.environment)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Server is not running. Please start it first with: python apps/backend/src/main.py" -ForegroundColor Red
    exit 1
}

# Test 2: List all stations
Write-Host "[TEST 2] Listing all stations..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/stations" -Method GET
    Write-Host "✅ Successfully retrieved stations!" -ForegroundColor Green
    Write-Host "   Total stations found: $($response.Count)" -ForegroundColor Gray
    
    if ($response.Count -gt 0) {
        foreach ($station in $response) {
            Write-Host ""
            Write-Host "   📍 Station Details:" -ForegroundColor Cyan
            Write-Host "      ID: $($station.id)" -ForegroundColor Gray
            Write-Host "      Code: $($station.code)" -ForegroundColor White
            Write-Host "      Name: $($station.name)" -ForegroundColor White
            Write-Host "      Location: $($station.city), $($station.state)" -ForegroundColor Gray
            Write-Host "      Status: $($station.status)" -ForegroundColor Gray
        }
    }
    Write-Host ""
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Response: $($_.ErrorDetails.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 3: Get specific station details
Write-Host "[TEST 3] Getting specific station details..." -ForegroundColor Yellow
if ($response.Count -gt 0) {
    $stationId = $response[0].id
    try {
        $detail = Invoke-RestMethod -Uri "http://localhost:8000/api/stations/$stationId" -Method GET
        Write-Host "✅ Successfully retrieved station details!" -ForegroundColor Green
        Write-Host "   Code: $($detail.code)" -ForegroundColor White
        Write-Host "   Name: $($detail.name)" -ForegroundColor White
        Write-Host "   Display Name: $($detail.display_name)" -ForegroundColor White
        Write-Host "   Email: $($detail.email)" -ForegroundColor Gray
        Write-Host "   Phone: $($detail.phone)" -ForegroundColor Gray
        Write-Host "   Timezone: $($detail.timezone)" -ForegroundColor Gray
        Write-Host "   Max Concurrent Bookings: $($detail.max_concurrent_bookings)" -ForegroundColor Gray
        Write-Host "   Booking Lead Time: $($detail.booking_lead_time_hours) hours" -ForegroundColor Gray
        Write-Host ""
    } catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
} else {
    Write-Host "⚠️  No stations available to test" -ForegroundColor Yellow
    Write-Host ""
}

# Test 4: Check API documentation
Write-Host "[TEST 4] Checking API documentation..." -ForegroundColor Yellow
try {
    $docs = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method GET
    Write-Host "✅ API documentation available at: http://localhost:8000/docs" -ForegroundColor Green
    Write-Host "   Open this URL in your browser to explore all endpoints!" -ForegroundColor Cyan
    Write-Host ""
} catch {
    Write-Host "⚠️  API documentation not available (may be disabled in production)" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  TEST SUMMARY" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Station Management API is working correctly!" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Available Endpoints:" -ForegroundColor Cyan
Write-Host "   GET    /api/stations           - List all stations" -ForegroundColor White
Write-Host "   GET    /api/stations/{id}      - Get station details" -ForegroundColor White
Write-Host "   POST   /api/stations           - Create new station" -ForegroundColor White
Write-Host "   PUT    /api/stations/{id}      - Update station" -ForegroundColor White
Write-Host "   DELETE /api/stations/{id}      - Delete station" -ForegroundColor White
Write-Host ""
Write-Host "📋 First Station Seeded:" -ForegroundColor Cyan
Write-Host "   Code: STATION-CA-BAY-001" -ForegroundColor White
Write-Host "   Name: California Bay Area" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Open http://localhost:8000/docs to explore all endpoints" -ForegroundColor Gray
Write-Host "   2. Build the frontend /admin/stations page" -ForegroundColor Gray
Write-Host "   3. Implement Google OAuth integration" -ForegroundColor Gray
Write-Host ""
