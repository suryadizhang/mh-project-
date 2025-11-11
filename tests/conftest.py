"""
Test configuration for the MH webapps project.
Sets up Python path and common test fixtures.
"""
import sys
import os
from pathlib import Path

# Add the API app directory to Python path so imports work correctly
api_path = Path(__file__).parent.parent / "apps" / "api"
sys.path.insert(0, str(api_path))

# Also add the root project directory
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

# Set environment variables for testing
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("DATABASE_URL_SYNC", "sqlite:///./test.db") 
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-testing-only")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "test-encryption-key-for-testing-only-not-production")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:3000","http://localhost:5173"]')
os.environ.setdefault("LOG_LEVEL", "warning")
os.environ.setdefault("DEBUG", "false")

# Integration settings using actual Settings class fields (prevent validation errors)
os.environ.setdefault("ENABLE_METRICS", "false")  # Use enable_metrics instead
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-for-testing-only")
os.environ.setdefault("RINGCENTRAL_CLIENT_ID", "test-client-id")
os.environ.setdefault("RINGCENTRAL_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("RINGCENTRAL_JWT_TOKEN", "test-jwt-token")
os.environ.setdefault("RINGCENTRAL_WEBHOOK_SECRET", "test-webhook-secret")
os.environ.setdefault("DEFAULT_ADMIN_EMAIL", "test@example.com")
os.environ.setdefault("DEFAULT_ADMIN_PASSWORD", "testpass123")