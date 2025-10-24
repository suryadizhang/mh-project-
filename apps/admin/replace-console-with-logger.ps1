# PowerShell Script to Replace Console Statements with Logger
# Run from: apps/admin directory
# Usage: .\replace-console-with-logger.ps1

Write-Host "🔧 Starting console.log → logger replacement..." -ForegroundColor Cyan
Write-Host ""

# Files to update (remaining 28 console statements in 12 files)
$filesToUpdate = @(
    "src/app/page.tsx",
    "src/app/invoices/[bookingId]/page.tsx",
    "src/app/login/page.tsx",
    "src/app/discounts/page.tsx",
    "src/services/ai-api.ts",
    "src/components/AdminChatWidget.tsx",
    "src/components/BaseLocationManager.tsx",
    "src/components/StationManager.tsx",
    "src/components/PaymentManagement.tsx",
    "src/components/SEOAutomationDashboard.tsx",
    "src/components/ChatBot.tsx",
    "src/components/BaseLocationManager-simplified.tsx"
)

$totalFiles = $filesToUpdate.Count
$filesProcessed = 0
$totalReplacements = 0

foreach ($file in $filesToUpdate) {
    $filesProcessed++
    $filePath = Join-Path $PSScriptRoot $file
    
    if (!(Test-Path $filePath)) {
        Write-Host "⚠️  [$filesProcessed/$totalFiles] File not found: $file" -ForegroundColor Yellow
        continue
    }
    
    Write-Host "📝 [$filesProcessed/$totalFiles] Processing: $file" -ForegroundColor White
    
    # Read file content
    $content = Get-Content $filePath -Raw
    $originalContent = $content
    $replacements = 0
    
    # Check if logger is already imported
    if ($content -notmatch "import.*logger.*from.*@/lib/logger") {
        Write-Host "   ✚ Adding logger import..." -ForegroundColor Gray
        
        # Find the last import statement
        if ($content -match "(?s)(.*?import[^;]+;)") {
            # Add logger import after last import
            $content = $content -replace "(import[^;]+;)(\s*\n)", "`$1`n`nimport { logger } from '@/lib/logger';`$2"
            $replacements++
        }
    }
    
    # Replace console.log with logger.debug
    $consoleLogMatches = [regex]::Matches($content, "console\.log\(")
    if ($consoleLogMatches.Count -gt 0) {
        Write-Host "   → Replacing $($consoleLogMatches.Count) console.log() calls..." -ForegroundColor Gray
        $content = $content -replace "console\.log\(", "logger.debug("
        $replacements += $consoleLogMatches.Count
    }
    
    # Replace console.error with logger.error
    $consoleErrorMatches = [regex]::Matches($content, "console\.error\(")
    if ($consoleErrorMatches.Count -gt 0) {
        Write-Host "   → Replacing $($consoleErrorMatches.Count) console.error() calls..." -ForegroundColor Gray
        
        # Need to handle console.error specially - it takes (message, error)
        # Convert to logger.error(error, { context: 'message' })
        $content = $content -replace "console\.error\((['\`"][^\'\`"]+['\`"]),\s*(\w+)\)", "logger.error(`$2, { context: `$1 })"
        $content = $content -replace "console\.error\(", "logger.error("
        $replacements += $consoleErrorMatches.Count
    }
    
    # Replace console.warn with logger.warn
    $consoleWarnMatches = [regex]::Matches($content, "console\.warn\(")
    if ($consoleWarnMatches.Count -gt 0) {
        Write-Host "   → Replacing $($consoleWarnMatches.Count) console.warn() calls..." -ForegroundColor Gray
        $content = $content -replace "console\.warn\(", "logger.warn("
        $replacements += $consoleWarnMatches.Count
    }
    
    # Replace console.info with logger.info
    $consoleInfoMatches = [regex]::Matches($content, "console\.info\(")
    if ($consoleInfoMatches.Count -gt 0) {
        Write-Host "   → Replacing $($consoleInfoMatches.Count) console.info() calls..." -ForegroundColor Gray
        $content = $content -replace "console\.info\(", "logger.info("
        $replacements += $consoleInfoMatches.Count
    }
    
    # Only write if changes were made
    if ($content -ne $originalContent) {
        Set-Content -Path $filePath -Value $content -NoNewline
        Write-Host "   ✅ Updated with $replacements changes" -ForegroundColor Green
        $totalReplacements += $replacements
    } else {
        Write-Host "   ℹ️  No changes needed" -ForegroundColor Gray
    }
    
    Write-Host ""
}

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "✅ COMPLETE!" -ForegroundColor Green
Write-Host "Files processed: $filesProcessed/$totalFiles" -ForegroundColor White
Write-Host "Total replacements: $totalReplacements" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run: npm run typecheck" -ForegroundColor Gray
Write-Host "2. Run: npm run build" -ForegroundColor Gray
Write-Host "3. Review changes: git diff" -ForegroundColor Gray
Write-Host ""
