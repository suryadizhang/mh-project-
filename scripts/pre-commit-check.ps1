#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Pre-commit quality gate for My Hibachi codebase.

.DESCRIPTION
    Runs comprehensive quality checks before any commit:
    - SSoT compliance (no hardcoded business values)
    - Build verification (customer + admin apps)
    - Backend import check
    - Type safety scan
    - Security scan
    - Debug code detection
    - Test execution

.EXAMPLE
    .\scripts\pre-commit-check.ps1

.NOTES
    Run from project root: c:\Users\surya\projects\MH webapps
    See: .github/instructions/22-QUALITY_CONTROL.instructions.md
#>

param(
  [switch]$SkipBuild,     # Skip frontend builds (faster)
  [switch]$SkipTests,     # Skip test execution (faster)
  [switch]$Verbose        # Show more details
)

$ErrorActionPreference = "Continue"
$ProjectRoot = "c:\Users\surya\projects\MH webapps"
$ErrorCount = 0
$WarningCount = 0

# Change to project root
Set-Location $ProjectRoot

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "         MY HIBACHI - PRE-COMMIT QUALITY GATE              " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# 1. SSoT COMPLIANCE SCAN
# ============================================================================
Write-Host "[1/10] SSoT Compliance Scan..." -ForegroundColor Yellow

$ssotPatterns = @(
  '\$55',
  '\$30',
  '\$100',
  '\$550',
  '5500',     # adult_price_cents
  '3000',     # child_price_cents
  '55000',    # party_minimum_cents
  '10000'     # deposit_amount_cents
)

$ssotViolations = @()

foreach ($pattern in $ssotPatterns) {
  $matches = Get-ChildItem -Path "apps" -Recurse -Include "*.ts", "*.tsx", "*.py" -ErrorAction SilentlyContinue |
  Select-String -Pattern $pattern -ErrorAction SilentlyContinue |
  Where-Object {
    $_.Line -notmatch '(//|/\*|\*|#|test|mock|spec|example|\.d\.ts|node_modules|__pycache__|\.test\.|\.spec\.)' -and
    $_.Path -notmatch '(node_modules|__pycache__|\.next|dist|coverage)'
  }

  if ($matches) {
    $ssotViolations += $matches
  }
}

