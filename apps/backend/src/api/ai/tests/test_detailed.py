"""Test router and orchestrator integration with detailed logging"""
import asyncio
import logging

# Set up logging first
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    print("\n" + "="*80)
    print("TESTING PHASE 1A INTEGRATION")
    print("="*80)
    
    # Test 1: Import router
    print("\n[TEST 1] Importing Intent Router...")
    try:
        from api.ai.routers import get_intent_router
        router = get_intent_router()
        print("[PASS] Intent Router imported and initialized")
        print(f"   Router class: {router.__class__.__name__}")
    except Exception as e:
        print(f"[FAIL] Router import failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Import provider
    print("\n[TEST 2] Importing Model Provider...")
    try:
        from api.ai.orchestrator.providers import get_provider
        provider = get_provider()
        print("[PASS] Model Provider imported and initialized")
        print(f"   Provider class: {provider.__class__.__name__}")
    except Exception as e:
        print(f"[FAIL] Provider import failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: Import orchestrator
    print("\n[TEST 3] Importing Orchestrator...")
    try:
        from api.ai.orchestrator import AIOrchestrator
        orch = AIOrchestrator(use_router=True)
        print("[PASS] Orchestrator imported and initialized")
        stats = orch.get_statistics()
        print(f"   Mode: {stats['mode']}")
        print(f"   Phase: {stats['phase']}")
        print(f"   Router enabled: {orch.use_router}")
    except Exception as e:
        print(f"[FAIL] Orchestrator import failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 4: Simple classification
    print("\n[TEST 4] Testing Intent Classification...")
    try:
        agent_type, confidence = await router.classify_intent(
            "How much for 50 people?"
        )
        print(f"[PASS] Classification successful")
        print(f"   Agent: {agent_type.value}")
        print(f"   Confidence: {confidence:.2%}")
    except Exception as e:
        print(f"[FAIL] Classification failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Simple routing
    print("\n[TEST 5] Testing Router...")
    try:
        response = await router.route(
            message="What's your cancellation policy?",
            context={"conversation_id": "test_123"}
        )
        routing = response.get("routing", {})
        print(f"[PASS] Routing successful")
        print(f"   Agent: {routing.get('agent_type')}")
        print(f"   Confidence: {routing.get('confidence'):.2%}")
        print(f"   Response: {response['content'][:100]}...")
    except Exception as e:
        print(f"[FAIL] Routing failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 6: Full orchestrator integration
    print("\n[TEST 6] Testing Full Orchestrator...")
    try:
        from api.ai.orchestrator import OrchestratorRequest
        
        request = OrchestratorRequest(
            message="I'm interested in booking for 60 people",
            channel="webchat",
            customer_context={}
        )
        
        response = await orch.process_inquiry(request)
        print(f"[PASS] Orchestrator processing successful")
        print(f"   Success: {response.success}")
        print(f"   Agent: {response.metadata.get('agent_type')}")
        print(f"   Latency: {response.metadata.get('execution_time_ms'):.0f}ms")
        print(f"   Response: {response.response[:150]}...")
    except Exception as e:
        print(f"[FAIL] Orchestrator processing failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("INTEGRATION TESTS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
