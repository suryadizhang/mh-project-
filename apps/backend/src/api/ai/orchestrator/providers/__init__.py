"""
Model Provider Module

Provides abstract interfaces for swapping AI models (OpenAI, Llama 3, Hybrid).
Enables zero-rebuild upgrades from OpenAI → Llama → Hybrid routing.

Author: MH Backend Team
Created: 2025-10-31 (Phase 1A)
"""

from .base import (
    ModelProvider,
    ModelType,
    ModelCapability,
    ProviderConfig,
    ProviderError,
    RateLimitError,
    AuthenticationError,
    ModelNotFoundError,
    InvalidRequestError
)

from .openai_provider import OpenAIProvider
from .llama_provider import LlamaProvider
from .hybrid_provider import HybridProvider

from .factory import (
    ProviderFactory,
    get_provider,
    test_provider,
    validate_provider_config
)

__all__ = [
    # Base classes
    "ModelProvider",
    "ModelType",
    "ModelCapability",
    "ProviderConfig",
    
    # Exceptions
    "ProviderError",
    "RateLimitError",
    "AuthenticationError",
    "ModelNotFoundError",
    "InvalidRequestError",
    
    # Provider implementations
    "OpenAIProvider",
    "LlamaProvider",
    "HybridProvider",
    
    # Factory
    "ProviderFactory",
    "get_provider",
    "test_provider",
    "validate_provider_config",
]
