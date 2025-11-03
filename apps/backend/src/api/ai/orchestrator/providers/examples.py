"""
Model Provider Usage Examples

Demonstrates how to use the model provider system.
Shows OpenAI usage now, and how to swap to Llama/Hybrid later.

Author: MH Backend Team
Created: 2025-10-31 (Phase 1A)
"""

import asyncio
import os

# Set environment (would be in .env file in production)
os.environ["AI_PROVIDER"] = "openai"  # or "llama" or "hybrid"
os.environ["OPENAI_API_KEY"] = "your-key-here"  # Required for OpenAI
os.environ["OPENAI_CHAT_MODEL"] = "gpt-4o-mini"

from .factory import get_provider


async def example_basic_chat():
    """Example 1: Basic chat completion"""

    provider = get_provider()

    await provider.complete(
        messages=[
            {"role": "system", "content": "You are a helpful customer service agent."},
            {"role": "user", "content": "What are your business hours?"},
        ],
        temperature=0.7,
        max_tokens=150,
    )


async def example_function_calling():
    """Example 2: Function calling (OpenAI only for now)"""

    provider = get_provider()

    # Define available tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "check_order_status",
                "description": "Check the status of a customer order",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": "The order ID to check"}
                    },
                    "required": ["order_id"],
                },
            },
        }
    ]

    response = await provider.complete(
        messages=[{"role": "user", "content": "What's the status of order #12345?"}],
        tools=tools,
        tool_choice="auto",
    )

    if response["tool_calls"]:
        for _tool_call in response["tool_calls"]:
            pass
    else:
        pass


async def example_streaming():
    """Example 3: Streaming responses"""

    provider = get_provider()

    async for chunk in provider.complete_stream(
        messages=[{"role": "user", "content": "Write a short thank you message to a customer."}],
        temperature=0.7,
        max_tokens=100,
    ):
        if chunk["delta"]:
            pass

        if chunk["finish_reason"] == "stop" and chunk.get("usage"):
            pass


async def example_embeddings():
    """Example 4: Generate embeddings"""

    provider = get_provider()

    texts = [
        "How do I reset my password?",
        "What are your business hours?",
        "I want to cancel my order",
    ]

    await provider.embed(texts)


async def example_with_metadata():
    """Example 5: Track usage with metadata"""

    provider = get_provider()

    # Metadata is used for cost monitoring and analytics
    await provider.complete(
        messages=[{"role": "user", "content": "Tell me about your products"}],
        metadata={
            "conversation_id": "conv_12345",
            "agent_type": "lead_nurturing",
            "channel": "webchat",
            "customer_id": "cust_789",
        },
    )


async def example_health_check():
    """Example 6: Provider health check"""

    provider = get_provider()

    health = await provider.health_check()

    if health["error"]:
        pass


async def example_swap_providers():
    """Example 7: How to swap providers (zero code changes!)"""

    # Scenario 1: Using OpenAI (current, default)
    os.environ["AI_PROVIDER"] = "openai"

    from .factory import ProviderFactory

    ProviderFactory.reset()  # Clear cache

    get_provider()

    # Scenario 2: Switch to Llama 3 (when API costs >$500/month)
    os.environ["AI_PROVIDER"] = "llama"
    os.environ["LLAMA_API_BASE"] = "http://localhost:11434"

    ProviderFactory.reset()  # Clear cache

    get_provider()

    # Scenario 3: Hybrid routing (teacher-student)
    os.environ["AI_PROVIDER"] = "hybrid"
    os.environ["HYBRID_CONFIDENCE_THRESHOLD"] = "0.7"

    ProviderFactory.reset()  # Clear cache

    get_provider()

    # Reset to OpenAI
    os.environ["AI_PROVIDER"] = "openai"
    ProviderFactory.reset()


async def example_cost_comparison():
    """Example 8: Cost comparison across providers"""

    # Simulate 1 million tokens (typical monthly usage)
    input_tokens = 600_000  # 60% input
    output_tokens = 400_000  # 40% output

    from .base import ModelType, ProviderConfig
    from .hybrid_provider import HybridProvider
    from .llama_provider import LlamaProvider
    from .openai_provider import OpenAIProvider

    # OpenAI costs
    openai_config = ProviderConfig.from_env(ModelType.OPENAI)
    openai = OpenAIProvider(openai_config)
    openai.estimate_cost(input_tokens, output_tokens, "gpt-4o-mini")

    # Llama costs (free, runs locally)
    llama_config = ProviderConfig.from_env(ModelType.LLAMA)
    llama = LlamaProvider(llama_config)
    llama.estimate_cost(input_tokens, output_tokens, "llama3:70b")

    # Hybrid costs (80% Llama, 20% OpenAI)
    hybrid_config = ProviderConfig.from_env(ModelType.HYBRID)
    hybrid = HybridProvider(hybrid_config)
    hybrid.estimate_cost(input_tokens, output_tokens, "gpt-4o-mini")


async def run_all_examples():
    """Run all examples"""

    try:
        await example_basic_chat()
        await example_function_calling()
        await example_streaming()
        await example_embeddings()
        await example_with_metadata()
        await example_health_check()
        await example_swap_providers()
        await example_cost_comparison()

    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run examples
    asyncio.run(run_all_examples())
