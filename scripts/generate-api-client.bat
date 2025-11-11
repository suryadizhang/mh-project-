@echo off
setlocal enabledelayedexpansion

echo 🔄 Generating OpenAPI TypeScript client...

REM Set API URL
if "%API_URL%"=="" set API_URL=http://localhost:8000

echo 📡 Checking API server at %API_URL%...

REM Check if API is running
curl -s "%API_URL%/health" >nul 2>&1
if !errorlevel! neq 0 (
    echo 🚀 Starting API server...
    cd "%~dp0..\apps\api"
    start /b python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

    REM Wait for API to be ready
    for /l %%i in (1,1,30) do (
        echo ⏳ Waiting for API to start (%%i/30)...
        timeout /t 2 /nobreak >nul
        curl -s "%API_URL%/health" >nul 2>&1
        if !errorlevel! equ 0 (
            echo ✅ API server is ready!
            goto :api_ready
        )
    )

    echo ❌ API server failed to start
    exit /b 1
) else (
    echo ✅ API server is already running
)

:api_ready
echo 📥 Fetching OpenAPI schema...
set SCHEMA_FILE=%~dp0..\packages\api-client\openapi.json
mkdir "%~dp0..\packages\api-client" 2>nul

curl -s "%API_URL%/openapi.json" -o "%SCHEMA_FILE%"
if !errorlevel! neq 0 (
    echo ❌ Failed to fetch OpenAPI schema
    exit /b 1
)

echo ✅ OpenAPI schema saved to %SCHEMA_FILE%

echo 🔧 Generating TypeScript types...
cd "%~dp0..\packages\api-client"
npm run generate
if !errorlevel! neq 0 (
    echo ❌ Failed to generate TypeScript types
    exit /b 1
)

echo ✅ TypeScript types generated successfully
echo 🎉 OpenAPI client generation complete!
echo 📋 Generated files:
echo    - %SCHEMA_FILE%
echo    - packages/api-client/src/types/api.ts
