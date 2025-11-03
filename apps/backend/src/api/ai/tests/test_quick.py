"""Quick test to verify orchestrator integration"""

import asyncio

from api.ai.orchestrator import AIOrchestrator, OrchestratorRequest


async def main():
    orch = AIOrchestrator(use_router=True)

    orch.get_statistics()

    request = OrchestratorRequest(
        message="How much for 50 people?", channel="webchat", customer_context={}
    )

    await orch.process_inquiry(request)


if __name__ == "__main__":
    asyncio.run(main())
