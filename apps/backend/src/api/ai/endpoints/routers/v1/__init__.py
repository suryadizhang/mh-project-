"""
V1 API Router Package
Agent-aware unified API endpoints with proper scoping and tool permissions.
"""

from .unified_chat import router as unified_chat_router

__all__ = ["unified_chat_router"]