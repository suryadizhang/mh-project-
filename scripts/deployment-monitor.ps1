# 🚀 My Hibachi Deployment Monitor & Health Check System (Windows)
# PowerShell version for Windows environments

param(
    [ValidateSet("single", "continuous", "quick")]
    [string]$Mode = "single",
    
    [int]$Interval = 300,
    
    [string]$Environment = "production"
)

# Configuration
$ScriptDir = Split-Path -Parent $MyInv        if ($failedChecks -eq 0) {
            $successChecks = $totalChecks - $failedChecks
            Write-Success "🎉 ALL SYSTEMS HEALTHY ($successChecks/$totalChecks checks passed)"
            Write-Host "✅ System Status: OPERATIONAL" -ForegroundColor Green
        } elseif ($failedChecks -le 2) {
            $successChecks = $totalChecks - $failedChecks
            Write-Warning "⚠️ MINOR ISSUES DETECTED ($successChecks/$totalChecks checks passed)"
            Write-Host "⚠️ System Status: DEGRADED PERFORMANCE" -ForegroundColor Yellow
        } else {
            $successChecks = $totalChecks - $failedChecks
            Write-Error "❌ CRITICAL ISSUES DETECTED ($successChecks/$totalChecks checks passed)"
            Write-Host "❌ System Status: MAJOR OUTAGE" -ForegroundColor Red
        }Command.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$LogDir = Join-Path $ProjectRoot "logs\deployment"
$HealthCheckTimeout = 30

# Ensure log directory exists
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Logging functions
function Write-Log {
    param(
        [string]$Level,
        [string]$Message,
        [ConsoleColor]$Color = "White"
    )
    
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "$Timestamp [$Level] $Message"
    
    Write-Host $LogMessage -ForegroundColor $Color
    Add-Content -Path (Join-Path $LogDir "deployment-monitor.log") -Value $LogMessage
}

function Write-Info { param([string]$Message) Write-Log "INFO" $Message "Cyan" }
function Write-Success { param([string]$Message) Write-Log "SUCCESS" $Message "Green" }
function Write-Warning { param([string]$Message) Write-Log "WARNING" $Message "Yellow" }
function Write-Error { param([string]$Message) Write-Log "ERROR" $Message "Red" }

# Banner
function Show-Banner {
    Write-Host ""
    Write-Host "==============================================================================" -ForegroundColor Magenta
    Write-Host "🚀 MY HIBACHI DEPLOYMENT MONITOR" -ForegroundColor Magenta
    Write-Host "==============================================================================" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "🕐 $(Get-Date)"
    Write-Host "📍 Environment: $Environment"
    Write-Host "📂 Project Root: $ProjectRoot"
    Write-Host ""
}

# Test-UrlHealth function
function Test-UrlHealth {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200,
        [int]$TimeoutSeconds = $HealthCheckTimeout
    )
    
    Write-Info "Checking $Name at $Url"
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSeconds -UseBasicParsing -ErrorAction Stop
        
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Success "✅ $Name`: HTTP $($response.StatusCode) (OK)"
            return $true
        } else {
            Write-Error "❌ $Name`: HTTP $($response.StatusCode) (Expected: $ExpectedStatus)"
            return $false
        }
    }
    catch {
        Write-Error "❌ $Name`: Connection failed - $($_.Exception.Message)"
        return $false
    }
}

function Test-ApiHealth {
    param(
        [string]$BaseUrl,
        [string]$AppName
    )
    
    Write-Info "🔍 Checking $AppName API health..."
    
    # Basic health check
    if (!(Test-UrlHealth "$AppName Health" "$BaseUrl/health")) {
        return $false
    }
    
    # Configuration health check
    if (!(Test-UrlHealth "$AppName Config" "$BaseUrl/health/config")) {
        Write-Warning "⚠️ $AppName configuration health check failed (non-critical)"
    }
    
    # API version check
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/health/config" -TimeoutSec 10 -ErrorAction Stop
        
        if ($response.api_version) {
            Write-Success "📋 $AppName Version: $($response.api_version)"
        }
        
        if ($response.environment) {
            Write-Info "🌍 $AppName Environment: $($response.environment)"
        }
    }
    catch {
        Write-Warning "⚠️ Could not retrieve $AppName version info"
    }
    
    return $true
}

# Application monitoring functions
function Test-CustomerFrontend {
    Write-Info "🛍️ Monitoring Customer Website (Next.js)"
    
    $urls = @(
        "https://myhibachichef.com",
        "https://myhibachichef.com/api/health"
    )
    
    $failed = 0
    foreach ($url in $urls) {
        if (!(Test-UrlHealth "Customer Site" $url)) {
            $failed++
        }
    }
    
    if ($failed -eq 0) {
        Write-Success "✅ Customer Website: All endpoints healthy"
        return $true
    } else {
        Write-Error "❌ Customer Website: $failed/$($urls.Count) endpoints failed"
        return $false
    }
}

