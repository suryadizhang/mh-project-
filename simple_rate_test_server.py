#!/usr/bin/env python3

"""
Simple Rate Limiting Test Server
Simplified version to test rate limiting without database dependencies
"""

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import os
import sys

# Add the src directory to Python path
backend_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apps', 'backend', 'src')
sys.path.insert(0, backend_src)

from core.rate_limiting import rate_limit_middleware
from core.config import get_settings, UserRole

settings = get_settings()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Rate Limiting Test Server",
    description="Simple server to test admin-optimized rate limiting",
    version="1.0.0",
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def apply_rate_limiting(request: Request, call_next):
    """Apply tiered rate limiting based on user role"""
    # Extract user from JWT token if present
    user = None
    
    try:
        # Try to get user from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # This will be properly implemented with JWT validation
            # For now, we'll detect admin users by checking the token
            token = auth_header.split(" ")[1]
            # Mock admin user detection (replace with real JWT validation)
            if token in ["admin_token", "super_admin_token"]:
                class MockUser:
                    def __init__(self, role, user_id):
                        self.role = role
                        self.id = user_id
                
                if token == "super_admin_token":
                    user = MockUser(UserRole.OWNER, "admin_1")
                else:
                    user = MockUser(UserRole.ADMIN, "admin_2")
    except Exception:
        # If any error in user extraction, treat as public
        user = None
    
    return await rate_limit_middleware(request, call_next, user)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "service": "rate-limiting-test",
        "version": "1.0.0",
        "timestamp": int(time.time())
    }

# Test endpoints for rate limiting
@app.get("/v1/customers", tags=["Test"])
async def test_customers():
    """Test endpoint for customer operations"""
    return {
        "message": "Customers endpoint - test successful",
        "timestamp": int(time.time())
    }

@app.get("/v1/leads", tags=["Test"])
async def test_leads():
    """Test endpoint for lead operations"""
    return {
        "message": "Leads endpoint - test successful",
        "timestamp": int(time.time())
    }

@app.get("/v1/ai/chat", tags=["AI"])
async def test_ai_chat():
    """Test endpoint for AI operations (should have special rate limits)"""
    return {
        "message": "AI Chat endpoint - test successful",
        "timestamp": int(time.time())
    }

@app.get("/", tags=["Info"])
async def root():
    """Root endpoint"""
    return {
        "service": "Rate Limiting Test Server",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "customers": "/v1/customers", 
            "leads": "/v1/leads",
            "ai_chat": "/v1/ai/chat"
        },
        "rate_limiting": {
            "public": "20 req/min",
            "admin": "100 req/min", 
            "super_admin": "200 req/min",
            "ai": "10 req/min"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Rate Limiting Test Server...")
    print(f"⚠️ Redis available: {hasattr(settings, 'REDIS_URL')}")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        reload=False,  # Disable reload for testing
        log_level="info"
    )