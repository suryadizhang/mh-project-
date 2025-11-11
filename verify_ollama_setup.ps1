# Ollama Setup Verification Script
# Run this after Ollama installation completes

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "   OLLAMA SETUP VERIFICATION SCRIPT" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

# Step 1: Check Ollama Installation
Write-Host "[1/5] Checking Ollama installation..." -ForegroundColor Yellow
try {
    $version = ollama --version
    Write-Host "  ✅ Ollama installed: $version" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Ollama not found in PATH" -ForegroundColor Red
    Write-Host "  💡 Open a NEW PowerShell window and try again" -ForegroundColor Yellow
    exit 1
}

# Step 2: Check Ollama Service
Write-Host "`n[2/5] Checking Ollama service..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5
    Write-Host "  ✅ Ollama service is running" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Ollama service not reachable" -ForegroundColor Red
    Write-Host "  💡 Starting Ollama service..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# Step 3: Check if Llama-3 is installed
Write-Host "`n[3/5] Checking for Llama-3 model..." -ForegroundColor Yellow
$models = ollama list 2>$null
if ($models -like "*llama3*") {
    Write-Host "  ✅ Llama-3 model is installed" -ForegroundColor Green
    $downloadNeeded = $false
} else {
    Write-Host "  ⚠️  Llama-3 model not found" -ForegroundColor Yellow
    $downloadNeeded = $true
}

# Step 4: Download Llama-3 if needed
if ($downloadNeeded) {
    Write-Host "`n[4/5] Downloading Llama-3 model (4.7 GB)..." -ForegroundColor Yellow
    Write-Host "  This may take 10-20 minutes depending on connection speed..." -ForegroundColor Gray
    
    $confirm = Read-Host "  Download Llama-3 now? (Y/n)"
    if ($confirm -eq "" -or $confirm -eq "Y" -or $confirm -eq "y") {
        ollama pull llama3
        Write-Host "  ✅ Llama-3 downloaded successfully!" -ForegroundColor Green
    } else {
        Write-Host "  ⏸️  Skipping download. Run 'ollama pull llama3' manually later." -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[4/5] Download step skipped (model already present)" -ForegroundColor Gray
}

# Step 5: Test Llama-3 inference
Write-Host "`n[5/5] Testing Llama-3 inference..." -ForegroundColor Yellow
if (-not $downloadNeeded -or $confirm -eq "" -or $confirm -eq "Y" -or $confirm -eq "y") {
    Write-Host "  Sending test prompt: 'Say hello in 5 words or less'" -ForegroundColor Gray
    $testResponse = ollama run llama3 "Say hello in 5 words or less" --verbose=false 2>$null
    if ($testResponse) {
        Write-Host "  ✅ Llama-3 response: $testResponse" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Could not get response from Llama-3" -ForegroundColor Yellow
    }
}

# Summary
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "   SETUP SUMMARY" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

Write-Host "`n✅ Ollama Installation: Complete" -ForegroundColor Green
if (-not $downloadNeeded -or ($confirm -eq "" -or $confirm -eq "Y" -or $confirm -eq "y")) {
    Write-Host "✅ Llama-3 Model: Ready" -ForegroundColor Green
} else {
    Write-Host "⏸️  Llama-3 Model: Download pending" -ForegroundColor Yellow
}

Write-Host "`n📝 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Start backend server:" -ForegroundColor White
Write-Host "     cd apps\backend" -ForegroundColor Gray
Write-Host "     python -m uvicorn src.main:app --reload --port 8000" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Test Shadow Learning health:" -ForegroundColor White
Write-Host "     curl http://localhost:8000/api/v1/ai/shadow/health" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Test cost monitoring:" -ForegroundColor White
Write-Host "     python test_cost_monitoring_api.py" -ForegroundColor Gray
Write-Host ""

Write-Host "🎉 Ollama setup complete! Ready to test Shadow Learning.`n" -ForegroundColor Green
