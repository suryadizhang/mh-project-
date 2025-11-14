"""
Knowledge Sync API Module
=========================
Auto-sync system for dynamic knowledge base (menu, FAQs, terms).

Endpoints:
- GET /status - Check sync status for all sources
- POST /auto - Trigger auto-sync (respects conflicts)
- POST /force - Force override conflicts (superadmin only)
- GET /diff/{source} - Show differences for specific source
- GET /health - Service health check
"""

from .router import router

__all__ = ["router"]
