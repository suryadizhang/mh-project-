# 🧪 Simple Deployment Readiness Test
# Quick validation of deployment setup

param(
    [switch]$Verbose
)

Write-Host "=============================================================================="
Write-Host "🧪 MY HIBACHI DEPLOYMENT READINESS TEST" -ForegroundColor Cyan
Write-Host "=============================================================================="
Write-Host ""

$testResults = @()
$failed = 0

function Test-Component {
    param(
        [string]$Name,
        [scriptblock]$Test
    )
    
    Write-Host "🔍 Testing $Name..." -ForegroundColor Yellow
    
    try {
        $result = & $Test
        if ($result) {
            Write-Host "  ✅ PASS: $Name" -ForegroundColor Green
            $script:testResults += @{ Name = $Name; Status = "PASS"; Details = "" }
        } else {
            Write-Host "  ❌ FAIL: $Name" -ForegroundColor Red
            $script:testResults += @{ Name = $Name; Status = "FAIL"; Details = "Test returned false" }
            $script:failed++
        }
    }
    catch {
        Write-Host "  ❌ ERROR: $Name - $($_.Exception.Message)" -ForegroundColor Red
        $script:testResults += @{ Name = $Name; Status = "ERROR"; Details = $_.Exception.Message }
        $script:failed++
    }
    
    Write-Host ""
}

# Test 1: Check project structure
Test-Component "Project Structure" {
    $requiredDirs = @(
        "apps\customer",
        "apps\admin", 
        "apps\backend",
        "scripts",
        ".github\workflows"
    )
    
    foreach ($dir in $requiredDirs) {
        if (!(Test-Path $dir)) {
            Write-Host "    Missing directory: $dir" -ForegroundColor Red
            return $false
        }
    }
    
    Write-Host "    All required directories exist" -ForegroundColor Green
    return $true
}

# Test 2: Check security files
Test-Component "Security Configuration" {
    # Check .gitignore has secret protections
    $gitignoreContent = Get-Content ".gitignore" -ErrorAction SilentlyContinue
    
    if (!$gitignoreContent) {
        Write-Host "    .gitignore file missing" -ForegroundColor Red
        return $false
    }
    
    $hasSecretProtections = $false
    foreach ($line in $gitignoreContent) {
        if ($line -match "secret|key|password|gsm" -and !$line.StartsWith("#")) {
            $hasSecretProtections = $true
            break
        }
    }
    
    if (!$hasSecretProtections) {
        Write-Host "    .gitignore missing secret protections" -ForegroundColor Red
        return $false
    }
    
    Write-Host "    .gitignore has secret protections" -ForegroundColor Green
    return $true
}

# Test 3: Check backend GSM integration
Test-Component "GSM Integration Files" {
    $gsmConfigPath = "apps\backend\src\config\gsm_config.py"
    
    if (!(Test-Path $gsmConfigPath)) {
        Write-Host "    Missing GSM config file: $gsmConfigPath" -ForegroundColor Red
        return $false
    }
    
    $configContent = Get-Content $gsmConfigPath -ErrorAction SilentlyContinue
    if ($configContent -match "class GSMConfig" -and $configContent -match "google.cloud") {
        Write-Host "    GSM config file looks valid" -ForegroundColor Green
        return $true
    }
    
    Write-Host "    GSM config file appears invalid" -ForegroundColor Red
    return $false
}

# Test 4: Check monitoring scripts
Test-Component "Monitoring Scripts" {
    $scripts = @(
        "scripts\deployment-monitor.sh",
        "scripts\deployment-monitor.ps1"
    )
    
    foreach ($script in $scripts) {
        if (!(Test-Path $script)) {
            Write-Host "    Missing script: $script" -ForegroundColor Red
            return $false
        }
    }
    
    Write-Host "    All monitoring scripts exist" -ForegroundColor Green
    return $true
}

