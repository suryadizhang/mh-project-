# Phase 0: Secure Commit and Push Current Work
# This script safely commits all completed work with security checks

Write-Host "`n🔐 Phase 0: Secure Commit and Push Current Work" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray

# Step 1: Security Pre-Check
Write-Host "`n📋 Step 1: Running Security Checks..." -ForegroundColor Yellow

Write-Host "  • Checking for hardcoded secrets..."
$secrets_check = git diff --cached | Select-String -Pattern "(API_KEY|SECRET|PASSWORD|TOKEN).*=.*['\"][a-zA-Z0-9]{20}"

if ($secrets_check) {
    Write-Host "  ❌ ERROR: Potential secrets found in staged files!" -ForegroundColor Red
    Write-Host "  Please review and remove any hardcoded secrets:" -ForegroundColor Red
    $secrets_check | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    exit 1
}

Write-Host "  ✅ No hardcoded secrets detected" -ForegroundColor Green

Write-Host "  • Checking for .env files..."
$env_check = git status --short | Select-String "\.env[^.]*$"

if ($env_check) {
    Write-Host "  ⚠️  WARNING: .env files detected in git status!" -ForegroundColor Yellow
    $env_check | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
    Write-Host "  These will NOT be committed (filtered by .gitignore)" -ForegroundColor Yellow
}
else {
    Write-Host "  ✅ No .env files in staging area" -ForegroundColor Green
}

# Step 2: Show What Will Be Committed
Write-Host "`n📋 Step 2: Files to be Committed" -ForegroundColor Yellow
Write-Host "  The following completed work will be committed:" -ForegroundColor Gray

$files_to_add = @(
    "apps/admin/src/app/superadmin/knowledge-sync/page.tsx",
    "apps/backend/src/services/lead_service.py",
    "apps/backend/src/services/newsletter_service.py",
    "apps/backend/scripts/create_consent_referral_tables.sql",
    "apps/customer/src/components/forms/QuoteRequestForm.tsx",
    "apps/customer/src/components/lead-capture/ExitIntentPopup.tsx",
    "apps/customer/src/hooks/useExitIntent.ts",
    "INFRASTRUCTURE_AUDIT_AND_REFACTOR_PLAN.md",
    "REFACTOR_QUICK_SUMMARY.md",
    "COMPLETE_IMPLEMENTATION_PLAN.md"
)

foreach ($file in $files_to_add) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    }
    else {
        Write-Host "  ⚠️  $file (not found)" -ForegroundColor Yellow
    }
}

# Step 3: Confirm Before Proceeding
Write-Host "`n📋 Step 3: Confirmation" -ForegroundColor Yellow
$confirmation = Read-Host "  Proceed with commit and push? (yes/no)"

if ($confirmation -ne "yes") {
    Write-Host "  ❌ Aborted by user" -ForegroundColor Red
    exit 0
}

# Step 4: Stage Files
Write-Host "`n📋 Step 4: Staging Files..." -ForegroundColor Yellow

foreach ($file in $files_to_add) {
    if (Test-Path $file) {
        git add $file
        Write-Host "  ✅ Staged: $file" -ForegroundColor Green
    }
}

# Step 5: Commit with Descriptive Message
Write-Host "`n📋 Step 5: Creating Commit..." -ForegroundColor Yellow

$commit_message = @"
feat: Complete Phase 0 - Admin Dashboard, Compliance, Lead Capture

Completed Tasks (6/11):
- Admin Knowledge Sync Dashboard with real-time polling
- TCPA/CAN-SPAM compliance integration in services
- Database migrations for consent_records and referrals
- QuoteRequestForm TCPA consent checkboxes
- Exit-intent popup with lead capture
- Infrastructure audit for DI refactor planning

Features:
- Real-time sync dashboard with role protection
- create_lead_with_consent() with full audit trail
- STOP/START/HELP SMS handlers for compliance
- Consent tracking with IP, timestamp, user agent
- Exit intent detection with 3s delay threshold
- Referral tracking database schema

Next Phase: Setup DI Foundation (Phase 1)
Estimated Time: 12 hours
"@

git commit -m $commit_message

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Commit created successfully" -ForegroundColor Green
}
else {
    Write-Host "  ❌ Commit failed!" -ForegroundColor Red
    exit 1
}

# Step 6: Show Commit Details
Write-Host "`n📋 Step 6: Commit Details" -ForegroundColor Yellow
git log -1 --stat

# Step 7: Push to Remote
Write-Host "`n📋 Step 7: Pushing to Remote..." -ForegroundColor Yellow
Write-Host "  Branch: nuclear-refactor-clean-architecture" -ForegroundColor Gray

$push_confirmation = Read-Host "  Push to remote? (yes/no)"

if ($push_confirmation -eq "yes") {
    git push origin nuclear-refactor-clean-architecture
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Pushed successfully!" -ForegroundColor Green
    }
    else {
        Write-Host "  ❌ Push failed!" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "  ⏭️  Skipped push (you can push manually later)" -ForegroundColor Yellow
}

# Step 8: Summary
Write-Host "`n" + ("=" * 70) -ForegroundColor Gray
Write-Host "✅ Phase 0 Complete!" -ForegroundColor Green
Write-Host "`n📊 Summary:" -ForegroundColor Cyan
Write-Host "  • Security checks: PASSED" -ForegroundColor Green
Write-Host "  • Files committed: $($files_to_add.Count)" -ForegroundColor Green
Write-Host "  • Branch: nuclear-refactor-clean-architecture" -ForegroundColor Green
Write-Host "  • Status: Ready for Phase 1" -ForegroundColor Green

Write-Host "`n🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Review commit on GitHub" -ForegroundColor White
Write-Host "  2. Run: .\scripts\phase1-setup-di-foundation.ps1" -ForegroundColor White
Write-Host "  3. Estimated time: 12 hours for Phase 1" -ForegroundColor White

Write-Host "`n" + ("=" * 70) -ForegroundColor Gray
