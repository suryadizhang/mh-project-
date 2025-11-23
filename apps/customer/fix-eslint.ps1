# Quick ESLint Fix Script
# This script fixes remaining React unescaped entities and <a> → <Link /> issues

$ErrorActionPreference = "Continue"

Write-Host "Fixing remaining ESLint errors..." -ForegroundColor Cyan

# Fix apostrophes in review pages
Write-Host "`nFixing apostrophes..." -ForegroundColor Yellow

# src/app/review/[id]/page.tsx - line 231
$file1 = "src\app\review\[id]\page.tsx"
if (Test-Path $file1) {
    (Get-Content $file1 -Raw) -replace "We're glad", "We&apos;re glad" | Set-Content $file1 -NoNewline
    Write-Host "  ✓ Fixed $file1"
}

# src/app/review/[id]/thank-you/page.tsx - lines 78, 139, 195
$file2 = "src\app\review\[id]\thank-you\page.tsx"
if (Test-Path $file2) {
    $content = Get-Content $file2 -Raw
    $content = $content -replace "We're thrilled", "We&apos;re thrilled"
    $content = $content -replace "you're redirecting", "you&apos;re redirecting"
    $content = $content -replace "We'd love", "We&apos;d love"
    $content | Set-Content $file2 -NoNewline
    Write-Host "  ✓ Fixed $file2"
}

# src/components/payment/AlternativePayerField.tsx - line 260
$file3 = "src\components\payment\AlternativePayerField.tsx"
if (Test-Path $file3) {
    (Get-Content $file3 -Raw) -replace "someone else's card", "someone else&apos;s card" | Set-Content $file3 -NoNewline
    Write-Host "  ✓ Fixed $file3"
}

# src/components/reviews/CustomerReviewForm.tsx - line 306
$file4 = "src\components\reviews\CustomerReviewForm.tsx"
if (Test-Path $file4) {
    (Get-Content $file4 -Raw) -replace "We're committed", "We&apos;re committed" | Set-Content $file4 -NoNewline
    Write-Host "  ✓ Fixed $file4"
}

Write-Host "`nAll apostrophes fixed!" -ForegroundColor Green

Write-Host "`nNote: <a> → <Link /> conversions require manual import additions" -ForegroundColor Yellow
Write-Host "Run 'npm run lint' to see remaining issues" -ForegroundColor Cyan