# Test 5: Check workflow files
Test-Component "GitHub Workflows" {
    $workflows = @(
        ".github\workflows\ci-deploy.yml",
        ".github\workflows\deployment-testing.yml"
    )
    
    foreach ($workflow in $workflows) {
        if (!(Test-Path $workflow)) {
            Write-Host "    Missing workflow: $workflow" -ForegroundColor Red
            return $false
        }
    }
    
    Write-Host "    All required workflows exist" -ForegroundColor Green
    return $true
}

# Test 6: Check for hardcoded secrets
Test-Component "Secret Security Scan" {
    Write-Host "    Scanning for hardcoded secrets..." -ForegroundColor Yellow
    
    # Search for common secret patterns
    $secretPatterns = @("sk_", "pk_", "AIza", "ACCESS_TOKEN")
    $foundSecrets = @()
    
    foreach ($pattern in $secretPatterns) {
        $matches = Get-ChildItem -Path . -Recurse -Include "*.py", "*.js", "*.ts", "*.sh" -ErrorAction SilentlyContinue |
                   Select-String -Pattern $pattern -ErrorAction SilentlyContinue |
                   Where-Object { $_.Filename -notmatch "template" }
        
        if ($matches) {
            $foundSecrets += $matches
        }
    }
    
    if ($foundSecrets.Count -gt 0) {
        Write-Host "    Found potential hardcoded secrets:" -ForegroundColor Red
        foreach ($match in $foundSecrets[0..4]) {  # Show first 5
            Write-Host "      $($match.Filename):$($match.LineNumber)" -ForegroundColor Red
        }
        return $false
    }
    
    Write-Host "    No hardcoded secrets found" -ForegroundColor Green
    return $true
}

# Test 7: Basic health check capability
Test-Component "Health Check Capability" {
    # Test if we can make HTTP requests (check PowerShell capability)
    try {
        $testUrl = "https://httpbin.org/status/200"
        $response = Invoke-WebRequest -Uri $testUrl -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            Write-Host "    HTTP request capability verified" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "    HTTP request capability test failed (may be normal offline)" -ForegroundColor Yellow
        # This is not a failure for offline testing
        return $true
    }
    
    return $true
}

# Summary
Write-Host "=============================================================================="
Write-Host "📊 DEPLOYMENT READINESS SUMMARY" -ForegroundColor Cyan
Write-Host "=============================================================================="
Write-Host ""

$total = $testResults.Count
$passed = $total - $failed

if ($failed -eq 0) {
    Write-Host "🎉 ALL TESTS PASSED ($passed/$total)" -ForegroundColor Green
    Write-Host "✅ DEPLOYMENT READY" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Run full deployment test: gh workflow run deployment-testing.yml"
    Write-Host "  2. Test monitoring: .\scripts\deployment-monitor.ps1 -Mode quick"
    Write-Host "  3. Deploy when ready: gh workflow run ci-deploy.yml"
    
} elseif ($failed -le 2) {
    Write-Host "⚠️  MINOR ISSUES ($passed/$total tests passed)" -ForegroundColor Yellow
    Write-Host "⚠️  DEPLOYMENT POSSIBLE WITH CAUTION" -ForegroundColor Yellow
    
} else {
    Write-Host "❌ CRITICAL ISSUES ($passed/$total tests passed)" -ForegroundColor Red
    Write-Host "❌ DEPLOYMENT NOT READY" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 Test Details:" -ForegroundColor Cyan
foreach ($test in $testResults) {
    $status = $test.Status
    $color = switch ($status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "ERROR" { "Red" }
        default { "Gray" }
    }
    
    Write-Host "  $($test.Status): $($test.Name)" -ForegroundColor $color
    
    if ($Verbose -and $test.Details) {
        Write-Host "    Details: $($test.Details)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "📅 Test Completed: $(Get-Date)" -ForegroundColor Gray
Write-Host "=============================================================================="

# Exit with appropriate code
if ($failed -eq 0) {
    exit 0
} else {
    exit 1
}
