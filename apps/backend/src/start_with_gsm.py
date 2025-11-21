"""
Backend startup script with GSM integration
Loads secrets before starting the FastAPI server
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from core.config import get_settings_async, get_config_status

logger = logging.getLogger(__name__)


async def startup_with_gsm():
    """Load configuration from GSM and start the application"""

    print("🚀 My Hibachi Backend Starting...")
    print("=" * 50)

    # Load configuration from GSM
    print("🔑 Loading configuration...")
    try:
        settings = await get_settings_async()
        config_status = get_config_status()

        print("✅ Configuration loaded successfully")
        print(f"   - GSM Available: {config_status['gsm_available']}")
        print(f"   - Config Loaded: {config_status['config_loaded']}")
        print(f"   - Secrets Count: {config_status['secrets_count']}")

        # Validate critical configuration
        critical_checks = [
            ("JWT_SECRET", settings.JWT_SECRET),
            ("SECRET_KEY", settings.SECRET_KEY),
            ("ENCRYPTION_KEY", settings.ENCRYPTION_KEY),
            ("DATABASE_URL", settings.DATABASE_URL),
        ]

        missing = []
        for name, value in critical_checks:
            if not value:
                missing.append(name)
            else:
                print(f"   ✅ {name}: {'*' * min(8, len(str(value)))}")

        if missing:
            print(f"❌ Critical configuration missing: {missing}")
            return False

        print("✅ All critical configuration validated")
        return True

    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        logger.exception("Configuration loading failed")
        return False


def main():
    """Main startup function"""
    # Run the startup sequence
    success = asyncio.run(startup_with_gsm())

    if not success:
        print("❌ Startup failed, exiting...")
        sys.exit(1)

    print("✅ Startup complete, configuration ready")
    print("=" * 50)

    # Now start the FastAPI application
    print("🌐 Starting FastAPI server...")

    # Import and run the FastAPI app
    try:
        import uvicorn
        from main import app  # Import the FastAPI app

        # Get settings for server configuration
        from core.config import get_settings

        settings = get_settings()

        # Start the server
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level=settings.LOG_LEVEL.lower(),
        )

    except ImportError as e:
        print(f"❌ Failed to import FastAPI dependencies: {e}")
        print("💡 Make sure uvicorn and fastapi are installed:")
        print("   pip install fastapi uvicorn")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Failed to start FastAPI server: {e}")
        logger.exception("FastAPI startup failed")
        sys.exit(1)


if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    main()
