"""
Backend Server Startup Script
Fixes import paths and starts the FastAPI server
"""

import os
import sys

# Add src directory to Python path
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


# Import and run uvicorn
if __name__ == "__main__":
    from main import app
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, log_level="info")