if ($ssotViolations.Count -gt 0) {
  Write-Host "  ⚠️  Potential SSoT violations found ($($ssotViolations.Count)):" -ForegroundColor Yellow
  $ssotViolations | ForEach-Object {
    $relativePath = $_.Path.Replace($ProjectRoot, "").TrimStart("\")
    Write-Host "     $relativePath`:$($_.LineNumber)" -ForegroundColor Yellow
  }
  $WarningCount++
}
else {
  Write-Host "  ✅ SSoT compliance OK - No hardcoded business values" -ForegroundColor Green
}

# ============================================================================
# 2. CUSTOMER APP BUILD
# ============================================================================
if (-not $SkipBuild) {
  Write-Host "`n[2/10] Customer App Build..." -ForegroundColor Yellow
  Push-Location "$ProjectRoot\apps\customer"
  try {
    $buildOutput = npm run build 2>&1
    if ($LASTEXITCODE -eq 0) {
      Write-Host "  ✅ Customer build passed" -ForegroundColor Green
    }
    else {
      Write-Host "  ❌ Customer build FAILED" -ForegroundColor Red
      if ($Verbose) { Write-Host $buildOutput }
      $ErrorCount++
    }
  }
  catch {
    Write-Host "  ❌ Customer build error: $_" -ForegroundColor Red
    $ErrorCount++
  }
  Pop-Location
}
else {
  Write-Host "`n[2/10] Customer App Build... SKIPPED" -ForegroundColor Gray
}

# ============================================================================
# 3. ADMIN APP BUILD
# ============================================================================
if (-not $SkipBuild) {
  Write-Host "`n[3/10] Admin App Build..." -ForegroundColor Yellow
  Push-Location "$ProjectRoot\apps\admin"
  try {
    $buildOutput = npm run build 2>&1
    if ($LASTEXITCODE -eq 0) {
      Write-Host "  ✅ Admin build passed" -ForegroundColor Green
    }
    else {
      Write-Host "  ❌ Admin build FAILED" -ForegroundColor Red
      if ($Verbose) { Write-Host $buildOutput }
      $ErrorCount++
    }
  }
  catch {
    Write-Host "  ❌ Admin build error: $_" -ForegroundColor Red
    $ErrorCount++
  }
  Pop-Location
}
else {
  Write-Host "`n[3/10] Admin App Build... SKIPPED" -ForegroundColor Gray
}

# ============================================================================
# 4. BACKEND IMPORT CHECK
# ============================================================================
Write-Host "`n[4/10] Backend Import Check..." -ForegroundColor Yellow
Push-Location "$ProjectRoot\apps\backend\src"
try {
  $pythonOutput = python -c "from main import app; print('OK')" 2>&1
  if ($LASTEXITCODE -eq 0 -and $pythonOutput -match "OK") {
    Write-Host "  ✅ Backend imports OK" -ForegroundColor Green
  }
  else {
    Write-Host "  ❌ Backend import FAILED" -ForegroundColor Red
    if ($Verbose) { Write-Host $pythonOutput }
    $ErrorCount++
  }
}
catch {
  Write-Host "  ❌ Backend import error: $_" -ForegroundColor Red
  $ErrorCount++
}
Pop-Location

# ============================================================================
# 5. TYPE SAFETY SCAN (No `any` types)
# ============================================================================
Write-Host "`n[5/10] Type Safety Scan..." -ForegroundColor Yellow

$anyTypes = Get-ChildItem -Path "apps/customer/src", "apps/admin/src" -Recurse -Include "*.ts", "*.tsx" -ErrorAction SilentlyContinue |
Select-String -Pattern ': any\b|as any\b' -ErrorAction SilentlyContinue |
Where-Object {
  $_.Path -notmatch '(node_modules|\.d\.ts|test|spec|mock)' -and
  $_.Line -notmatch '// eslint-disable'
}

if ($anyTypes.Count -gt 0) {
  Write-Host "  ⚠️  Found 'any' types ($($anyTypes.Count)):" -ForegroundColor Yellow
  $anyTypes | Select-Object -First 5 | ForEach-Object {
    $relativePath = $_.Path.Replace($ProjectRoot, "").TrimStart("\")
    Write-Host "     $relativePath`:$($_.LineNumber)" -ForegroundColor Yellow
  }
  if ($anyTypes.Count -gt 5) {
    Write-Host "     ... and $($anyTypes.Count - 5) more" -ForegroundColor Yellow
  }
  $WarningCount++
}
else {
  Write-Host "  ✅ Type safety OK - No 'any' types found" -ForegroundColor Green
}

# ============================================================================
# 6. SECURITY SCAN (Secrets, SQL injection patterns)
# ============================================================================
Write-Host "`n[6/10] Security Scan..." -ForegroundColor Yellow

$securityPatterns = @(
  'password\s*=\s*[''"][^''"]{3,}',
  'api_key\s*=\s*[''"][^''"]{10,}',
  'secret\s*=\s*[''"][^''"]{10,}',
  'sk_live_',
  'pk_live_'
)

$securityIssues = @()

foreach ($pattern in $securityPatterns) {
  $matches = Get-ChildItem -Path "apps" -Recurse -Include "*.ts", "*.tsx", "*.py" -ErrorAction SilentlyContinue |
  Select-String -Pattern $pattern -ErrorAction SilentlyContinue |
  Where-Object {
    $_.Path -notmatch '(node_modules|\.env\.example|test|mock|spec)'
  }

  if ($matches) {
    $securityIssues += $matches
  }
}

if ($securityIssues.Count -gt 0) {
  Write-Host "  ⚠️  Potential security issues ($($securityIssues.Count)):" -ForegroundColor Red
  $securityIssues | ForEach-Object {
    $relativePath = $_.Path.Replace($ProjectRoot, "").TrimStart("\")
    Write-Host "     $relativePath`:$($_.LineNumber)" -ForegroundColor Red
  }
  $WarningCount++
}
else {
  Write-Host "  ✅ Security OK - No exposed secrets detected" -ForegroundColor Green
}

# ============================================================================
# 7. DEBUG CODE SCAN (console.log, print, debugger)
# ============================================================================
Write-Host "`n[7/10] Debug Code Scan..." -ForegroundColor Yellow

$debugPatterns = @(
  'console\.log\(',
  'console\.debug\(',
  '\bdebugger\b'
)

$debugCode = @()

foreach ($pattern in $debugPatterns) {
  $matches = Get-ChildItem -Path "apps/customer/src", "apps/admin/src" -Recurse -Include "*.ts", "*.tsx" -ErrorAction SilentlyContinue |
  Select-String -Pattern $pattern -ErrorAction SilentlyContinue |
  Where-Object {
    $_.Path -notmatch '(node_modules|test|spec|mock|\.test\.|\.spec\.)' -and
    $_.Line -notmatch '// eslint-disable'
  }

  if ($matches) {
    $debugCode += $matches
  }
}

if ($debugCode.Count -gt 0) {
  Write-Host "  ⚠️  Debug code found ($($debugCode.Count)):" -ForegroundColor Yellow
  $debugCode | Select-Object -First 5 | ForEach-Object {
    $relativePath = $_.Path.Replace($ProjectRoot, "").TrimStart("\")
    Write-Host "     $relativePath`:$($_.LineNumber)" -ForegroundColor Yellow
  }
  $WarningCount++
}
else {
  Write-Host "  ✅ Debug code OK - No console.log/debugger found" -ForegroundColor Green
}

# ============================================================================
# 8. FRONTEND TESTS
# ============================================================================
if (-not $SkipTests) {
  Write-Host "`n[8/10] Frontend Tests..." -ForegroundColor Yellow
  Push-Location "$ProjectRoot\apps\customer"
  try {
    $testOutput = npm test -- --run 2>&1
    if ($LASTEXITCODE -eq 0) {
      Write-Host "  ✅ Frontend tests passed" -ForegroundColor Green
    }
    else {
      Write-Host "  ❌ Frontend tests FAILED" -ForegroundColor Red
      if ($Verbose) { Write-Host $testOutput }
      $ErrorCount++
    }
  }
  catch {
    Write-Host "  ❌ Frontend tests error: $_" -ForegroundColor Red
    $ErrorCount++
  }
  Pop-Location
}
else {
  Write-Host "`n[8/10] Frontend Tests... SKIPPED" -ForegroundColor Gray
}

# ============================================================================
# 9. TODO/FIXME SCAN
# ============================================================================
Write-Host "`n[9/10] TODO/FIXME Scan..." -ForegroundColor Yellow

$todos = Get-ChildItem -Path "apps/customer/src", "apps/admin/src", "apps/backend/src" -Recurse -Include "*.ts", "*.tsx", "*.py" -ErrorAction SilentlyContinue |
Select-String -Pattern 'TODO|FIXME|HACK|XXX' -ErrorAction SilentlyContinue |
Where-Object {
  $_.Path -notmatch '(node_modules|__pycache__|\.d\.ts)'
}

if ($todos.Count -gt 0) {
  Write-Host "  ⚠️  Found TODO/FIXME comments ($($todos.Count)):" -ForegroundColor Yellow
  $todos | Select-Object -First 3 | ForEach-Object {
    $relativePath = $_.Path.Replace($ProjectRoot, "").TrimStart("\")
    Write-Host "     $relativePath`:$($_.LineNumber)" -ForegroundColor Yellow
  }
  if ($todos.Count -gt 3) {
    Write-Host "     ... and $($todos.Count - 3) more" -ForegroundColor Yellow
  }
  # TODOs are warnings, not errors
}
else {
  Write-Host "  ✅ No TODO/FIXME comments found" -ForegroundColor Green
}

# ============================================================================
# 10. GIT DIFF REMINDER
# ============================================================================
Write-Host "`n[10/10] Git Diff Review..." -ForegroundColor Yellow
Write-Host "  ℹ️  Remember to run: git diff --staged" -ForegroundColor Cyan
Write-Host "  ℹ️  Review every changed line before committing" -ForegroundColor Cyan

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan

if ($ErrorCount -gt 0) {
  Write-Host "  ❌ QUALITY GATE FAILED" -ForegroundColor Red
  Write-Host "     $ErrorCount error(s), $WarningCount warning(s)" -ForegroundColor Red
  Write-Host ""
  Write-Host "  Fix errors before committing!" -ForegroundColor Red
  Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
  exit 1
}
elseif ($WarningCount -gt 0) {
  Write-Host "  ⚠️  QUALITY GATE PASSED WITH WARNINGS" -ForegroundColor Yellow
  Write-Host "     $WarningCount warning(s) - review before committing" -ForegroundColor Yellow
  Write-Host ""
  Write-Host "  Proceed with caution!" -ForegroundColor Yellow
  Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
  exit 0
}
else {
  Write-Host "  ✅ QUALITY GATE PASSED" -ForegroundColor Green
  Write-Host "     All checks passed - ready to commit!" -ForegroundColor Green
  Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
  exit 0
}
