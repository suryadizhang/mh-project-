"""
Minimal MyHibachi Backend for Testing and Verification
Simple FastAPI server with health monitoring for system verification
"""

import time
from datetime import datetime
from typing import Any

import psutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI(title="MyHibachi Test Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track startup time
startup_time = time.time()

# Simple request counter for monitoring
request_count = 0
response_times = []


class ChatRequest(BaseModel):
    message: str
    page: str = "/"
    consent_to_save: bool = False


class ChatResponse(BaseModel):
    answer: str
    confidence: float = 0.8
    conversation_id: str = "test-conversation"


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Comprehensive health check endpoint"""
    global request_count, response_times

    uptime_seconds = time.time() - startup_time

    # Get system metrics
    try:
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        disk_percent = (disk.used / disk.total) * 100
    except Exception:
        cpu_percent = memory.percent = disk_percent = 0.0

    # Calculate average response time
    avg_response_time = (
        sum(response_times) / len(response_times) if response_times else 0.0
    )

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "MyHibachi Test Backend",
        "version": "1.0.0",
        "uptime_seconds": uptime_seconds,
        "uptime_human": f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m {int(uptime_seconds % 60)}s",
        "database": "connected",  # Simulated for testing
        "ai_service": "available",  # Simulated for testing
        "metrics": {
            "requests_total": request_count,
            "avg_response_time": avg_response_time,
            "error_rate": 0.0,  # Simulated low error rate
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk_percent,
            },
        },
        "issues": [],
        "endpoints": {
            "health": "/health",
            "chat": "/api/v1/chat",
            "status": "/status",
            "metrics": "/metrics/summary",
        },
    }


@app.get("/status")
async def system_status():
    """Get detailed system status"""
    return {
        "service": "MyHibachi Test Backend",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "health": await health_check(),
    }


@app.get("/metrics/summary")
async def metrics_summary():
    """Get performance metrics summary"""
    global request_count, response_times

    uptime_seconds = time.time() - startup_time

    return {
        "request_count": request_count,
        "avg_response_time": (
            sum(response_times) / len(response_times)
            if response_times
            else 0.0
        ),
        "error_rate": 0.0,
        "uptime_seconds": uptime_seconds,
        "system_cpu": psutil.cpu_percent() if psutil else 0.0,
        "system_memory": psutil.virtual_memory().percent if psutil else 0.0,
        "last_updated": datetime.utcnow().isoformat(),
    }


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Simple chat endpoint for testing"""
    global request_count, response_times

    start_time = time.time()
    request_count += 1

    # Simulate processing time
    import asyncio

    await asyncio.sleep(0.1)  # 100ms simulated processing

    # Simple response based on message content
    message = request.message.lower()

    if "menu" in message or "price" in message:
        answer = "Our hibachi experience includes premium meats, vegetables, fried rice, and our signature sauces. Pricing starts at $25 per person with a minimum of 8 people. Would you like a detailed quote?"
        confidence = 0.9
    elif "booking" in message or "book" in message:
        answer = "To book your hibachi experience, please call us at (916) 740-8768 or visit our booking page. We require 48 hours notice and a deposit to secure your event."
        confidence = 0.9
    elif "location" in message or "travel" in message:
        answer = "We serve the greater Sacramento area and surrounding cities within 25 miles. Our chef will bring everything needed for your event including the grill and all ingredients."
        confidence = 0.8
    elif "hello" in message or "hi" in message:
        answer = "Hello! Welcome to MyHibachi! I'm here to help you with questions about our mobile hibachi catering service. What would you like to know?"
        confidence = 0.9
    else:
        answer = "Thank you for your question! For detailed information about our mobile hibachi catering service, please call us at (916) 740-8768 or check our FAQ page. How can I help you today?"
        confidence = 0.6

    # Record response time
    response_time = time.time() - start_time
    response_times.append(response_time)

    # Keep only last 100 response times
    if len(response_times) > 100:
        response_times = response_times[-100:]

    return ChatResponse(
        answer=answer,
        confidence=confidence,
        conversation_id=f"test-{request_count}",
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MyHibachi Test Backend",
        "status": "running",
        "endpoints": [
            "/health",
            "/status",
            "/api/v1/chat",
            "/metrics/summary",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting MyHibachi Test Backend...")
    print("📋 Available endpoints:")
    print("   • http://localhost:8002/health")
    print("   • http://localhost:8002/status")
    print("   • http://localhost:8002/api/v1/chat")
    print("   • http://localhost:8002/metrics/summary")

    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")
