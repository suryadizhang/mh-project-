# Archive Cleanup Script - My Hibachi Backend
# November 27, 2025
#
# This script safely removes deprecated directories after endpoint migration verification.
# Run this ONLY after confirming all endpoints work (410 endpoints, zero errors).

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "My Hibachi Archive Cleanup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set backend root
$backendRoot = "c:\Users\surya\projects\MH webapps\apps\backend"
$srcRoot = "$backendRoot\src"

# Define directories to clean
$deprecatedDirs = @(
    "$srcRoot\models_DEPRECATED_DO_NOT_USE",
    "$srcRoot\core\auth_DEPRECATED_DO_NOT_USE",
    "$backendRoot\backups_20251125_211908",
    "$backendRoot\backups",
    "$backendRoot\archive_old_reports"
)

# Safety check: Verify backend loads first
Write-Host "🔍 SAFETY CHECK: Verifying backend loads without errors..." -ForegroundColor Yellow
cd $srcRoot
$env:PYTHONPATH = $srcRoot

$testLoad = python -c "from main import app; import sys; sys.exit(0)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ SAFETY CHECK FAILED!" -ForegroundColor Red
    Write-Host "Backend does NOT load correctly. DO NOT proceed with cleanup." -ForegroundColor Red
    Write-Host ""
    Write-Host "Fix errors first, then re-run this script." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Backend loads successfully" -ForegroundColor Green
Write-Host ""

# Check for active imports from deprecated locations
Write-Host "🔍 Checking for active imports from deprecated locations..." -ForegroundColor Yellow
$deprecatedImports = Get-ChildItem -Path $srcRoot -Recurse -Filter "*.py" |
    Select-String -Pattern "from models_DEPRECATED|from core\.auth_DEPRECATED" |
    Where-Object { $_.Line -notmatch "^\s*#" }  # Exclude comments

if ($deprecatedImports.Count -gt 0) {
    Write-Host "⚠️  WARNING: Found active imports from deprecated locations!" -ForegroundColor Red
    Write-Host ""
    $deprecatedImports | ForEach-Object {
        Write-Host "  $($_.Path):$($_.LineNumber) - $($_.Line.Trim())" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Fix these imports before proceeding with cleanup." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ No active imports from deprecated locations" -ForegroundColor Green
Write-Host ""

# Display what will be deleted
Write-Host "📁 Directories scheduled for cleanup:" -ForegroundColor Cyan
Write-Host ""
foreach ($dir in $deprecatedDirs) {
    if (Test-Path $dir) {
        $size = (Get-ChildItem -Path $dir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "  📦 $dir" -ForegroundColor Yellow
        Write-Host "     Size: $([math]::Round($size, 2)) MB" -ForegroundColor Gray
    } else {
        Write-Host "  ⏭️  $dir (already deleted)" -ForegroundColor Gray
    }
}
Write-Host ""

# Confirmation prompt
Write-Host "⚠️  WARNING: This will PERMANENTLY delete the above directories!" -ForegroundColor Red
Write-Host ""
$confirmation = Read-Host "Type 'DELETE' to proceed with cleanup (or anything else to cancel)"

if ($confirmation -ne "DELETE") {
    Write-Host ""
    Write-Host "❌ Cleanup cancelled by user" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "🗑️  Starting cleanup..." -ForegroundColor Cyan
Write-Host ""

# Delete each directory
foreach ($dir in $deprecatedDirs) {
    if (Test-Path $dir) {
        try {
            Write-Host "  Deleting: $dir" -ForegroundColor Yellow
            Remove-Item -Path $dir -Recurse -Force
            Write-Host "  ✅ Deleted successfully" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ Failed to delete: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⏭️  Skipped (already deleted): $dir" -ForegroundColor Gray
    }
    Write-Host ""
}

# Final verification
Write-Host "🔍 FINAL VERIFICATION: Testing backend load after cleanup..." -ForegroundColor Yellow
cd $srcRoot
$env:PYTHONPATH = $srcRoot

$finalTest = python -c "from main import app; routes = [r.path for r in app.routes if hasattr(r, 'path')]; print(f'Endpoints: {len(routes)}'); import sys; sys.exit(0)" 2>&1 | Select-String -Pattern "Endpoints:"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Backend still loads correctly after cleanup" -ForegroundColor Green
    Write-Host "   $finalTest" -ForegroundColor Cyan
} else {
    Write-Host "❌ WARNING: Backend load failed after cleanup!" -ForegroundColor Red
    Write-Host "   Restore from Git: git checkout HEAD -- src/" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Cleanup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Commit changes: git add . && git commit -m 'Clean up deprecated directories'" -ForegroundColor White
Write-Host "  2. Run test suite: pytest tests/ -v" -ForegroundColor White
Write-Host "  3. Deploy to staging" -ForegroundColor White
Write-Host ""
