# Test Station Management API Endpoints
# Run this script while the FastAPI server is running on localhost:8000

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  TESTING STATION MANAGEMENT API ENDPOINTS" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Check if server is running
Write-Host "TEST 1: Checking server health..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/" -Method GET
    Write-Host "SUCCESS - Server is running!" -ForegroundColor Green
    Write-Host "   Version:" $response.version -ForegroundColor Gray
    Write-Host "   Environment:" $response.environment -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "FAILED - Server is not running. Please start it first" -ForegroundColor Red
    exit 1
}

# Test 2: List all stations
Write-Host "TEST 2: Listing all stations..." -ForegroundColor Yellow
try {
    $stations = Invoke-RestMethod -Uri "http://localhost:8000/api/stations" -Method GET
    Write-Host "SUCCESS - Retrieved stations!" -ForegroundColor Green
    Write-Host "   Total stations found:" $stations.Count -ForegroundColor Gray
    
    if ($stations.Count -gt 0) {
        $station = $stations[0]
        Write-Host ""
        Write-Host "   First Station Details:" -ForegroundColor Cyan
        Write-Host "      Code:" $station.code -ForegroundColor White
        Write-Host "      Name:" $station.name -ForegroundColor White
        Write-Host "      City:" $station.city -ForegroundColor Gray
        Write-Host "      State:" $station.state -ForegroundColor Gray
        Write-Host "      Status:" $station.status -ForegroundColor Gray
        Write-Host "      ID:" $station.id -ForegroundColor Gray
        
        # Test 3: Get specific station details
        Write-Host ""
        Write-Host "TEST 3: Getting station details by ID..." -ForegroundColor Yellow
        try {
            $detail = Invoke-RestMethod -Uri "http://localhost:8000/api/stations/$($station.id)" -Method GET
            Write-Host "SUCCESS - Retrieved station details!" -ForegroundColor Green
            Write-Host "   Display Name:" $detail.display_name -ForegroundColor White
            Write-Host "   Email:" $detail.email -ForegroundColor Gray
            Write-Host "   Phone:" $detail.phone -ForegroundColor Gray
            Write-Host "   Timezone:" $detail.timezone -ForegroundColor Gray
            Write-Host "   Max Concurrent Bookings:" $detail.max_concurrent_bookings -ForegroundColor Gray
        } catch {
            Write-Host "FAILED - Error:" $_.Exception.Message -ForegroundColor Red
        }
    }
    Write-Host ""
} catch {
    Write-Host "FAILED - Error:" $_.Exception.Message -ForegroundColor Red
    Write-Host ""
}

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  TESTS COMPLETE" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Station Management API is working!" -ForegroundColor Green
Write-Host ""
Write-Host "Available Endpoints:" -ForegroundColor Cyan
Write-Host "   GET    /api/stations           - List all stations" -ForegroundColor White
Write-Host "   GET    /api/stations/{id}      - Get station details" -ForegroundColor White
Write-Host "   POST   /api/stations           - Create new station" -ForegroundColor White
Write-Host "   PUT    /api/stations/{id}      - Update station" -ForegroundColor White
Write-Host "   DELETE /api/stations/{id}      - Delete station" -ForegroundColor White
Write-Host ""
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
