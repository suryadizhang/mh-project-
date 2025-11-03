"""
Model Provider Usage Examples

Demonstrates how to use the model provider system.
Shows OpenAI usage now, and how to swap to Llama/Hybrid later.

Author: MH Backend Team
Created: 2025-10-31 (Phase 1A)
"""

import asyncio
import os
from typing import List, Dict

# Set environment (would be in .env file in production)
os.environ["AI_PROVIDER"] = "openai"  # or "llama" or "hybrid"
os.environ["OPENAI_API_KEY"] = "your-key-here"  # Required for OpenAI
os.environ["OPENAI_CHAT_MODEL"] = "gpt-4o-mini"

from .factory import get_provider
from .base import ModelCapability


async def example_basic_chat():
    """Example 1: Basic chat completion"""
    
    print("\n=== Example 1: Basic Chat ===")
    
    provider = get_provider()
    
    response = await provider.complete(
        messages=[
            {"role": "system", "content": "You are a helpful customer service agent."},
            {"role": "user", "content": "What are your business hours?"}
        ],
        temperature=0.7,
        max_tokens=150
    )
    
    print(f"Response: {response['content']}")
    print(f"Model: {response['model']}")
    print(f"Tokens: {response['usage']['total_tokens']}")
    print(f"Latency: {response['latency_ms']}ms")
    print(f"Cost: ${provider.estimate_cost(response['usage']['input_tokens'], response['usage']['output_tokens'], response['model']):.4f}")


async def example_function_calling():
    """Example 2: Function calling (OpenAI only for now)"""
    
    print("\n=== Example 2: Function Calling ===")
    
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
                        "order_id": {
                            "type": "string",
                            "description": "The order ID to check"
                        }
                    },
                    "required": ["order_id"]
                }
            }
        }
    ]
    
    response = await provider.complete(
        messages=[
            {"role": "user", "content": "What's the status of order #12345?"}
        ],
        tools=tools,
        tool_choice="auto"
    )
    
    if response["tool_calls"]:
        print("Tool calls requested:")
        for tool_call in response["tool_calls"]:
            print(f"  - {tool_call['function']['name']}")
            print(f"    Args: {tool_call['function']['arguments']}")
    else:
        print(f"Response: {response['content']}")


async def example_streaming():
    """Example 3: Streaming responses"""
    
    print("\n=== Example 3: Streaming ===")
    
    provider = get_provider()
    
    print("Streaming response: ", end="", flush=True)
    
    async for chunk in provider.complete_stream(
        messages=[
            {"role": "user", "content": "Write a short thank you message to a customer."}
        ],
        temperature=0.7,
        max_tokens=100
    ):
        if chunk["delta"]:
            print(chunk["delta"], end="", flush=True)
        
        if chunk["finish_reason"] == "stop":
            print("\n")
            if chunk.get("usage"):
                print(f"Total tokens: {chunk['usage']['total_tokens']}")
                print(f"Latency: {chunk['latency_ms']}ms")


async def example_embeddings():
    """Example 4: Generate embeddings"""
    
    print("\n=== Example 4: Embeddings ===")
    
    provider = get_provider()
    
    texts = [
        "How do I reset my password?",
        "What are your business hours?",
        "I want to cancel my order"
    ]
    
    result = await provider.embed(texts)
    
    print(f"Generated embeddings for {len(texts)} texts")
    print(f"Embedding dimension: {len(result['embeddings'][0])}")
    print(f"Model: {result['model']}")
    print(f"Tokens used: {result['usage']['total_tokens']}")


async def example_with_metadata():
    """Example 5: Track usage with metadata"""
    
    print("\n=== Example 5: Usage Tracking ===")
    
    provider = get_provider()
    
    # Metadata is used for cost monitoring and analytics
    response = await provider.complete(
        messages=[
            {"role": "user", "content": "Tell me about your products"}
        ],
        metadata={
            "conversation_id": "conv_12345",
            "agent_type": "lead_nurturing",
            "channel": "webchat",
            "customer_id": "cust_789"
        }
    )
    
    print(f"Response: {response['content'][:100]}...")
    print("Metadata was recorded for cost monitoring!")


async def example_health_check():
    """Example 6: Provider health check"""
    
    print("\n=== Example 6: Health Check ===")
    
    provider = get_provider()
    
    health = await provider.health_check()
    
    print(f"Provider: {health['provider']}")
    print(f"Healthy: {health['healthy']}")
    print(f"Latency: {health['latency_ms']}ms")
    print(f"Models available: {', '.join(health['models_available'])}")
    
    if health['error']:
        print(f"Error: {health['error']}")


