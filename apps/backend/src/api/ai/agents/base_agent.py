"""
Base Agent - Abstract class for all AI agents

Defines the standard interface and shared functionality for specialized agents.
All agents (Lead Nurturing, Customer Care, Operations, Knowledge) extend this.

Author: MH Backend Team
Created: 2025-10-31 (Phase 1A)
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timezone
import logging
from typing import Any

from ..orchestrator.providers import ModelProvider, get_provider

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for AI agents.

    All specialized agents must implement:
    - get_system_prompt() - Domain-specific instructions
    - get_tools() - Available function calls
    - process_tool_call() - Execute tool functions

    Shared functionality:
    - Provider integration (OpenAI/Llama/Hybrid)
    - Conversation history management
    - Tool calling orchestration
    - Error handling & logging

    Usage:
        class MyAgent(BaseAgent):
            def get_system_prompt(self): return "You are..."
            def get_tools(self): return [...]
            async def process_tool_call(self, name, args): ...

        agent = MyAgent()
        response = await agent.process(message, context)
    """

    def __init__(
        self,
        agent_type: str,
        provider: ModelProvider | None = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ):
        """
        Initialize agent.

        Args:
            agent_type: Agent identifier (lead_nurturing, customer_care, etc.)
            provider: Model provider (None = lazy load from container)
            temperature: Response randomness (0.0-1.0)
            max_tokens: Max response length
        """
        self.agent_type = agent_type
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Phase 2: Dependency Injection support (backward compatible)
        self.provider = provider

        if self.provider is None:
            # Backward compatibility: lazy load from container
            try:
                from ..container import get_container

                self.provider = get_container().get_model_provider()
            except ImportError:
                # Fallback to old way if container not available
                self.provider = get_provider()

        # Tool registry (name -> function)
        self._tool_functions: dict[str, Callable] = {}
        self._register_tools()

        logger.info(
            f"{agent_type} agent initialized with {self.provider.provider_type.value} provider"
        )

    # ===== Abstract Methods (Must Implement) =====

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Return domain-specific system prompt.

        This defines the agent's personality, expertise, and behavior.
        Should include:
        - Role definition
        - Communication style
        - Key objectives
        - Constraints/guidelines

        Returns:
            System prompt string
        """

    @abstractmethod
    def get_tools(self) -> list[dict[str, Any]]:
        """
        Return available function calling tools.

        Format (OpenAI function calling spec):
        [
            {
                "type": "function",
                "function": {
                    "name": "tool_name",
                    "description": "What this tool does",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "param1": {"type": "string", "description": "..."}
                        },
                        "required": ["param1"]
                    }
                }
            }
        ]

        Returns:
            List of tool definitions
        """

    @abstractmethod
    async def process_tool_call(
        self, tool_name: str, arguments: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute a tool function call.

        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments (parsed from JSON)
            context: Request context (conversation_id, customer_id, etc.)

        Returns:
            {
                "success": bool,
                "result": Any,  # Tool output
                "error": Optional[str]
            }
        """

    # ===== Core Processing =====

    async def process(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        enable_tools: bool = True,
    ) -> dict[str, Any]:
        """
        Process a user message and generate response.

        Args:
            message: User message
            context: Request context (conversation_id, customer_id, channel, etc.)
            conversation_history: Previous messages [{"role": "user|assistant", "content": "..."}]
            enable_tools: Enable function calling

        Returns:
            {
                "content": str,              # Response text
                "tool_calls": List[Dict],    # Tool calls made (if any)
                "tool_results": List[Dict],  # Tool execution results
                "finish_reason": str,        # "stop", "tool_calls", "length"
                "usage": Dict,               # Token usage
                "metadata": Dict             # Additional metadata
            }
        """
        context = context or {}
        conversation_history = conversation_history or []

        start_time = datetime.now(timezone.utc)

        try:
            # Build messages
            messages = self._build_messages(message, conversation_history)

            # Get tools (if enabled)
            tools = self.get_tools() if enable_tools else None

            # Call provider
            response = await self.provider.complete(
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                tools=tools,
                tool_choice="auto" if tools else None,
                metadata={
                    "agent_type": self.agent_type,
                    "conversation_id": context.get("conversation_id"),
                    "channel": context.get("channel"),
                    **context,
                },
            )

            # Handle tool calls
            tool_results = []
            if response.get("tool_calls"):
                tool_results = await self._execute_tool_calls(response["tool_calls"], context)

                # If tools were called, get final response
                if tool_results:
                    response = await self._get_final_response(
                        messages, response, tool_results, context
                    )

            # Build result
            result = {
                "content": response["content"],
                "tool_calls": response.get("tool_calls", []),
                "tool_results": tool_results,
                "finish_reason": response["finish_reason"],
                "usage": response["usage"],
                "metadata": {
                    "agent_type": self.agent_type,
                    "provider": self.provider.provider_type.value,
                    "model": response["model"],
                    "latency_ms": response.get("latency_ms", 0),
                    "processing_time_ms": int(
                        (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                    ),
                },
            }

            logger.info(
                f"{self.agent_type} processed message: "
                f"{len(tool_results)} tools, "
                f"{response['usage']['total_tokens']} tokens, "
                f"{result['metadata']['processing_time_ms']}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Error in {self.agent_type} agent: {e}", exc_info=True)
            raise

    # ===== Helper Methods =====

    def _build_messages(
        self, message: str, conversation_history: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """Build message list with system prompt + history + current message"""

        messages = [{"role": "system", "content": self.get_system_prompt()}]

        # Add conversation history
        messages.extend(conversation_history)

        # Add current message
        messages.append({"role": "user", "content": message})

        return messages

    async def _execute_tool_calls(
        self, tool_calls: list[dict[str, Any]], context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Execute all tool calls and collect results"""

        results = []

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]

            try:
                # Parse arguments
                import json

                arguments = json.loads(tool_call["function"]["arguments"])

                # Execute tool
                result = await self.process_tool_call(tool_name, arguments, context)

                results.append(
                    {
                        "tool_call_id": tool_call["id"],
                        "tool_name": tool_name,
                        "success": result["success"],
                        "result": result["result"],
                        "error": result.get("error"),
                    }
                )

                logger.info(
                    f"Tool executed: {tool_name} - {'success' if result['success'] else 'failed'}"
                )

            except Exception as e:
                logger.error(f"Tool execution failed: {tool_name} - {e}", exc_info=True)
                results.append(
                    {
                        "tool_call_id": tool_call["id"],
                        "tool_name": tool_name,
                        "success": False,
                        "result": None,
                        "error": str(e),
                    }
                )

        return results

    async def _get_final_response(
        self,
        original_messages: list[dict[str, str]],
        tool_response: dict[str, Any],
        tool_results: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Get final response after tool execution"""

        # Build messages with tool results
        messages = original_messages.copy()

        # Add assistant's tool calls
        messages.append(
            {
                "role": "assistant",
                "content": tool_response.get("content") or "",
                "tool_calls": tool_response["tool_calls"],
            }
        )

        # Add tool results
        for result in tool_results:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": result["tool_call_id"],
                    "name": result["tool_name"],
                    "content": (
                        str(result["result"]) if result["success"] else f"Error: {result['error']}"
                    ),
                }
            )

        # Get final response
        response = await self.provider.complete(
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            metadata={
                "agent_type": self.agent_type,
                "conversation_id": context.get("conversation_id"),
                "channel": context.get("channel"),
                "tool_followup": True,
            },
        )

        return response

    def _register_tools(self):
        """Register tool functions (override in subclasses if needed)"""

    def register_tool(self, name: str, function: Callable):
        """Register a tool function"""
        self._tool_functions[name] = function
        logger.debug(f"Registered tool: {name}")

    def get_metadata(self) -> dict[str, Any]:
        """Get agent metadata"""
        return {
            "agent_type": self.agent_type,
            "provider": self.provider.provider_type.value,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tools_available": len(self.get_tools()),
        }
