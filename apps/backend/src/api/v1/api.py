"""
API Router - Unified endpoint aggregation
Combines operational and AI routes under single API
"""
from fastapi import APIRouter

# Import endpoint routers
from .endpoints import auth, bookings, customers, leads, inbox, rate_limit_metrics
from .endpoints.ai import chat

api_router = APIRouter()

# Operational endpoints (CRM functions)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(inbox.router, prefix="/inbox", tags=["Inbox"])

# AI endpoints (integrated, not separate API)
api_router.include_router(chat.router, prefix="/ai", tags=["AI"])

# Rate limiting monitoring endpoints
api_router.include_router(rate_limit_metrics.router, prefix="/monitoring", tags=["Monitoring"])

# TODO: Add remaining AI endpoints
# api_router.include_router(voice.router, prefix="/ai/voice", tags=["AI Voice"])
# api_router.include_router(embeddings.router, prefix="/ai/embeddings", tags=["AI Embeddings"])

# Placeholder endpoints for now
@api_router.get("/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": "1.0.0",
        "status": "active",
        "endpoints": {
            "operational": [
                "/v1/auth",
                "/v1/bookings", 
                "/v1/customers",
                "/v1/leads",
                "/v1/inbox"
            ],
            "ai": [
                "/v1/ai/chat",
                "/v1/ai/voice", 
                "/v1/ai/embeddings"
            ]
        },
        "architecture": "unified_api",
        "note": "AI endpoints integrated into main API, not separate service"
    }

@api_router.get("/endpoints")
async def list_endpoints():
    """List all available endpoints"""
    return {
        "operational_endpoints": {
            "auth": {
                "login": "POST /v1/auth/login",
                "logout": "POST /v1/auth/logout",
                "refresh": "POST /v1/auth/refresh"
            },
            "bookings": {
                "list": "GET /v1/bookings",
                "create": "POST /v1/bookings",
                "get": "GET /v1/bookings/{id}",
                "update": "PUT /v1/bookings/{id}",
                "delete": "DELETE /v1/bookings/{id}"
            },
            "customers": {
                "list": "GET /v1/customers",
                "create": "POST /v1/customers",
                "get": "GET /v1/customers/{id}",
                "update": "PUT /v1/customers/{id}"
            },
            "leads": {
                "list": "GET /v1/leads",
                "create": "POST /v1/leads",
                "get": "GET /v1/leads/{id}",
                "update": "PUT /v1/leads/{id}",
                "convert": "POST /v1/leads/{id}/convert"
            },
            "inbox": {
                "threads": "GET /v1/inbox/threads",
                "messages": "GET /v1/inbox/threads/{id}/messages",
                "send": "POST /v1/inbox/threads/{id}/send"
            }
        },
        "ai_endpoints": {
            "chat": {
                "send": "POST /v1/ai/chat",
                "history": "GET /v1/ai/chat/history",
                "thread": "GET /v1/ai/chat/threads/{id}"
            },
            "voice": {
                "transcribe": "POST /v1/ai/voice/transcribe",
                "synthesize": "POST /v1/ai/voice/synthesize",
                "realtime": "WebSocket /ws/ai/voice"
            },
            "embeddings": {
                "create": "POST /v1/ai/embeddings",
                "search": "POST /v1/ai/embeddings/search"
            }
        },
        "rate_limits": {
            "public": "20 req/min, 1000 req/hour",
            "admin": "100 req/min, 5000 req/hour", 
            "admin_super": "200 req/min, 10000 req/hour",
            "ai_endpoints": "10 req/min, 300 req/hour (all users)"
        }
    }