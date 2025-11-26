"""Test router and orchestrator integration with detailed logging"""

import asyncio
import logging

# Set up logging first
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def main():

    # Test 1: Import router
    try:
        from api.ai.routers import get_intent_router

        router = get_intent_router()
    except Exception:
        import traceback

        traceback.print_exc()
        return

    # Test 2: Import provider
    try:
        from api.ai.orchestrator.providers import get_provider

        get_provider()
    except Exception:
        import traceback

        traceback.print_exc()
        return

    # Test 3: Import orchestrator
    try:
        from api.ai.orchestrator import AIOrchestrator

        orch = AIOrchestrator(use_router=True)
        orch.get_statistics()
    except Exception:
        import traceback

        traceback.print_exc()
        return

    # Test 4: Simple classification
    try:
        agent_type, confidence = await router.classify_intent("How much for 50 people?")
    except Exception:
        import traceback

        traceback.print_exc()

    # Test 5: Simple routing
    try:
        response = await router.route(
            message="What's your cancellation policy?", context={"conversation_id": "test_123"}
        )
        response.get("routing", {})
    except Exception:
        import traceback

        traceback.print_exc()

    # Test 6: Full orchestrator integration
    try:
        from api.ai.orchestrator import OrchestratorRequest

        request = OrchestratorRequest(
            message="I'm interested in booking for 60 people",
            channel="webchat",
            customer_context={},
        )

        response = await orch.process_inquiry(request)
    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

