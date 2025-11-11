"""
Model Provider Module

Provides abstract interfaces for swapping AI models (OpenAI, Llama 3, Hybrid).
Enables zero-rebuild upgrades from OpenAI → Llama → Hybrid routing.

Author: MH Backend Team
Created: 2025-10-31 (Phase 1A)
"""

from .base import (
    AuthenticationError,
    InvalidRequestError,
    ModelCapability,
    ModelNotFoundError,
    ModelProvider,
    ModelType,
    ProviderConfig,
    ProviderError,
    RateLimitError,
)
from .factory import (
    ProviderFactory,
    get_provider,
    test_provider,
    validate_provider_config,
)
from .hybrid_provider import HybridProvider
from .llama_provider import LlamaProvider
from .openai_provider import OpenAIProvider

__all__ = [
    "AuthenticationError",
    "HybridProvider",
    "InvalidRequestError",
    "LlamaProvider",
    "ModelCapability",
    "ModelNotFoundError",
    # Base classes
    "ModelProvider",
    "ModelType",
    # Provider implementations
    "OpenAIProvider",
    "ProviderConfig",
    # Exceptions
    "ProviderError",
    # Factory
    "ProviderFactory",
    "RateLimitError",
    "get_provider",
    "test_provider",
    "validate_provider_config",
]