function Test-AdminPanel {
    Write-Info "👥 Monitoring Admin Panel (Next.js)"
    
    $urls = @(
        "https://admin.mysticdatanode.net",
        "https://admin.mysticdatanode.net/api/health"
    )
    
    $failed = 0
    foreach ($url in $urls) {
        if (!(Test-UrlHealth "Admin Panel" $url)) {
            $failed++
        }
    }
    
    if ($failed -eq 0) {
        Write-Success "✅ Admin Panel: All endpoints healthy"
        return $true
    } else {
        Write-Error "❌ Admin Panel: $failed/$($urls.Count) endpoints failed"
        return $false
    }
}

function Test-BackendApi {
    Write-Info "🔧 Monitoring Backend API (FastAPI)"
    
    $backendUrl = if ($env:BACKEND_URL) { $env:BACKEND_URL } else { "https://mhapi.mysticdatanode.net" }
    
    if (!(Test-ApiHealth $backendUrl "Backend API")) {
        return $false
    }
    
    # Additional FastAPI-specific checks
    Write-Info "🔍 Running FastAPI-specific health checks..."
    
    # Check OpenAPI docs
    if (!(Test-UrlHealth "API Docs" "$backendUrl/docs")) {
        Write-Warning "⚠️ API documentation not accessible (non-critical)"
    }
    
    # Check metrics endpoint (if available)
    if (Test-UrlHealth "Metrics" "$backendUrl/metrics" 200 5) {
        Write-Success "📊 Metrics endpoint available"
    }
    
    Write-Success "✅ Backend API: All critical endpoints healthy"
    return $true
}

# Database and external service checks
function Test-Database {
    Write-Info "🗄️ Monitoring Database Connectivity"
    
    $backendUrl = if ($env:BACKEND_URL) { $env:BACKEND_URL } else { "https://mhapi.mysticdatanode.net" }
    
    try {
        $response = Invoke-RestMethod -Uri "$backendUrl/health/dependencies" -TimeoutSec 10 -ErrorAction Stop
        
        if ($response.dependencies.database.status -eq "healthy") {
            Write-Success "✅ Database: Connection healthy"
            return $true
        } else {
            Write-Error "❌ Database: Connection unhealthy ($($response.dependencies.database.status))"
            return $false
        }
    }
    catch {
        Write-Warning "⚠️ Database: Health check inconclusive"
        return $false
    }
}

function Test-Redis {
    Write-Info "📦 Monitoring Redis Connectivity"
    
    $backendUrl = if ($env:BACKEND_URL) { $env:BACKEND_URL } else { "https://mhapi.mysticdatanode.net" }
    
    try {
        $response = Invoke-RestMethod -Uri "$backendUrl/health/dependencies" -TimeoutSec 10 -ErrorAction Stop
        
        if ($response.dependencies.redis.status -eq "healthy") {
            Write-Success "✅ Redis: Connection healthy"
            return $true
        } else {
            Write-Error "❌ Redis: Connection unhealthy ($($response.dependencies.redis.status))"
            return $false
        }
    }
    catch {
        Write-Warning "⚠️ Redis: Health check inconclusive"
        return $false
    }
}

function Test-ExternalApis {
    Write-Info "🌐 Monitoring External API Dependencies"
    
    $backendUrl = if ($env:BACKEND_URL) { $env:BACKEND_URL } else { "https://mhapi.mysticdatanode.net" }
    
    try {
        $response = Invoke-RestMethod -Uri "$backendUrl/health/dependencies" -TimeoutSec 15 -ErrorAction Stop
        
        if ($response.dependencies.external_apis) {
            $apis = $response.dependencies.external_apis
            
            foreach ($api in $apis.PSObject.Properties) {
                $name = $api.Name
                $configured = $api.Value.configured
                
                if ($configured) {
                    Write-Success "✅ External API $name`: configured"
                } else {
                    Write-Warning "⚠️ External API $name`: not configured"
                }
            }
        }
    }
    catch {
        Write-Warning "⚠️ External APIs: Health check inconclusive"
    }
}

# GSM and secret management monitoring
function Test-GsmIntegration {
    Write-Info "🔐 Monitoring GSM Secret Management"
    
    $backendUrl = if ($env:BACKEND_URL) { $env:BACKEND_URL } else { "https://mhapi.mysticdatanode.net" }
    
    try {
        $response = Invoke-RestMethod -Uri "$backendUrl/health/config" -TimeoutSec 10 -ErrorAction Stop
        
        if ($response.gsm_available -eq $true) {
            Write-Success "✅ GSM Integration: $($response.secrets_count) secrets loaded"
            return $true
        } else {
            Write-Warning "⚠️ GSM Integration: Not available, using environment variables"
            return $false
        }
    }
    catch {
        Write-Error "❌ GSM Integration: Health check failed"
        return $false
    }
}

