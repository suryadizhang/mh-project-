#!/usr/bin/env python3
"""
WSGI Entry Point for MyHibachi AI API Backend  
For deployment on Plesk VPS hosting platforms
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the FastAPI application
from simple_backend_corrected import app

# WSGI callable for Plesk deployment
application = app

if __name__ == "__main__":
    import uvicorn
    
    # For local development
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8002)), 
        reload=False
    )