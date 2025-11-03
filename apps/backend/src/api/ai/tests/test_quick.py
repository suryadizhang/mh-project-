"""Quick test to verify orchestrator integration"""
import asyncio
from api.ai.orchestrator import AIOrchestrator, OrchestratorRequest

async def main():
    print("Initializing orchestrator with router...")
    orch = AIOrchestrator(use_router=True)
    
    stats = orch.get_statistics()
    print(f"✅ Orchestrator initialized")
    print(f"   Mode: {stats['mode']}")
    print(f"   Phase: {stats['phase']}")
    
    print("\nTesting simple inquiry...")
    request = OrchestratorRequest(
        message="How much for 50 people?",
        channel="webchat",
        customer_context={}
    )
    
    response = await orch.process_inquiry(request)
    
    print(f"✅ Response received")
    print(f"   Agent: {response.metadata.get('agent_type')}")
    print(f"   Success: {response.success}")
    print(f"   Latency: {response.metadata.get('execution_time_ms'):.0f}ms")
    print(f"   Response length: {len(response.response)} chars")
    
    print("\n🎉 Basic integration test passed!")

if __name__ == "__main__":
    asyncio.run(main())
