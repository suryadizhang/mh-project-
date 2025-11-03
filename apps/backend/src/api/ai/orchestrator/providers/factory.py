"""
Model Provider Factory

Creates the appropriate model provider based on configuration.
Enables zero-code provider swapping via environment variables.

Author: MH Backend Team
Created: 2025-10-31 (Phase 1A)
"""

import logging
import os
from typing import Any

from .base import ModelType, ProviderConfig
from .hybrid_provider import HybridProvider
from .llama_provider import LlamaProvider
from .openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """
    Factory for creating model providers.

    Usage:
        # Get provider from environment
        provider = ProviderFactory.create()

        # Get specific provider
        provider = ProviderFactory.create(ModelType.OPENAI)

        # Provider automatically selected based on AI_PROVIDER env var
    """

    _instance: OpenAIProvider | LlamaProvider | HybridProvider | None = None
    _provider_type: ModelType | None = None

    @classmethod
    def create(
        cls, provider_type: ModelType | None = None, force_new: bool = False
    ) -> OpenAIProvider | LlamaProvider | HybridProvider:
        """
        Create or return cached provider instance.

        Args:
            provider_type: Provider to create (None = auto-detect from env)
            force_new: Force creation of new instance (ignore cache)

        Returns:
            Provider instance (OpenAI, Llama, or Hybrid)

        Environment Variables:
            AI_PROVIDER: "openai" (default), "llama", or "hybrid"
            OPENAI_API_KEY: OpenAI API key (required for openai/hybrid)
            LLAMA_API_BASE: Ollama API base URL (required for llama/hybrid)
            HYBRID_CONFIDENCE_THRESHOLD: Confidence threshold for hybrid routing (default: 0.7)
        """

        # Auto-detect provider from environment
        if provider_type is None:
            provider_str = os.getenv("AI_PROVIDER", "openai").lower()

            if provider_str == "openai":
                provider_type = ModelType.OPENAI
            elif provider_str == "llama":
                provider_type = ModelType.LLAMA
            elif provider_str == "hybrid":
                provider_type = ModelType.HYBRID
            else:
                logger.warning(f"Unknown AI_PROVIDER: {provider_str}, defaulting to OpenAI")
                provider_type = ModelType.OPENAI

        # Return cached instance if available
        if not force_new and cls._instance and cls._provider_type == provider_type:
            logger.debug(f"Returning cached {provider_type.value} provider")
            return cls._instance

        # Create new instance
        logger.info(f"Creating new {provider_type.value} provider")

        try:
            if provider_type == ModelType.OPENAI:
                config = ProviderConfig.from_env(ModelType.OPENAI)
                cls._instance = OpenAIProvider(config)

            elif provider_type == ModelType.LLAMA:
                config = ProviderConfig.from_env(ModelType.LLAMA)
                cls._instance = LlamaProvider(config)

            elif provider_type == ModelType.HYBRID:
                config = ProviderConfig.from_env(ModelType.HYBRID)
                cls._instance = HybridProvider(config)

            else:
                raise ValueError(f"Unknown provider type: {provider_type}")

            cls._provider_type = provider_type

            logger.info(f"✅ {provider_type.value.upper()} provider created successfully")

            return cls._instance

        except Exception as e:
            logger.exception(f"Failed to create {provider_type.value} provider: {e}")

            # Fallback to OpenAI if other providers fail
            if provider_type != ModelType.OPENAI:
                logger.warning("Falling back to OpenAI provider")
                config = ProviderConfig.from_env(ModelType.OPENAI)
                cls._instance = OpenAIProvider(config)
                cls._provider_type = ModelType.OPENAI
                return cls._instance
            else:
                raise

    @classmethod
    def reset(cls):
        """Reset cached provider (for testing)"""
        cls._instance = None
        cls._provider_type = None

    @classmethod
    def get_active_provider_type(cls) -> ModelType | None:
        """Get the currently active provider type"""
        return cls._provider_type


def get_provider() -> OpenAIProvider | LlamaProvider | HybridProvider:
    """
    Get the active model provider.

    Convenience function for getting provider instance.
    Provider is cached and reused across calls.

    Returns:
        Active provider (OpenAI, Llama, or Hybrid)

    Example:
        provider = get_provider()
        response = await provider.complete(
            messages=[{"role": "user", "content": "Hello"}]
        )
    """
    return ProviderFactory.create()


async def test_provider() -> dict[str, Any]:
    """
    Test the active provider's health.

    Useful for startup checks and debugging.

    Returns:
        Health check results
    """
    provider = get_provider()
    return await provider.health_check()


# Configuration validation
def validate_provider_config(provider_type: ModelType) -> dict[str, Any]:
    """
    Validate provider configuration.

    Args:
        provider_type: Provider to validate

    Returns:
        {
            "valid": bool,
            "provider": str,
            "missing_vars": [str],
            "warnings": [str]
        }
    """

    missing_vars = []
    warnings = []

    if provider_type == ModelType.OPENAI:
        if not os.getenv("OPENAI_API_KEY"):
            missing_vars.append("OPENAI_API_KEY")

        if not os.getenv("OPENAI_CHAT_MODEL"):
            warnings.append("OPENAI_CHAT_MODEL not set, using default: gpt-4o-mini")

    elif provider_type == ModelType.LLAMA:
        if not os.getenv("LLAMA_API_BASE"):
            missing_vars.append("LLAMA_API_BASE")

        warnings.append(
            "LlamaProvider is a stub - not functional yet. " "See MIGRATION_GUIDE_LLAMA3.md"
        )

    elif provider_type == ModelType.HYBRID:
        if not os.getenv("OPENAI_API_KEY"):
            missing_vars.append("OPENAI_API_KEY")

        if not os.getenv("LLAMA_API_BASE"):
            missing_vars.append("LLAMA_API_BASE")

        warnings.append(
            "HybridProvider is a stub - not functional yet. " "See MIGRATION_GUIDE_FULL_OPTION2.md"
        )

    return {
        "valid": len(missing_vars) == 0,
        "provider": provider_type.value,
        "missing_vars": missing_vars,
        "warnings": warnings,
    }
