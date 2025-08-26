#!/usr/bin/env python3
"""
MyHibachi AI Backend - Main Entry Point
Unified AI-powered customer service and FAQ system
"""

import sys
import uvicorn
from pathlib import Path


def main():
    """Main entry point for the AI backend"""
    print("🤖 MyHibachi AI Backend Starting...")
    
    # Check if we should use the corrected version
    corrected_backend = Path(__file__).parent / "simple_backend_corrected.py"
    
    if corrected_backend.exists():
        print("✅ Using corrected backend implementation")
        # Run the corrected backend
        try:
            uvicorn.run(
                "simple_backend_corrected:app",
                host="127.0.0.1",
                port=8001,
                reload=True,
                log_level="info"
            )
        except ImportError as e:
            print(f"❌ Error importing corrected backend: {e}")
            sys.exit(1)
    else:
        print("❌ Corrected backend not found")
        sys.exit(1)


if __name__ == "__main__":
    main()