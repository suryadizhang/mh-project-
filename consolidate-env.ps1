# Environment Files Consolidation Script
# Simplified version - clean up duplicate and unnecessary .env files

$ErrorActionPreference = "Stop"
$workspaceRoot = "c:\Users\surya\projects\MH webapps"
Set-Location $workspaceRoot

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Environment Files Consolidation" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: List all environment files
Write-Host "Current Environment Files:" -ForegroundColor Yellow
Write-Host ""

$envFiles = Get-ChildItem -Recurse -Filter ".env*" -File | 
    Where-Object { $_.Directory.FullName -notmatch "node_modules|\.next|\.git|dist|build|\.venv|__pycache__|backup" }

$envFiles | ForEach-Object {
    $relativePath = $_.FullName.Replace($workspaceRoot, ".")
    $sizeKB = [math]::Round($_.Length/1KB,2)
    Write-Host "  $relativePath ($sizeKB KB)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Total: $($envFiles.Count) files" -ForegroundColor White
Write-Host ""

# Step 2: Define which files to keep and delete
Write-Host "File Analysis:" -ForegroundColor Cyan
Write-Host ""

$keepFiles = @(
    '.env.docker',
    'apps\backend\.env',
    'apps\backend\.env.example',
    'apps\backend\.env.test',
    'apps\customer\.env.local',
    'apps\customer\.env.example',
    'apps\admin\.env.local',
    'apps\admin\.env.example'
)

$deleteFiles = @(
    '.env',
    '.env.production.template',
    'apps\customer\.env.local.example',
    'apps\customer\.env.production.example',
    'config\environments\.env.development.template',
    'config\environments\.env.production.template'
)

Write-Host "Files to KEEP ($($keepFiles.Count)):" -ForegroundColor Green
$keepFiles | ForEach-Object {
    Write-Host "  - $_" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Files to DELETE ($($deleteFiles.Count)):" -ForegroundColor Red
$deleteFiles | ForEach-Object {
    Write-Host "  - $_" -ForegroundColor Gray
}

Write-Host ""

# Step 3: Confirmation
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Ready to Consolidate?" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  1. DELETE $($deleteFiles.Count) duplicate/unused .env files" -ForegroundColor Red
Write-Host "  2. KEEP $($keepFiles.Count) essential .env files" -ForegroundColor Green
Write-Host "  3. Create backups before deletion" -ForegroundColor Gray
Write-Host ""

$confirm = Read-Host "Do you want to proceed? (yes/no)"

if ($confirm -ne 'yes') {
    Write-Host ""
    Write-Host "Consolidation cancelled." -ForegroundColor Red
    exit 0
}

# Step 4: Create backup directory
Write-Host ""
Write-Host "Creating backup directory..." -ForegroundColor Cyan

$timestamp = Get-Date -Format 'yyyy-MM-dd-HHmmss'
$backupDir = Join-Path $workspaceRoot "env-backup-$timestamp"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

Write-Host "Backup directory: $backupDir" -ForegroundColor Green
Write-Host ""

# Step 5: Backup and delete files
Write-Host "Processing deletions..." -ForegroundColor Cyan
Write-Host ""

$deletedCount = 0
foreach ($fileToDelete in $deleteFiles) {
    $fullPath = Join-Path $workspaceRoot $fileToDelete
    
    if (Test-Path $fullPath) {
        # Backup first
        $backupFileName = $fileToDelete.Replace('\', '_')
        $backupPath = Join-Path $backupDir $backupFileName
        Copy-Item $fullPath $backupPath -Force
        Write-Host "  Backed up: $fileToDelete" -ForegroundColor Gray
        
        # Delete original
        Remove-Item $fullPath -Force
        Write-Host "  Deleted: $fileToDelete" -ForegroundColor Green
        $deletedCount++
    } else {
        Write-Host "  Not found: $fileToDelete" -ForegroundColor Yellow
    }
}

# Step 6: Remove empty config/environments directory
$configEnvDir = Join-Path $workspaceRoot "config\environments"
if (Test-Path $configEnvDir) {
    $remainingFiles = Get-ChildItem $configEnvDir -File
    if ($remainingFiles.Count -eq 0) {
        Remove-Item $configEnvDir -Recurse -Force
        Write-Host ""
        Write-Host "  Removed empty directory: config\environments" -ForegroundColor Green
    }
}

# Step 7: Summary
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Consolidation Complete!" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Deleted: $deletedCount files" -ForegroundColor Green
Write-Host "Kept: $($keepFiles.Count) files" -ForegroundColor Green
Write-Host "Backup: $backupDir" -ForegroundColor Gray
Write-Host ""

# Step 8: Show remaining structure
Write-Host "Final Environment File Structure:" -ForegroundColor Cyan
Write-Host ""

Write-Host "Backend (apps/backend/):" -ForegroundColor Yellow
Write-Host "  .env               - Active development (gitignored)" -ForegroundColor Green
Write-Host "  .env.example       - Template for developers (committed)" -ForegroundColor Green
Write-Host "  .env.test          - Testing environment (gitignored)" -ForegroundColor Green

Write-Host ""
Write-Host "Customer Frontend (apps/customer/):" -ForegroundColor Yellow
Write-Host "  .env.local         - Active development (gitignored)" -ForegroundColor Green
Write-Host "  .env.example       - Template for developers (committed)" -ForegroundColor Green

Write-Host ""
Write-Host "Admin Frontend (apps/admin/):" -ForegroundColor Yellow
Write-Host "  .env.local         - Active development (gitignored)" -ForegroundColor Green
Write-Host "  .env.example       - Template for developers (committed)" -ForegroundColor Green

Write-Host ""
Write-Host "Docker (root):" -ForegroundColor Yellow
Write-Host "  .env.docker        - Docker Compose dev environment (gitignored)" -ForegroundColor Green

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Review backup if needed: $backupDir" -ForegroundColor White
Write-Host "2. Test that all apps still work:" -ForegroundColor White
Write-Host "   - Backend: cd apps\backend ; python -m uvicorn src.main:app --reload" -ForegroundColor Gray
Write-Host "   - Customer: cd apps\customer ; npm run dev" -ForegroundColor Gray
Write-Host "   - Admin: cd apps\admin ; npm run dev" -ForegroundColor Gray
Write-Host "3. Verify with git: git status" -ForegroundColor White
Write-Host "4. Commit the changes" -ForegroundColor White
Write-Host ""
Write-Host "Environment consolidation successful!" -ForegroundColor Green
Write-Host ""
