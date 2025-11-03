"""
AI Routers Module

Intelligent routing of conversations to specialized agents.

Available routers:
- IntentRouter: Embedding-based semantic routing to agents
"""

from api.ai.routers.intent_router import (
    AgentType,
    IntentRouter,
    get_intent_router,
)

__all__ = ["AgentType", "IntentRouter", "get_intent_router"]
