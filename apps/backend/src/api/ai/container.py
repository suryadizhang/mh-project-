"""
Dependency Injection Container for AI Module

This is the central hub that manages all AI-related dependencies and prevents
circular imports by controlling instantiation order and providing lazy loading.

Architecture:
- Singleton pattern for shared instances
- Lazy initialization (created on first access)
- Clear dependency graph
- Easy testing (can swap implementations)

Usage:
    from api.ai.container import AIContainer

    # Get instances
    container = AIContainer()
    orchestrator = container.get_orchestrator()
    router = container.get_intent_router()
    agent = container.get_agent("lead_nurturing")

Author: MH Backend Team
Created: 2025-11-03
"""

import logging

logger = logging.getLogger(__name__)


class AIContainer:
    """
    Dependency Injection Container for AI components.

    Manages lifecycle and dependencies of:
    - AIOrchestrator
    - IntentRouter
    - Specialized Agents (Lead Nurturing, Customer Care, Operations, Knowledge)
    - Model Providers (OpenAI, Llama, Hybrid)
    - Memory backends
    - Tool registry

    Implements singleton pattern with lazy initialization.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        """Ensure only one container instance exists"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize container (only once)"""
        if self._initialized:
            return

        # Dependency instances (lazy loaded)
        self._orchestrator = None
        self._intent_router = None
        self._model_provider = None
        self._agents = {}
        self._tools = {}

        self._initialized = True
        logger.info("🏗️ AI Dependency Container initialized")

    def get_orchestrator(self):
        """
        Get or create AIOrchestrator instance.

        Returns:
            AIOrchestrator: The main orchestrator instance
        """
        if self._orchestrator is None:
            # Lazy import to avoid circular dependency
            from .orchestrator.ai_orchestrator import AIOrchestrator

            self._orchestrator = AIOrchestrator(
                router=self.get_intent_router(),
                provider=self.get_model_provider(),
            )
            logger.info("✅ AIOrchestrator created via container")

        return self._orchestrator

    def get_intent_router(self):
        """
        Get or create IntentRouter instance.

        Returns:
            IntentRouter: The intent routing instance
        """
        if self._intent_router is None:
            # Lazy import to avoid circular dependency
            from .routers.intent_router import IntentRouter

            self._intent_router = IntentRouter(provider=self.get_model_provider())
            logger.info("✅ IntentRouter created via container")

        return self._intent_router

    def get_model_provider(self):
        """
        Get or create ModelProvider instance.

        Returns:
            ModelProvider: The model provider instance (OpenAI/Llama/Hybrid)
        """
        if self._model_provider is None:
            # Lazy import to avoid circular dependency
            from .orchestrator.providers import get_provider

            self._model_provider = get_provider()
            logger.info("✅ ModelProvider created via container")

        return self._model_provider

    def get_agent(self, agent_type: str):
        """
        Get or create a specialized agent.

        Args:
            agent_type: Agent identifier (lead_nurturing, customer_care, operations, knowledge)

        Returns:
            BaseAgent: The requested agent instance
        """
        if agent_type not in self._agents:
            # Lazy import to avoid circular dependency
            from .agents import (
                CustomerCareAgent,
                KnowledgeAgent,
                LeadNurturingAgent,
                OperationsAgent,
            )

            agent_map = {
                "lead_nurturing": LeadNurturingAgent,
                "customer_care": CustomerCareAgent,
                "operations": OperationsAgent,
                "knowledge": KnowledgeAgent,
            }

            if agent_type not in agent_map:
                raise ValueError(f"Unknown agent type: {agent_type}")

            # Create agent with provider from container
            agent_class = agent_map[agent_type]
            self._agents[agent_type] = agent_class(provider=self.get_model_provider())
            logger.info(f"✅ {agent_type} Agent created via container")

        return self._agents[agent_type]

    def get_tool(self, tool_name: str):
        """
        Get or create a tool instance.

        Args:
            tool_name: Tool identifier (pricing, travel_fee, protein)

        Returns:
            BaseTool: The requested tool instance
        """
        if tool_name not in self._tools:
            # Lazy import to avoid circular dependency
            from .orchestrator.tools import (
                PricingTool,
                ProteinTool,
                TravelFeeTool,
            )

            tool_map = {
                "pricing": PricingTool,
                "travel_fee": TravelFeeTool,
                "protein": ProteinTool,
            }

            if tool_name not in tool_map:
                raise ValueError(f"Unknown tool: {tool_name}")

            tool_class = tool_map[tool_name]
            self._tools[tool_name] = tool_class()
            logger.info(f"✅ {tool_name} Tool created via container")

        return self._tools[tool_name]

    def reset(self):
        """
        Reset container (useful for testing).

        Clears all cached instances, forcing recreation on next access.
        """
        self._orchestrator = None
        self._intent_router = None
        self._model_provider = None
        self._agents = {}
        self._tools = {}
        logger.info("🔄 AI Container reset")


# Global container instance
_container = None


def get_container() -> AIContainer:
    """
    Get the global AI container instance.

    Returns:
        AIContainer: The singleton container

    Example:
        from api.ai.container import get_container

        container = get_container()
        orchestrator = container.get_orchestrator()
    """
    global _container
    if _container is None:
        _container = AIContainer()
    return _container


# Convenience functions for common operations
def get_orchestrator_from_container():
    """Convenience function to get orchestrator"""
    return get_container().get_orchestrator()


def get_router_from_container():
    """Convenience function to get intent router"""
    return get_container().get_intent_router()


def get_agent_from_container(agent_type: str):
    """Convenience function to get agent"""
    return get_container().get_agent(agent_type)
