@echo off
REM MyHibachi Backend Startup Script for Windows

echo 🍤 Starting MyHibachi Backend API...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Set environment variables
if exist ".env" (
    echo Loading environment variables from .env...
    for /f "delims=" %%i in (.env) do set %%i
) else (
    echo Warning: .env file not found. Using default settings.
)

REM Start the FastAPI server
echo 🚀 Starting FastAPI server on http://localhost:8000
echo 📖 API Documentation: http://localhost:8000/docs
echo 📚 Alternative docs: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server

uvicorn main:app --reload --host 0.0.0.0 --port 8000
