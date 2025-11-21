"""
Base Tool Interface for AI Orchestrator

This module provides the abstract base class for all tools that can be called
by the AI orchestrator. Each tool represents a specific capability that the AI
can invoke to perform actions or retrieve information.

Architecture:
- Abstract interface for consistent tool implementation
- Type-safe parameter validation
- Structured response format
- Error handling and logging
- ChatGPT-ready design for Phase 3 expansion

Author: MyHibachi Development Team
Created: October 31, 2025
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ToolParameter(BaseModel):
    """
    Tool parameter definition for OpenAI function calling schema.

    Attributes:
        name: Parameter name
        type: JSON schema type (string, integer, number, boolean, object, array)
        description: Human-readable description for the AI
        required: Whether this parameter is required
        enum: Optional list of allowed values
        properties: For object types, nested parameter definitions
        items: For array types, specification of array element type (REQUIRED by OpenAI)
    """

    name: str
    type: str
    description: str
    required: bool = False
    enum: list[str] | None = None
    properties: dict[str, Any] | None = None
    items: dict[str, Any] | None = None  # Required for array types!


class ToolResult(BaseModel):
    """
    Standardized tool execution result.

    Attributes:
        success: Whether the tool executed successfully
        data: Result data (varies by tool)
        error: Error message if execution failed
        metadata: Additional context (execution time, tool name, etc.)
    """

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"quote_total": 735.00, "travel_fee": 0.00},
                "error": None,
                "metadata": {
                    "execution_time_ms": 45,
                    "tool_name": "calculate_party_quote",
                },
            }
        }


class BaseTool(ABC):
    """
    Abstract base class for all AI orchestrator tools.

    Each tool must implement:
    1. name: Unique tool identifier
    2. description: What the tool does (for AI context)
    3. parameters: List of ToolParameter objects
    4. execute(): The actual tool logic

    Tools are automatically registered with the orchestrator and made available
    to the AI via OpenAI function calling.

    Example:
        ```python
        class PricingTool(BaseTool):
            @property
            def name(self) -> str:
                return "calculate_party_quote"

            @property
            def description(self) -> str:
                return "Calculate accurate hibachi party quote with travel fees"

            @property
            def parameters(self) -> List[ToolParameter]:
                return [
                    ToolParameter(
                        name="adults",
                        type="integer",
                        description="Number of adult guests",
                        required=True
                    )
                ]

            async def execute(self, **kwargs) -> ToolResult:
                # Tool logic here
                return ToolResult(success=True, data={"total": 735.00})
        ```
    """

    def __init__(self):
        """Initialize the tool with logging."""
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )
        self.logger.info(f"Initialized tool: {self.name}")

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique tool name (used by OpenAI function calling).

        Must match OpenAI function naming rules:
        - Only a-z, A-Z, 0-9, underscores and dashes
        - Max 64 characters
        - Descriptive and action-oriented (e.g., "calculate_party_quote")

        Returns:
            str: Tool name
        """

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description of what the tool does.

        This is shown to the AI model to help it decide when to use the tool.
        Should be clear, concise, and include key use cases.

        Returns:
            str: Tool description
        """

    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]:
        """
        List of parameters this tool accepts.

        Used to generate OpenAI function calling schema automatically.
        Include detailed descriptions to help the AI extract correct values.

        Returns:
            List[ToolParameter]: Parameter definitions
        """

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.

        This is the actual tool logic. Should:
        1. Validate input parameters
        2. Perform the tool's action
        3. Return structured ToolResult
        4. Handle errors gracefully
        5. Log execution details

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult: Execution result with success status and data

        Raises:
            ValueError: If parameters are invalid
            Exception: Other execution errors (caught and returned in ToolResult)
        """

    def to_openai_function(self) -> dict[str, Any]:
        """
        Convert tool definition to OpenAI function calling schema.

        Automatically generates the JSON schema that OpenAI expects for
        function calling. This allows the AI to understand what tools are
        available and how to call them.

        Returns:
            Dict[str, Any]: OpenAI function schema

        Example Output:
            ```json
            {
                "type": "function",
                "function": {
                    "name": "calculate_party_quote",
                    "description": "Calculate accurate hibachi party quote",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "adults": {
                                "type": "integer",
                                "description": "Number of adult guests"
                            }
                        },
                        "required": ["adults"]
                    }
                }
            }
            ```
        """
        properties = {}
        required = []

        for param in self.parameters:
            param_schema = {
                "type": param.type,
                "description": param.description,
            }

            if param.enum:
                param_schema["enum"] = param.enum

            if param.properties:
                param_schema["properties"] = param.properties

            # CRITICAL: OpenAI requires 'items' for array types
            if param.items:
                param_schema["items"] = param.items

            properties[param.name] = param_schema

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def validate_parameters(self, **kwargs) -> None:
        """
        Validate that all required parameters are present and correct type.

        Args:
            **kwargs: Parameters to validate

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                raise ValueError(f"Missing required parameter: {param.name}")

            if param.name in kwargs and kwargs[param.name] is not None:
                value = kwargs[param.name]

                # Type validation
                if param.type == "integer" and not isinstance(value, int):
                    raise ValueError(
                        f"Parameter {param.name} must be an integer"
                    )
                elif param.type == "string" and not isinstance(value, str):
                    raise ValueError(
                        f"Parameter {param.name} must be a string"
                    )
                elif param.type == "number" and not isinstance(
                    value, int | float
                ):
                    raise ValueError(
                        f"Parameter {param.name} must be a number"
                    )
                elif param.type == "boolean" and not isinstance(value, bool):
                    raise ValueError(
                        f"Parameter {param.name} must be a boolean"
                    )

                # Enum validation
                if param.enum and value not in param.enum:
                    raise ValueError(
                        f"Parameter {param.name} must be one of: {', '.join(param.enum)}"
                    )

    async def execute_with_logging(self, **kwargs) -> ToolResult:
        """
        Execute tool with automatic logging and error handling.

        Wraps the execute() method with:
        - Parameter validation
        - Execution timing
        - Error catching
        - Structured logging

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult: Execution result
        """
        start_time = datetime.now(UTC)

        try:
            # Validate parameters
            self.validate_parameters(**kwargs)

            # Log execution start
            self.logger.info(
                f"Executing tool: {self.name}", extra={"parameters": kwargs}
            )

            # Execute tool
            result = await self.execute(**kwargs)

            # Add metadata
            execution_time_ms = (
                datetime.now(UTC) - start_time
            ).total_seconds() * 1000
            result.metadata.update(
                {
                    "tool_name": self.name,
                    "execution_time_ms": round(execution_time_ms, 2),
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            # Log success
            self.logger.info(
                f"Tool execution successful: {self.name}",
                extra={
                    "execution_time_ms": execution_time_ms,
                    "success": result.success,
                },
            )

            return result

        except Exception as e:
            # Log error
            execution_time_ms = (
                datetime.now(UTC) - start_time
            ).total_seconds() * 1000
            self.logger.error(
                f"Tool execution failed: {self.name}",
                extra={
                    "error": str(e),
                    "parameters": kwargs,
                    "execution_time_ms": execution_time_ms,
                },
                exc_info=True,
            )

            # Return error result
            return ToolResult(
                success=False,
                error=str(e),
                metadata={
                    "tool_name": self.name,
                    "execution_time_ms": round(execution_time_ms, 2),
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )


class ToolRegistry:
    """
    Registry for managing available tools.

    Maintains a central registry of all tools available to the orchestrator.
    Provides methods to register, retrieve, and list tools.

    This is used by the orchestrator to:
    1. Generate OpenAI function schemas
    2. Route function calls to appropriate tools
    3. Validate tool availability
    """

    def __init__(self):
        """Initialize empty tool registry."""
        self._tools: dict[str, BaseTool] = {}
        self.logger = logging.getLogger(__name__)

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool with the registry.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If tool name already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")

        self._tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")

    def get(self, name: str) -> BaseTool | None:
        """
        Get tool by name.

        Args:
            name: Tool name

        Returns:
            BaseTool: Tool instance or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """
        List all registered tool names.

        Returns:
            List[str]: Tool names
        """
        return list(self._tools.keys())

    def to_openai_functions(self) -> list[dict[str, Any]]:
        """
        Convert all registered tools to OpenAI function schemas.

        Returns:
            List[Dict[str, Any]]: OpenAI function schemas
        """
        return [tool.to_openai_function() for tool in self._tools.values()]
