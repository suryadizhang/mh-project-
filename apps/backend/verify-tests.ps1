# Test Suite Verification Script - My Hibachi Backend
# November 27, 2025
#
# Runs pytest and generates a detailed test report after endpoint migration.

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "My Hibachi Test Suite Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set backend root
$backendRoot = "c:\Users\surya\projects\MH webapps\apps\backend"
$srcRoot = "$backendRoot\src"
$testsRoot = "$backendRoot\tests"

# Verify test directory exists
if (-not (Test-Path $testsRoot)) {
    Write-Host "❌ Tests directory not found: $testsRoot" -ForegroundColor Red
    exit 1
}

# Count test files
$testFiles = Get-ChildItem -Path $testsRoot -Recurse -Filter "test_*.py"
$testCount = $testFiles.Count

Write-Host "📊 Test Suite Information:" -ForegroundColor Cyan
Write-Host "   Test directory: $testsRoot" -ForegroundColor Gray
Write-Host "   Test files found: $testCount" -ForegroundColor Gray
Write-Host ""

if ($testCount -eq 0) {
    Write-Host "⚠️  No test files found!" -ForegroundColor Yellow
    exit 0
}

# Set environment
cd $backendRoot
$env:PYTHONPATH = $srcRoot

Write-Host "🧪 Running pytest..." -ForegroundColor Cyan
Write-Host ""

# Run pytest with detailed output
$reportFile = "$backendRoot\test-results.txt"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Header
@"
========================================
My Hibachi Test Suite Results
Generated: $timestamp
========================================

"@ | Out-File -FilePath $reportFile -Encoding UTF8

# Run pytest
$pytestOutput = pytest tests/ -v --tb=short --maxfail=10 2>&1 | Tee-Object -Append -FilePath $reportFile

# Parse results
$passed = ($pytestOutput | Select-String -Pattern " PASSED" -AllMatches).Matches.Count
$failed = ($pytestOutput | Select-String -Pattern " FAILED" -AllMatches).Matches.Count
$skipped = ($pytestOutput | Select-String -Pattern " SKIPPED" -AllMatches).Matches.Count
$errors = ($pytestOutput | Select-String -Pattern " ERROR" -AllMatches).Matches.Count

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Results Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  ✅ PASSED:  $passed" -ForegroundColor Green
Write-Host "  ❌ FAILED:  $failed" -ForegroundColor Red
Write-Host "  ⏭️  SKIPPED: $skipped" -ForegroundColor Yellow
Write-Host "  ⚠️  ERRORS:  $errors" -ForegroundColor Red
Write-Host ""
Write-Host "  📄 Full report saved to: test-results.txt" -ForegroundColor Gray
Write-Host ""

# Calculate pass rate
$total = $passed + $failed + $errors
if ($total -gt 0) {
    $passRate = [math]::Round(($passed / $total) * 100, 1)

    if ($passRate -ge 80) {
        Write-Host "  🎉 Pass Rate: $passRate% (EXCELLENT)" -ForegroundColor Green
    } elseif ($passRate -ge 60) {
        Write-Host "  ⚠️  Pass Rate: $passRate% (NEEDS IMPROVEMENT)" -ForegroundColor Yellow
    } else {
        Write-Host "  ❌ Pass Rate: $passRate% (CRITICAL)" -ForegroundColor Red
    }
} else {
    Write-Host "  ⚠️  No tests executed" -ForegroundColor Yellow
}

Write-Host ""

# Recommendations
if ($failed -gt 0 -or $errors -gt 0) {
    Write-Host "📋 Recommendations:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1. Review failed tests in test-results.txt" -ForegroundColor White
    Write-Host "  2. Check if failures are due to migration changes" -ForegroundColor White
    Write-Host "  3. Update tests to match new architecture" -ForegroundColor White
    Write-Host "  4. Re-run: pytest tests/ -v --tb=long" -ForegroundColor White
    Write-Host ""
}

# Migration-specific checks
Write-Host "🔍 Migration-Specific Checks:" -ForegroundColor Cyan
Write-Host ""

# Check for tests importing from deprecated locations
$deprecatedTestImports = Get-ChildItem -Path $testsRoot -Recurse -Filter "*.py" |
    Select-String -Pattern "from models_DEPRECATED|from core\.auth_DEPRECATED|from src\.models\." |
    Where-Object { $_.Line -notmatch "^\s*#" }

if ($deprecatedTestImports.Count -gt 0) {
    Write-Host "  ⚠️  Found $($deprecatedTestImports.Count) test files importing from old locations" -ForegroundColor Yellow
    Write-Host ""
    $deprecatedTestImports | Select-Object -First 5 | ForEach-Object {
        Write-Host "     $($_.Path):$($_.LineNumber)" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "  Action: Update test imports to use db.models.* instead" -ForegroundColor White
} else {
    Write-Host "  ✅ All tests use correct import paths" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Test Verification Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
