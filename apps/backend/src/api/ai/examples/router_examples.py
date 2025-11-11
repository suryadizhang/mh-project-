"""
Intent Router Examples

Demonstrates how to use the IntentRouter for intelligent conversation routing.

Run with:
    cd apps/backend
    PYTHONPATH=src python src/api/ai/examples/router_examples.py
"""

import asyncio
import logging

from api.ai.routers import AgentType, get_intent_router

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def example_1_basic_routing():
    """Example 1: Basic intent routing"""

    router = get_intent_router()

    # Test messages for each intent
    test_messages = [
        "How much does it cost for 50 people?",
        "The chef was late to my event",
        "Are you available on December 15th?",
        "What's your cancellation policy?",
    ]

    for message in test_messages:

        response = await router.route(
            message=message, context={"conversation_id": "example_1", "channel": "webchat"}
        )

        response["routing"]


async def example_2_conversation_continuity():
    """Example 2: Multi-turn conversation with context"""

    router = get_intent_router()

    conversation_id = "example_2"
    conversation_history: list[dict[str, str]] = []

    # Simulate a multi-turn conversation
    messages = [
        "I'm interested in catering for 60 people",
        "What's included in the premium package?",
        "Can I add a sushi station?",
        "Actually, what's your cancellation policy?",
        "Okay, I'd like to book for December 20th",
    ]

    for _i, message in enumerate(messages, 1):

        response = await router.route(
            message=message,
            context={"conversation_id": conversation_id, "channel": "webchat"},
            conversation_history=conversation_history,
        )

        routing = response["routing"]

        if routing.get("intent_transition"):
            pass

        # Update conversation history
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": response["content"]})

    # Show conversation state
    await router.get_conversation_state(conversation_id)


async def example_3_intent_suggestions():
    """Example 3: Get intent suggestions for ambiguous messages"""

    router = get_intent_router()

    # Ambiguous messages
    ambiguous_messages = [
        "I need help",
        "Tell me more about your services",
        "Can I talk to someone?",
        "I'm not sure what I need",
    ]

    for message in ambiguous_messages:

        suggestions = await router.suggest_agent(message, top_k=3)

        for _suggestion in suggestions:
            pass


async def example_4_fallback_routing():
    """Example 4: Fallback routing for low-confidence intents"""

    router = get_intent_router()

    # Messages with potentially low confidence
    test_messages = ["Hello", "What?", "I don't know", "Maybe"]

    for message in test_messages:

        response = await router.route_with_fallback(
            message=message,
            context={"conversation_id": "example_4", "channel": "webchat"},
            confidence_threshold=0.65,
        )

        routing = response["routing"]

        if routing.get("fallback"):
            routing["fallback"]


async def example_5_intent_classification_only():
    """Example 5: Classify intent without routing"""

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

    for message, expected_agent in test_cases:
        agent_type, confidence = await router.classify_intent(message)

        is_correct = agent_type == expected_agent
        correct += int(is_correct)

    (correct / total) * 100


async def example_6_router_statistics():
    """Example 6: Router statistics and monitoring"""

    router = get_intent_router()

    # Simulate some conversations
    test_conversations = [
        ("conv_1", ["How much?", "What packages?", "Book for Saturday"]),
        ("conv_2", ["I'm unhappy", "I want a refund", "Thank you"]),
        ("conv_3", ["What's your policy?", "Tell me about insurance"]),
        ("conv_4", ["Available next week?", "Book for 50 people"]),
    ]

    for conv_id, messages in test_conversations:
        for message in messages:
            await router.route(message=message, context={"conversation_id": conv_id})

    # Get statistics
    stats = router.get_statistics()

    for _intent, count in stats["intent_distribution"].items():
        percentage = (
            (count / stats["total_conversations"]) * 100 if stats["total_conversations"] > 0 else 0
        )
        "█" * int(percentage / 5)


async def example_7_tool_calling():
    """Example 7: Agent tool calling through router"""

    router = get_intent_router()

    # Messages that should trigger tool calls
    tool_call_messages = [
        "Can you recommend a package for 60 guests with a $3000 budget?",
        "Check the status of order ORD-2024-1234",
        "Are you available on December 25th for 80 people?",
        "What's your cancellation policy for events under 14 days?",
    ]

    for message in tool_call_messages:

        response = await router.route(
            message=message, context={"conversation_id": "example_7", "channel": "webchat"}
        )

        response["routing"]

        # Check if tools were called
        if response.get("tool_calls"):
            for tool_call in response["tool_calls"]:
                tool_call["function"]["name"]
        else:
            pass


async def main():
    """Run all examples"""

    try:
        await example_1_basic_routing()
        await example_2_conversation_continuity()
        await example_3_intent_suggestions()
        await example_4_fallback_routing()
        await example_5_intent_classification_only()
        await example_6_router_statistics()
        await example_7_tool_calling()

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
