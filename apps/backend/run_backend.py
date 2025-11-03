"""
Backend Server Runner - Fixes Python Path and Starts Server
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
backend_dir = Path(__file__).parent
src_dir = backend_dir / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

print(f"[OK] Added {src_dir} to Python path")
print(f"[START] Starting FastAPI backend server...")
print(f"[INFO] Server will be available at: http://localhost:8000")
print(f"[INFO] API documentation: http://localhost:8000/docs")
print(f"[INFO] Metrics: http://localhost:8000/metrics")
print(f"[INFO] Health checks:")
print(f"   - Basic: http://localhost:8000/health")
print(f"   - Liveness: http://localhost:8000/api/health/live")
print(f"   - Readiness: http://localhost:8000/api/health/ready")
print(f"   - Startup: http://localhost:8000/api/health/startup")
print()

# Set environment variable for the src path
os.environ['PYTHONPATH'] = str(src_dir)

if __name__ == "__main__":
    import uvicorn
    
    # Change to src directory
    os.chdir(src_dir)
    
    # Run uvicorn with the app
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
