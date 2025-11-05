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
print("[START] Starting FastAPI backend server...")
print("[INFO] Server will be available at: http://localhost:8000")
print("[INFO] API documentation: http://localhost:8000/docs")
print("[INFO] Metrics: http://localhost:8000/metrics")
print("[INFO] Health checks:")
print("   - Basic: http://localhost:8000/health")
print("   - Liveness: http://localhost:8000/api/health/live")
print("   - Readiness: http://localhost:8000/api/health/ready")
print("   - Startup: http://localhost:8000/api/health/startup")
print()

# Set environment variable for the src path
os.environ["PYTHONPATH"] = str(src_dir)

if __name__ == "__main__":
    import uvicorn

    # Change to src directory
    os.chdir(src_dir)

    try:
        # Run uvicorn with the app
        # Uvicorn handles signals gracefully by default, no need for custom handlers
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload - appears to have issues with Python 3.13
            log_level="info",
            access_log=True,
            # Add timeout settings to prevent zombie processes
            timeout_keep_alive=5,
            timeout_graceful_shutdown=30,
        )
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Keyboard interrupt received, shutting down...")
    except Exception as e:
        print(f"\n[ERROR] Server error: {e}")
    finally:
        print("[CLEANUP] Server stopped")
