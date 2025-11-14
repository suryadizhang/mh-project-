"""
API Router - Unified endpoint aggregation
Combines operational and AI routes under single API
"""

# ruff: noqa: E501, ERA001 - Long lines for readability, commented TODOs
from fastapi import APIRouter

# Import endpoint routers
from .endpoints import (
    ai_costs,
    ai_readiness,
    analytics_holidays,
    auth,
    bookings,
    campaigns,
    customers,
    inbox,
    leads,
    newsletters,
    rate_limit_metrics,
    shadow_learning,
)
from .endpoints.ai import chat, orchestrator

api_router = APIRouter()

# Public endpoints (no authentication required)
# api_router.include_router(public_leads.router, prefix="/public", tags=["Public"])
# api_router.include_router(public_quote.router, prefix="/public/quote", tags=["Public", "Quotes"])

# Operational endpoints (CRM functions)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(inbox.router, prefix="/inbox", tags=["Inbox"])

# AI endpoints (integrated, not separate API)
api_router.include_router(chat.router, prefix="/ai", tags=["AI"])
api_router.include_router(orchestrator.router, prefix="/ai/orchestrator", tags=["AI Orchestrator"])

# AI Cost Monitoring endpoints
api_router.include_router(ai_costs.router, tags=["AI Cost Monitoring"])

# Shadow Learning endpoints (Phase 1.5)
api_router.include_router(shadow_learning.router, tags=["Shadow Learning"])

# AI Readiness & Monitoring endpoints (Phase 1.5 - Option B+C)
api_router.include_router(ai_readiness.router, tags=["AI Readiness"])

# Rate limiting monitoring endpoints
api_router.include_router(rate_limit_metrics.router, prefix="/monitoring", tags=["Monitoring"])

# AI-Powered Marketing endpoints (NEW)
api_router.include_router(newsletters.router, prefix="/marketing", tags=["AI Marketing", "Newsletters"])
api_router.include_router(campaigns.router, prefix="/marketing", tags=["AI Marketing", "Campaigns"])
api_router.include_router(analytics_holidays.router, prefix="/marketing", tags=["AI Marketing", "Analytics"])

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
            "operational": ["/v1/auth", "/v1/bookings", "/v1/customers", "/v1/leads", "/v1/inbox"],
            "ai": ["/v1/ai/chat", "/v1/ai/orchestrator", "/v1/ai/voice", "/v1/ai/embeddings"],
        },
        "architecture": "unified_api",
        "note": "AI endpoints integrated into main API, not separate service",
    }


@api_router.get("/endpoints")
async def list_endpoints():
    """List all available endpoints"""
    return {
        "operational_endpoints": {
            "auth": {
                "login": "POST /v1/auth/login",
                "logout": "POST /v1/auth/logout",
                "refresh": "POST /v1/auth/refresh",
            },
            "bookings": {
                "list": "GET /v1/bookings",
                "create": "POST /v1/bookings",
                "get": "GET /v1/bookings/{id}",
                "update": "PUT /v1/bookings/{id}",
                "delete": "DELETE /v1/bookings/{id}",
            },
            "customers": {
                "list": "GET /v1/customers",
                "create": "POST /v1/customers",
                "get": "GET /v1/customers/{id}",
                "update": "PUT /v1/customers/{id}",
            },
            "leads": {
                "list": "GET /v1/leads",
                "create": "POST /v1/leads",
                "get": "GET /v1/leads/{id}",
                "update": "PUT /v1/leads/{id}",
                "convert": "POST /v1/leads/{id}/convert",
            },
            "inbox": {
                "threads": "GET /v1/inbox/threads",
                "messages": "GET /v1/inbox/threads/{id}/messages",
                "send": "POST /v1/inbox/threads/{id}/send",
            },
        },
        "ai_endpoints": {
            "chat": {
                "send": "POST /v1/ai/chat",
                "history": "GET /v1/ai/chat/history",
                "thread": "GET /v1/ai/chat/threads/{id}",
            },
            "orchestrator": {
                "process": "POST /v1/ai/orchestrator/process",
                "batch_process": "POST /v1/ai/orchestrator/batch-process",
                "config": "GET /v1/ai/orchestrator/config",
                "health": "GET /v1/ai/orchestrator/health",
                "tools": "GET /v1/ai/orchestrator/tools",
            },
            "voice": {
                "transcribe": "POST /v1/ai/voice/transcribe",
                "synthesize": "POST /v1/ai/voice/synthesize",
                "realtime": "WebSocket /ws/ai/voice",
            },
            "embeddings": {
                "create": "POST /v1/ai/embeddings",
                "search": "POST /v1/ai/embeddings/search",
            },
            "marketing": {
                "newsletters": {
                    "generate": "GET /v1/marketing/newsletters/generate?days_ahead=60",
                    "generate_content": "POST /v1/marketing/newsletters/generate-content",
                    "send": "POST /v1/marketing/newsletters/send",
                    "preview": "GET /v1/marketing/newsletters/preview/{holiday_key}",
                },
                "campaigns": {
                    "annual": "GET /v1/marketing/campaigns/annual?days_ahead=365",
                    "generate_content": "POST /v1/marketing/campaigns/generate-content",
                    "launch": "POST /v1/marketing/campaigns/launch",
                    "budget_recommendations": "GET /v1/marketing/campaigns/budget-recommendations",
                },
                "analytics": {
                    "trends": "GET /v1/marketing/analytics/holidays/trends?year=2025",
                    "summary": "GET /v1/marketing/analytics/holidays/summary?year=2025",
                    "peaks": "GET /v1/marketing/analytics/holidays/peaks?year=2025",
                    "forecast": "GET /v1/marketing/analytics/holidays/forecast/{holiday_key}",
                    "comparison": "GET /v1/marketing/analytics/holidays/comparison",
                },
            },
        },
        "rate_limits": {
            "public": "20 req/min, 1000 req/hour",
            "admin": "100 req/min, 5000 req/hour",
            "admin_super": "200 req/min, 10000 req/hour",
            "ai_endpoints": "10 req/min, 300 req/hour (all users)",
        },
    }
