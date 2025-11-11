#!/usr/bin/env python3
"""
WSGI Entry Point for MyHibachi Unified Backend API
For deployment on Plesk VPS hosting platforms

This is the unified backend that combines:
- Core API endpoints (/v1/*)
- AI endpoints (/v1/ai/*)
- Webhook handlers (/webhooks/*)
- WebSocket connections (/ws/*)
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path for proper imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(src_dir))

# Import the unified FastAPI application
from src.main import app

# WSGI callable for Plesk deployment
application = app

if __name__ == "__main__":
    import uvicorn
    
    # For local development
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False
    )