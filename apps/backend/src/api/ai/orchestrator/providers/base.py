"""
Base Model Provider Protocol

Defines the abstract interface that all AI model providers must implement.
This enables swapping between OpenAI, Llama 3, or hybrid routing with zero code changes.

Author: MH Backend Team
Created: 2025-10-31 (Phase 1A)
"""

from collections.abc import AsyncIterator
from enum import Enum
from typing import Any, Protocol


class ModelType(str, Enum):
    """Supported model types"""

    OPENAI = "openai"
    LLAMA = "llama"
    HYBRID = "hybrid"  # Teacher-student routing (Option 2)


class ModelCapability(str, Enum):
    """Model capabilities for capability-based routing"""

    CHAT = "chat"
    EMBEDDING = "embedding"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    VISION = "vision"
    JSON_MODE = "json_mode"


class ModelProvider(Protocol):
    """
    Abstract protocol for AI model providers.

    All providers (OpenAI, Llama, Hybrid) must implement these methods.
    This enables zero-rebuild upgrades when adding new models.

    Usage:
        provider = get_provider()  # Returns OpenAI or Llama or Hybrid
        response = await provider.complete(messages, tools)
        # Same interface regardless of backend!
    """

    @property
    def provider_type(self) -> ModelType:
        """Return the provider type (openai, llama, hybrid)"""
        ...

    @property
    def capabilities(self) -> list[ModelCapability]:
        """Return list of capabilities this provider supports"""
        ...

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
        response_format: dict | None = None,
        stream: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate a completion from the model.

        Args:
            messages: List of chat messages [{"role": "user", "content": "..."}]
            model: Model name (e.g., "gpt-4o-mini", "llama-3-70b")
            temperature: Randomness (0.0-1.0)
            max_tokens: Max response tokens
            tools: Function calling tools (OpenAI format)
            tool_choice: Tool selection strategy ("auto", "none", {"name": "..."})
            response_format: Response format (e.g., {"type": "json_object"})
            stream: Enable streaming response
            metadata: Provider-specific metadata (agent_type, conversation_id, etc.)

        Returns:
            {
                "content": "Response text",
                "tool_calls": [...],  # If function calling used
                "finish_reason": "stop" | "tool_calls" | "length",
                "usage": {
                    "input_tokens": 123,
                    "output_tokens": 456,
                    "total_tokens": 579
                },
                "model": "gpt-4o-mini",
                "created_at": datetime.utcnow()
            }
        """
        ...

    async def complete_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream completion chunks from the model.

        Args:
            Same as complete() but without stream parameter

        Yields:
            {
                "delta": "chunk of text",
                "finish_reason": None | "stop" | "tool_calls" | "length",
                "usage": {...}  # Only in final chunk
            }
        """
        ...

    async def embed(
        self, texts: list[str], model: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Generate embeddings for text(s).

        Args:
            texts: List of texts to embed
            model: Embedding model (e.g., "text-embedding-3-small")
            metadata: Provider-specific metadata

        Returns:
            {
                "embeddings": [[0.123, -0.456, ...]],  # List of float vectors
                "model": "text-embedding-3-small",
                "usage": {
                    "input_tokens": 123,
                    "total_tokens": 123
                }
            }
        """
        ...

    async def health_check(self) -> dict[str, Any]:
        """
        Check if provider is healthy and reachable.

        Returns:
            {
                "healthy": True,
                "provider": "openai",
                "latency_ms": 123,
                "models_available": ["gpt-4o-mini", ...],
                "error": None | "error message"
            }
        """
        ...

    def get_default_model(self, capability: ModelCapability) -> str:
        """
        Get default model for a capability.

        Args:
            capability: Capability type (CHAT, EMBEDDING, etc.)

        Returns:
            Model name (e.g., "gpt-4o-mini", "llama-3-70b")
        """
        ...

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """
        Estimate cost in USD for token usage.

        Args:
            input_tokens: Input token count
            output_tokens: Output token count
            model: Model name

        Returns:
            Cost in USD (e.g., 0.00123)
        """
        ...


class ProviderConfig:
    """Configuration for model providers"""

    def __init__(
        self,
        provider_type: ModelType,
        api_key: str | None = None,
        api_base: str | None = None,
        default_chat_model: str | None = None,
        default_embedding_model: str | None = None,
        timeout: int = 60,
        max_retries: int = 3,
        enable_caching: bool = True,
        extra_config: dict[str, Any] | None = None,
    ):
        self.provider_type = provider_type
        self.api_key = api_key
        self.api_base = api_base
        self.default_chat_model = default_chat_model
        self.default_embedding_model = default_embedding_model
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_caching = enable_caching
        self.extra_config = extra_config or {}

    @classmethod
    def from_env(cls, provider_type: ModelType) -> "ProviderConfig":
        """Load provider config from environment variables"""
        import os

        if provider_type == ModelType.OPENAI:
            return cls(
                provider_type=provider_type,
                api_key=os.getenv("OPENAI_API_KEY"),
                default_chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
                default_embedding_model=os.getenv(
                    "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
                ),
                timeout=int(os.getenv("OPENAI_TIMEOUT", "60")),
                max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3")),
            )
        elif provider_type == ModelType.LLAMA:
            return cls(
                provider_type=provider_type,
                api_base=os.getenv("LLAMA_API_BASE", "http://localhost:11434"),
                default_chat_model=os.getenv("LLAMA_CHAT_MODEL", "llama3:70b"),
                default_embedding_model=os.getenv("LLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
                timeout=int(os.getenv("LLAMA_TIMEOUT", "120")),
            )
        elif provider_type == ModelType.HYBRID:
            return cls(
                provider_type=provider_type,
                extra_config={
                    "teacher_model": os.getenv("HYBRID_TEACHER_MODEL", "gpt-4o-mini"),
                    "student_model": os.getenv("HYBRID_STUDENT_MODEL", "llama3:70b"),
                    "confidence_threshold": float(os.getenv("HYBRID_CONFIDENCE_THRESHOLD", "0.7")),
                    "routing_strategy": os.getenv("HYBRID_ROUTING_STRATEGY", "confidence"),
                },
            )
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")


class ProviderError(Exception):
    """Base exception for provider errors"""

    def __init__(
        self,
        message: str,
        provider: str,
        error_code: str | None = None,
        retry_after: int | None = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code
        self.retry_after = retry_after


class RateLimitError(ProviderError):
    """Rate limit exceeded"""


class AuthenticationError(ProviderError):
    """Authentication failed"""


class ModelNotFoundError(ProviderError):
    """Model not available"""


class InvalidRequestError(ProviderError):
    """Invalid request parameters"""
