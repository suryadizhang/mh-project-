"""
Backend Server Startup Script
Fixes import paths and starts the FastAPI server
"""
import sys
import os

# Add src directory to Python path
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

print(f"✅ Added {src_dir} to Python path")
print(f"🚀 Starting FastAPI backend server...")
print(f"📡 Server will be available at: http://localhost:8000")
print(f"📚 API documentation: http://localhost:8000/docs")
print(f"❤️  Health check: http://localhost:8000/health")
print()

# Import and run uvicorn
if __name__ == "__main__":
    import uvicorn
    from main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