# Main monitoring function
function Invoke-HealthChecks {
    $failedChecks = 0
    $totalChecks = 0
    
    Write-Info "🏥 Starting comprehensive health checks..."
    Write-Host ""
    
    # Frontend applications
    $totalChecks++
    if (!(Test-CustomerFrontend)) {
        $failedChecks++
    }
    Write-Host ""
    
    $totalChecks++
    if (!(Test-AdminPanel)) {
        $failedChecks++
    }
    Write-Host ""
    
    # Backend API
    $totalChecks++
    if (!(Test-BackendApi)) {
        $failedChecks++
    }
    Write-Host ""
    
    # Infrastructure
    $totalChecks++
    if (!(Test-Database)) {
        $failedChecks++
    }
    Write-Host ""
    
    $totalChecks++
    if (!(Test-Redis)) {
        $failedChecks++
    }
    Write-Host ""
    
    # External dependencies
    Test-ExternalApis
    Write-Host ""
    
    # Secret management
    Test-GsmIntegration
    Write-Host ""
    
    # Summary
    Write-Host "==============================================================================" -ForegroundColor Magenta
    Write-Host "📊 HEALTH CHECK SUMMARY" -ForegroundColor Magenta
    Write-Host "==============================================================================" -ForegroundColor Magenta
    
    $successRate = [math]::Round((($totalChecks - $failedChecks) * 100 / $totalChecks), 1)
    
    if ($failedChecks -eq 0) {
        Write-Success "🎉 ALL SYSTEMS HEALTHY ($($totalChecks - $failedChecks)/$totalChecks checks passed)"
        Write-Host "✅ System Status: OPERATIONAL" -ForegroundColor Green
    } elseif ($failedChecks -le 2) {
        Write-Warning "⚠️ MINOR ISSUES DETECTED ($($totalChecks - $failedChecks)/$totalChecks checks passed)"
        Write-Host "⚠️ System Status: DEGRADED PERFORMANCE" -ForegroundColor Yellow
    } else {
        Write-Error "❌ CRITICAL ISSUES DETECTED ($($totalChecks - $failedChecks)/$totalChecks checks passed)"
        Write-Host "❌ System Status: MAJOR OUTAGE" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "📈 Overall Health: $successRate%"
    Write-Host "📅 Check Time: $(Get-Date)"
    Write-Host "📝 Detailed logs: $LogDir\deployment-monitor.log"
    
    return $failedChecks
}

# Continuous monitoring mode
function Start-ContinuousMonitoring {
    param([int]$IntervalSeconds)
    
    Write-Info "🔄 Starting continuous monitoring (interval: ${IntervalSeconds}s)"
    Write-Info "Press Ctrl+C to stop"
    
    try {
        while ($true) {
            Clear-Host
            Show-Banner
            Invoke-HealthChecks
            
            Write-Host ""
            Write-Info "⏱️ Sleeping for ${IntervalSeconds}s..."
            Start-Sleep -Seconds $IntervalSeconds
        }
    }
    catch [System.OperationCanceledException] {
        Write-Host "`n🛑 Monitoring stopped by user" -ForegroundColor Yellow
    }
}

# Main script logic
function Main {
    Show-Banner
    
    switch ($Mode) {
        "single" {
            $exitCode = Invoke-HealthChecks
            exit $exitCode
        }
        "continuous" {
            Start-ContinuousMonitoring $Interval
        }
        "quick" {
            Write-Info "🚀 Quick health check mode"
            Test-CustomerFrontend
            Test-AdminPanel
            Test-BackendApi
        }
        default {
            Write-Host "Usage: .\deployment-monitor.ps1 [-Mode <single|continuous|quick>] [-Interval <seconds>]"
            Write-Host ""
            Write-Host "Modes:"
            Write-Host "  single      - Run health checks once (default)"
            Write-Host "  continuous  - Run health checks continuously"
            Write-Host "  quick       - Quick check of main applications only"
            Write-Host ""
            Write-Host "Examples:"
            Write-Host "  .\deployment-monitor.ps1                           # Single run"
            Write-Host "  .\deployment-monitor.ps1 -Mode continuous -Interval 180  # Every 3 minutes"
            Write-Host "  .\deployment-monitor.ps1 -Mode quick              # Quick check"
            exit 1
        }
    }
}

# Handle Ctrl+C gracefully
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Write-Host "`n🛑 Monitoring stopped" -ForegroundColor Yellow
}

# Run the script
Main
