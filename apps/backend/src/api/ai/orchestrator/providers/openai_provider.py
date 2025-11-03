"""
OpenAI Model Provider

Production implementation using OpenAI API (GPT-4o-mini, embeddings).
Includes automatic cost tracking and usage monitoring.

Author: MH Backend Team
Created: 2025-10-31 (Phase 1A)
"""

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
import logging
import time
from typing import Any

try:
    from openai import APIError as OpenAIAPIError
    from openai import AsyncOpenAI
    from openai import AuthenticationError as OpenAIAuthError
    from openai import RateLimitError as OpenAIRateLimitError
except ImportError:
    # Graceful degradation if OpenAI not installed
    AsyncOpenAI = None
    OpenAIRateLimitError = Exception
    OpenAIAuthError = Exception
    OpenAIAPIError = Exception

from ...monitoring.pricing import calculate_cost
from ...monitoring.usage_tracker import UsageTracker
from .base import (
    AuthenticationError,
    InvalidRequestError,
    ModelCapability,
    ModelType,
    ProviderConfig,
    ProviderError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """
    OpenAI API provider implementation.

    Features:
    - GPT-4o-mini for chat completions
    - text-embedding-3-small for embeddings
    - Automatic cost tracking via UsageTracker
    - Retry logic with exponential backoff
    - Streaming support
    - Function calling support

    Usage:
        provider = OpenAIProvider(config)
        response = await provider.complete(messages=[{"role": "user", "content": "Hello"}])
        print(response["content"])  # AI response
    """

    def __init__(self, config: ProviderConfig):
        if AsyncOpenAI is None:
            raise ImportError("OpenAI package not installed. Run: pip install openai")

        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key, timeout=config.timeout, max_retries=config.max_retries
        )
        self.usage_tracker = UsageTracker()

        # Default models
        self._default_chat_model = config.default_chat_model or "gpt-4o-mini"
        self._default_embedding_model = config.default_embedding_model or "text-embedding-3-small"

        logger.info(f"OpenAI provider initialized (chat: {self._default_chat_model})")

    @property
    def provider_type(self) -> ModelType:
        return ModelType.OPENAI

    @property
    def capabilities(self) -> list[ModelCapability]:
        return [
            ModelCapability.CHAT,
            ModelCapability.EMBEDDING,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.STREAMING,
            ModelCapability.JSON_MODE,
        ]

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
        """Generate completion using OpenAI API"""

        if stream:
            raise InvalidRequestError(
                "Use complete_stream() for streaming responses", provider="openai"
            )

        model = model or self._default_chat_model
        metadata = metadata or {}

        start_time = time.time()

        try:
            # Build request parameters
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if tools:
                params["tools"] = tools
                params["tool_choice"] = tool_choice or "auto"

            if response_format:
                params["response_format"] = response_format

            # Call OpenAI API
            response = await self.client.chat.completions.create(**params)

            # Extract response data
            choice = response.choices[0]
            message = choice.message

            result = {
                "content": message.content or "",
                "tool_calls": [],
                "finish_reason": choice.finish_reason,
                "usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "model": response.model,
                "created_at": datetime.utcnow(),
                "latency_ms": int((time.time() - start_time) * 1000),
            }

            # Extract tool calls if present
            if message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in message.tool_calls
                ]

            # Track usage and cost (async, don't await to avoid blocking)
            asyncio.create_task(
                self._track_usage(
                    model=response.model,
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    metadata=metadata,
                )
            )

            logger.info(
                f"OpenAI completion: {response.usage.total_tokens} tokens, "
                f"{result['latency_ms']}ms, {choice.finish_reason}"
            )

            return result

        except OpenAIRateLimitError as e:
            logger.exception(f"OpenAI rate limit: {e}")
            raise RateLimitError(
                str(e),
                provider="openai",
                error_code="rate_limit",
                retry_after=getattr(e, "retry_after", None),
            )

        except OpenAIAuthError as e:
            logger.exception(f"OpenAI auth error: {e}")
            raise AuthenticationError(str(e), provider="openai", error_code="authentication_failed")

        except OpenAIAPIError as e:
            logger.exception(f"OpenAI API error: {e}")
            raise ProviderError(
                str(e), provider="openai", error_code=getattr(e, "code", "api_error")
            )

        except Exception as e:
            logger.error(f"Unexpected error in OpenAI provider: {e}", exc_info=True)
            raise ProviderError(
                f"Unexpected error: {e}", provider="openai", error_code="unknown_error"
            )

    async def complete_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream completion chunks from OpenAI"""

        model = model or self._default_chat_model
        metadata = metadata or {}

        start_time = time.time()
        total_input_tokens = 0
        total_output_tokens = 0

        try:
            # Build request parameters
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            }

            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            # Stream from OpenAI
            stream = await self.client.chat.completions.create(**params)

            async for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta

                # Track tokens if available
                if hasattr(chunk, "usage") and chunk.usage:
                    total_input_tokens = chunk.usage.prompt_tokens
                    total_output_tokens = chunk.usage.completion_tokens

                yield {
                    "delta": delta.content or "",
                    "finish_reason": choice.finish_reason,
                    "tool_calls": delta.tool_calls if hasattr(delta, "tool_calls") else None,
                    "usage": None,  # Usage only in final chunk
                }

            # Final chunk with usage
            yield {
                "delta": "",
                "finish_reason": "stop",
                "tool_calls": None,
                "usage": {
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "total_tokens": total_input_tokens + total_output_tokens,
                },
                "latency_ms": int((time.time() - start_time) * 1000),
            }

            # Track usage
            if total_input_tokens > 0:
                asyncio.create_task(
                    self._track_usage(
                        model=model,
                        input_tokens=total_input_tokens,
                        output_tokens=total_output_tokens,
                        metadata=metadata,
                    )
                )

        except Exception as e:
            logger.error(f"Error in OpenAI streaming: {e}", exc_info=True)
            raise ProviderError(
                f"Streaming error: {e}", provider="openai", error_code="streaming_error"
            )

    async def embed(
        self, texts: list[str], model: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Generate embeddings using OpenAI"""

        model = model or self._default_embedding_model
        metadata = metadata or {}

        try:
            response = await self.client.embeddings.create(model=model, input=texts)

            embeddings = [item.embedding for item in response.data]

            result = {
                "embeddings": embeddings,
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

            # Track embedding usage
            asyncio.create_task(
                self._track_usage(
                    model=response.model,
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=0,
                    metadata={**metadata, "embedding": True},
                )
            )

            logger.info(
                f"OpenAI embeddings: {len(texts)} texts, {response.usage.total_tokens} tokens"
            )

            return result

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}", exc_info=True)
            raise ProviderError(
                f"Embedding error: {e}", provider="openai", error_code="embedding_error"
            )

    async def health_check(self) -> dict[str, Any]:
        """Check OpenAI API health"""

        start_time = time.time()

        try:
            # Simple test request
            await self.client.chat.completions.create(
                model=self._default_chat_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )

            latency = int((time.time() - start_time) * 1000)

            return {
                "healthy": True,
                "provider": "openai",
                "latency_ms": latency,
                "models_available": [self._default_chat_model, self._default_embedding_model],
                "error": None,
            }

        except Exception as e:
            logger.exception(f"OpenAI health check failed: {e}")
            return {
                "healthy": False,
                "provider": "openai",
                "latency_ms": int((time.time() - start_time) * 1000),
                "models_available": [],
                "error": str(e),
            }

    def get_default_model(self, capability: ModelCapability) -> str:
        """Get default model for capability"""

        if capability == ModelCapability.CHAT:
            return self._default_chat_model
        elif capability == ModelCapability.EMBEDDING:
            return self._default_embedding_model
        elif capability == ModelCapability.FUNCTION_CALLING:
            return self._default_chat_model  # GPT-4o-mini supports function calling
        elif capability in (ModelCapability.STREAMING, ModelCapability.JSON_MODE):
            return self._default_chat_model
        else:
            return self._default_chat_model

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Estimate cost using pricing module"""
        return calculate_cost(model, input_tokens, output_tokens)

    async def _track_usage(
        self, model: str, input_tokens: int, output_tokens: int, metadata: dict[str, Any]
    ):
        """
        Track API usage and cost (internal helper).

        NOTE: Database tracking temporarily disabled in Phase 1A.
        Usage metadata is still returned in API responses for monitoring.
        Full database integration will be implemented in Phase 1B with
        Intelligence Layer database schema.
        """

        try:
            # Phase 1A: In-memory tracking only (database tracking disabled)
            # TODO Phase 1B: Implement proper async database tracking with Intelligence Layer
            cost = self.estimate_cost(input_tokens, output_tokens, model)
            logger.debug(
                f"Usage tracked (in-memory): {model} | "
                f"{input_tokens + output_tokens} tokens | "
                f"${cost:.6f}"
            )

            # Database tracking will be implemented in Phase 1B with:
            # - Async SQLAlchemy session management from core.database
            # - Intelligence Layer schema (emotion, memory, follow-ups)
            # - Cross-channel conversation history
            # - Analytics aggregation

            # Uncomment when Phase 1B database is ready:
            # from ......core.database import get_db
            # async for db in get_db():
            #     await self.usage_tracker.record_usage(
            #         db=db,
            #         model=model,
            #         input_tokens=input_tokens,
            #         output_tokens=output_tokens,
            #         conversation_id=metadata.get("conversation_id"),
            #         agent_type=metadata.get("agent_type"),
            #         channel=metadata.get("channel")
            #     )
            #     break  # Only need first session

        except Exception as e:
            # Don't fail the request if tracking fails
            logger.error(f"Failed to track usage: {e}", exc_info=True)