async def example_swap_providers():
    """Example 7: How to swap providers (zero code changes!)"""
    
    print("\n=== Example 7: Provider Swapping ===")
    
    # Scenario 1: Using OpenAI (current, default)
    print("\n📌 Scenario 1: OpenAI Provider (current)")
    os.environ["AI_PROVIDER"] = "openai"
    
    from .factory import ProviderFactory
    ProviderFactory.reset()  # Clear cache
    
    provider = get_provider()
    print(f"  Active provider: {provider.provider_type.value}")
    print(f"  Default model: {provider.get_default_model(ModelCapability.CHAT)}")
    
    # Scenario 2: Switch to Llama 3 (when API costs >$500/month)
    print("\n📌 Scenario 2: Llama Provider (Option 2 - when ready)")
    os.environ["AI_PROVIDER"] = "llama"
    os.environ["LLAMA_API_BASE"] = "http://localhost:11434"
    
    ProviderFactory.reset()  # Clear cache
    
    provider = get_provider()
    print(f"  Active provider: {provider.provider_type.value}")
    print(f"  Default model: {provider.get_default_model(ModelCapability.CHAT)}")
    print(f"  ⚠️ Note: Llama is a stub - not functional yet")
    
    # Scenario 3: Hybrid routing (teacher-student)
    print("\n📌 Scenario 3: Hybrid Provider (full Option 2)")
    os.environ["AI_PROVIDER"] = "hybrid"
    os.environ["HYBRID_CONFIDENCE_THRESHOLD"] = "0.7"
    
    ProviderFactory.reset()  # Clear cache
    
    provider = get_provider()
    print(f"  Active provider: {provider.provider_type.value}")
    print(f"  Routing: 80% Llama (free), 20% OpenAI (complex)")
    print(f"  Cost savings: ~75% vs OpenAI-only")
    print(f"  ⚠️ Note: Hybrid is a stub - not functional yet")
    
    # Reset to OpenAI
    os.environ["AI_PROVIDER"] = "openai"
    ProviderFactory.reset()
    
    print("\n✅ Key insight: Same code works with all providers!")
    print("   Just change AI_PROVIDER env var - zero code changes!")


async def example_cost_comparison():
    """Example 8: Cost comparison across providers"""
    
    print("\n=== Example 8: Cost Comparison ===")
    
    # Simulate 1 million tokens (typical monthly usage)
    input_tokens = 600_000  # 60% input
    output_tokens = 400_000  # 40% output
    
    from .openai_provider import OpenAIProvider
    from .llama_provider import LlamaProvider
    from .hybrid_provider import HybridProvider
    from .base import ProviderConfig, ModelType
    
    # OpenAI costs
    openai_config = ProviderConfig.from_env(ModelType.OPENAI)
    openai = OpenAIProvider(openai_config)
    openai_cost = openai.estimate_cost(input_tokens, output_tokens, "gpt-4o-mini")
    
    # Llama costs (free, runs locally)
    llama_config = ProviderConfig.from_env(ModelType.LLAMA)
    llama = LlamaProvider(llama_config)
    llama_cost = llama.estimate_cost(input_tokens, output_tokens, "llama3:70b")
    
    # Hybrid costs (80% Llama, 20% OpenAI)
    hybrid_config = ProviderConfig.from_env(ModelType.HYBRID)
    hybrid = HybridProvider(hybrid_config)
    hybrid_cost = hybrid.estimate_cost(input_tokens, output_tokens, "gpt-4o-mini")
    
    print(f"\n💰 Monthly cost for 1M tokens:")
    print(f"  OpenAI only:  ${openai_cost:.2f}/month")
    print(f"  Llama only:   ${llama_cost:.2f}/month (+ $1,500 server)")
    print(f"  Hybrid:       ${hybrid_cost:.2f}/month (+ $1,500 server)")
    
    print(f"\n📊 Savings vs OpenAI:")
    print(f"  Llama:  {((openai_cost - llama_cost) / openai_cost * 100):.1f}% API savings")
    print(f"  Hybrid: {((openai_cost - hybrid_cost) / openai_cost * 100):.1f}% API savings")
    
    print(f"\n🎯 Break-even point:")
    print(f"  Llama becomes profitable at ${1500 / (openai_cost - llama_cost):.0f} monthly API spend")
    print(f"  Current threshold: $500/month (conservative)")


async def run_all_examples():
    """Run all examples"""
    
    print("=" * 60)
    print("MODEL PROVIDER SYSTEM - USAGE EXAMPLES")
    print("=" * 60)
    
    try:
        await example_basic_chat()
        await example_function_calling()
        await example_streaming()
        await example_embeddings()
        await example_with_metadata()
        await example_health_check()
        await example_swap_providers()
        await example_cost_comparison()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run examples
    asyncio.run(run_all_examples())
