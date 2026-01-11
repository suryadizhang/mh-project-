"""
V1 WebSocket Endpoints Module
=============================

Provides WebSocket API endpoints for real-time functionality.

Endpoints:
    - /api/v1/ws/escalations: Real-time escalation notifications
    - /api/v1/ws/compliance: Real-time compliance monitoring
"""

from .escalations import router as escalations_router
from .compliance import router as compliance_router

__all__ = [
    "escalations_router",
    "compliance_router",
]
