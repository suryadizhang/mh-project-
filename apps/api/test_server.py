#!/usr/bin/env python3
"""
Simplified API server for testing without database dependencies
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json

# Create a minimal FastAPI app for testing
app = FastAPI(
    title="MyHibachi API - Testing Mode",
    description="Simplified API for testing Swagger documentation",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MyHibachi API - Testing Mode",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "MyHibachi API",
        "version": "2.0.0",
        "mode": "testing"
    }

@app.get("/api/health")
async def api_health():
    """API health check"""
    return {
        "status": "healthy",
        "database": "testing mode",
        "api": "operational"
    }

# Mock API endpoints for testing
@app.get("/api/bookings", tags=["Bookings"])
async def get_bookings():
    """Get all bookings (mock endpoint)"""
    return {
        "bookings": [],
        "total": 0,
        "message": "Mock endpoint - no database connection"
    }

@app.post("/api/bookings", tags=["Bookings"])
async def create_booking():
    """Create a new booking (mock endpoint)"""
    return {
        "id": "mock-123",
        "status": "pending",
        "message": "Mock booking created - testing mode"
    }

@app.get("/api/auth/me", tags=["Authentication"])
async def get_current_user():
    """Get current user (mock endpoint)"""
    return {
        "id": "mock-user",
        "email": "test@example.com",
        "role": "customer",
        "message": "Mock user - testing mode"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)