@echo off
echo Starting My Hibachi Chef CRM Unified API...
cd /d "C:\Users\surya\projects\MH webapps\apps\backend\src"
"C:\Users\surya\projects\MH webapps\.venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload