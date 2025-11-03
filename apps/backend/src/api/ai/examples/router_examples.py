"""
Intent Router Examples

Demonstrates how to use the IntentRouter for intelligent conversation routing.

Run with:
    cd apps/backend
    PYTHONPATH=src python src/api/ai/examples/router_examples.py
"""

import asyncio
import logging
from typing import List, Dict

from api.ai.routers import get_intent_router, AgentType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_1_basic_routing():
    """Example 1: Basic intent routing"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Intent Routing")
    print("="*80)
    
    router = get_intent_router()
    
    # Test messages for each intent
    test_messages = [
        "How much does it cost for 50 people?",
        "The chef was late to my event",
        "Are you available on December 15th?",
        "What's your cancellation policy?"
    ]
    
    for message in test_messages:
        print(f"\n📨 User: {message}")
        
        response = await router.route(
            message=message,
            context={
                "conversation_id": "example_1",
                "channel": "webchat"
            }
        )
        
        routing = response["routing"]
        print(f"🤖 Agent: {routing['agent_type']}")
        print(f"📊 Confidence: {routing['confidence']:.2%}")
        print(f"⏱️  Latency: {routing['total_latency_ms']:.0f}ms")
        print(f"💬 Response: {response['content'][:200]}...")


async def example_2_conversation_continuity():
    """Example 2: Multi-turn conversation with context"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Multi-Turn Conversation Continuity")
    print("="*80)
    
    router = get_intent_router()
    
    conversation_id = "example_2"
    conversation_history: List[Dict[str, str]] = []
    
    # Simulate a multi-turn conversation
    messages = [
        "I'm interested in catering for 60 people",
        "What's included in the premium package?",
        "Can I add a sushi station?",
        "Actually, what's your cancellation policy?",
        "Okay, I'd like to book for December 20th"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n--- Turn {i} ---")
        print(f"📨 User: {message}")
        
        response = await router.route(
            message=message,
            context={
                "conversation_id": conversation_id,
                "channel": "webchat"
            },
            conversation_history=conversation_history
        )
        
        routing = response["routing"]
        print(f"🤖 Agent: {routing['agent_type']}")
        print(f"📊 Confidence: {routing['confidence']:.2%}")
        
        if routing.get("intent_transition"):
            print(f"🔄 Transitioned from: {routing['intent_transition']}")
        
        print(f"💬 Response: {response['content'][:150]}...")
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": response["content"]})
    
    # Show conversation state
    print("\n--- Conversation State ---")
    state = await router.get_conversation_state(conversation_id)
    print(f"Current agent: {state['current_agent'].value}")
    print(f"Intent history: {len(state['intent_history'])} intents classified")


async def example_3_intent_suggestions():
    """Example 3: Get intent suggestions for ambiguous messages"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Intent Suggestions (Ambiguous Messages)")
    print("="*80)
    
    router = get_intent_router()
    
    # Ambiguous messages
    ambiguous_messages = [
        "I need help",
        "Tell me more about your services",
        "Can I talk to someone?",
        "I'm not sure what I need"
    ]
    
    for message in ambiguous_messages:
        print(f"\n📨 User: {message}")
        print("🤔 Suggested agents:")
        
        suggestions = await router.suggest_agent(message, top_k=3)
        
        for suggestion in suggestions:
            print(
                f"   • {suggestion['agent_type']:<20} "
                f"{suggestion['confidence']:.2%}  "
                f"({suggestion['description']})"
            )


async def example_4_fallback_routing():
    """Example 4: Fallback routing for low-confidence intents"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Fallback Routing (Low Confidence)")
    print("="*80)
    
    router = get_intent_router()
    
    # Messages with potentially low confidence
    test_messages = [
        "Hello",
        "What?",
        "I don't know",
        "Maybe"
    ]
    
    for message in test_messages:
        print(f"\n📨 User: {message}")
        
        response = await router.route_with_fallback(
            message=message,
            context={
                "conversation_id": "example_4",
                "channel": "webchat"
            },
            confidence_threshold=0.65
        )
        
        routing = response["routing"]
        print(f"🤖 Agent: {routing['agent_type']}")
        print(f"📊 Confidence: {routing['confidence']:.2%}")
        
        if routing.get("fallback"):
            fallback = routing["fallback"]
            print(f"⚠️  Fallback triggered!")
            print(f"   Original agent: {fallback['original_agent']}")
            print(f"   Original confidence: {fallback['original_confidence']:.2%}")
            print(f"   Threshold: {fallback['threshold']:.2%}")
        
        print(f"💬 Response: {response['content'][:150]}...")


async def example_5_intent_classification_only():
    """Example 5: Classify intent without routing"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Intent Classification Only")
    print("="*80)
    
    router = get_intent_router()
    
    # Test messages
    test_cases = [
        ("How much for 100 guests?", AgentType.LEAD_NURTURING),
        ("I want a refund!", AgentType.CUSTOMER_CARE),
        ("Can I reschedule to next week?", AgentType.OPERATIONS),
        ("What's your deposit policy?", AgentType.KNOWLEDGE),
    ]
    
    correct = 0
    total = len(test_cases)
    
    print("\nClassification Accuracy Test:")
    print("-" * 60)
    
    for message, expected_agent in test_cases:
        agent_type, confidence = await router.classify_intent(message)
        
        is_correct = agent_type == expected_agent
        correct += int(is_correct)
        
        status = "✅" if is_correct else "❌"
        
        print(
            f"{status} {message[:40]:<40} | "
            f"Expected: {expected_agent.value:<20} | "
            f"Got: {agent_type.value:<20} | "
            f"Confidence: {confidence:.2%}"
        )
    
    accuracy = (correct / total) * 100
    print("-" * 60)
    print(f"Accuracy: {correct}/{total} ({accuracy:.1f}%)")


async def example_6_router_statistics():
    """Example 6: Router statistics and monitoring"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Router Statistics")
    print("="*80)
    
    router = get_intent_router()
    
    # Simulate some conversations
    test_conversations = [
        ("conv_1", ["How much?", "What packages?", "Book for Saturday"]),
        ("conv_2", ["I'm unhappy", "I want a refund", "Thank you"]),
        ("conv_3", ["What's your policy?", "Tell me about insurance"]),
        ("conv_4", ["Available next week?", "Book for 50 people"]),
    ]
    
    print("\nSimulating conversations...")
    for conv_id, messages in test_conversations:
        for message in messages:
            await router.route(
                message=message,
                context={"conversation_id": conv_id}
            )
    
    # Get statistics
    stats = router.get_statistics()
    
    print("\n📊 Router Statistics:")
    print(f"   Total conversations: {stats['total_conversations']}")
    print(f"   Intent transitions: {stats['intent_transitions']}")
    print(f"   Embeddings computed: {stats['embeddings_computed']}")
    print(f"   Agents loaded: {len(stats['agents_loaded'])}")
    
    print("\n📈 Intent Distribution:")
    for intent, count in stats['intent_distribution'].items():
        percentage = (count / stats['total_conversations']) * 100 if stats['total_conversations'] > 0 else 0
        bar = "█" * int(percentage / 5)
        print(f"   {intent:<20} | {bar} {count} ({percentage:.1f}%)")


async def example_7_tool_calling():
    """Example 7: Agent tool calling through router"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Tool Calling Through Router")
    print("="*80)
    
    router = get_intent_router()
    
    # Messages that should trigger tool calls
    tool_call_messages = [
        "Can you recommend a package for 60 guests with a $3000 budget?",
        "Check the status of order ORD-2024-1234",
        "Are you available on December 25th for 80 people?",
        "What's your cancellation policy for events under 14 days?"
    ]
    
    for message in tool_call_messages:
        print(f"\n📨 User: {message}")
        
        response = await router.route(
            message=message,
            context={
                "conversation_id": "example_7",
                "channel": "webchat"
            }
        )
        
        routing = response["routing"]
        print(f"🤖 Agent: {routing['agent_type']}")
        
        # Check if tools were called
        if response.get("tool_calls"):
            print(f"🔧 Tools called: {len(response['tool_calls'])}")
            for tool_call in response["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                print(f"   • {tool_name}")
        else:
            print("🔧 No tools called")
        
        print(f"💬 Response: {response['content'][:200]}...")


async def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("INTENT ROUTER EXAMPLES")
    print("="*80)
    print("\nThis demonstrates the intelligent routing capabilities of the")
    print("Intent Router, which uses semantic embeddings to classify user")
    print("intent and route conversations to specialized agents.")
    print("\n" + "="*80)
    
    try:
        await example_1_basic_routing()
        await example_2_conversation_continuity()
        await example_3_intent_suggestions()
        await example_4_fallback_routing()
        await example_5_intent_classification_only()
        await example_6_router_statistics()
        await example_7_tool_calling()
        
        print("\n" + "="*80)
        print("✅ All examples completed successfully!")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
