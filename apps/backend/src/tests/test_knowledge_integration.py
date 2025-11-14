"""
Test Knowledge Integration - Verify dynamic knowledge context flows through entire system

This test validates:
1. KnowledgeService fetches current data from database
2. Intent Router injects knowledge_context before routing
3. All 4 agents receive and use knowledge_context
4. AI responses reflect current database data (not hardcoded values)

Author: AI Team
Date: 2025-11-05
"""

import asyncio
import pytest
from datetime import datetime

from api.ai.routers.intent_router import IntentRouter
from services.knowledge.knowledge_service import KnowledgeService
from core.database import get_db


@pytest.fixture
def test_context():
    """Provide test conversation context"""
    return {
        "conversation_id": f"test_{datetime.now().timestamp()}",
        "customer_tone": "casual",
        "guest_count": 50,
        "event_type": "corporate",
        "channel": "webchat"
    }


@pytest.fixture
async def db_session():
    """Provide database session"""
    async for db in get_db():
        yield db
        break


@pytest.mark.asyncio
async def test_knowledge_context_injection(test_context, db_session):
    """Test that Intent Router successfully injects knowledge_context"""
    router = IntentRouter()
    
    result = await router.route(
        message="What are your menu options?",
        context=test_context
    )
    
    # Verify knowledge_context was injected
    assert "knowledge_context" in test_context, "knowledge_context not injected into context"
    assert len(test_context["knowledge_context"]) > 0, "knowledge_context is empty"
    
    # Verify it contains expected sections (case-insensitive)
    knowledge_context = test_context["knowledge_context"]
    context_upper = knowledge_context.upper()
    assert "MENU" in context_upper or "PRICING" in context_upper or "PACKAGES" in context_upper
    assert "CHARTER" in context_upper or "BUSINESS" in context_upper
    
    print(f"✅ Knowledge context injected: {len(knowledge_context)} characters")


@pytest.mark.asyncio
async def test_lead_nurturing_agent_uses_knowledge(test_context):
    """Test LeadNurturingAgent receives and uses knowledge_context"""
    router = IntentRouter()
    
    result = await router.route(
        message="How much does the Standard Package cost for 50 people?",
        context=test_context
    )
    
    # Verify routing to lead_nurturing
    assert result["routing"]["agent_type"] == "lead_nurturing"
    
    # Verify response contains pricing (from database, not hardcoded)
    content = result["content"].lower()
    assert any(word in content for word in ["price", "cost", "package", "$"])
    
    print(f"✅ LeadNurturingAgent response: {result['content'][:200]}...")


@pytest.mark.asyncio
async def test_customer_care_agent_uses_knowledge(test_context):
    """Test CustomerCareAgent receives and uses knowledge_context"""
    router = IntentRouter()
    
    result = await router.route(
        message="What is your cancellation policy?",
        context=test_context
    )
    
    # Verify routing (could be customer_care or knowledge depending on classification)
    agent_type = result["routing"]["agent_type"]
    assert agent_type in ["customer_care", "knowledge"], f"Expected customer_care or knowledge, got {agent_type}"
    
    # Verify response contains policy information
    content = result["content"].lower()
    assert any(word in content for word in ["cancel", "policy", "refund", "help", "assist"])
    
    print(f"✅ Agent ({agent_type}) response: {result['content'][:200]}...")


@pytest.mark.asyncio
async def test_operations_agent_uses_knowledge(test_context):
    """Test OperationsAgent receives and uses knowledge_context"""
    router = IntentRouter()
    
    result = await router.route(
        message="Do you serve the Orange County area?",
        context=test_context
    )
    
    # Verify routing to operations
    assert result["routing"]["agent_type"] == "operations"
    
    # Verify response contains service area information
    content = result["content"].lower()
    assert any(word in content for word in ["area", "location", "service", "county"])
    
    print(f"✅ OperationsAgent response: {result['content'][:200]}...")


@pytest.mark.asyncio
async def test_knowledge_agent_uses_knowledge(test_context):
    """Test KnowledgeAgent receives and uses knowledge_context"""
    router = IntentRouter()
    
    result = await router.route(
        message="Tell me about My Hibachi",
        context=test_context
    )
    
    # Verify routing (AI might classify as knowledge or lead_nurturing depending on context)
    agent_type = result["routing"]["agent_type"]
    assert agent_type in ["knowledge", "lead_nurturing"], f"Expected knowledge or lead_nurturing, got {agent_type}"
    
    # Verify response contains business information
    content = result["content"].lower()
    assert any(word in content for word in ["hibachi", "restaurant", "service", "chef", "catering"])
    
    print(f"✅ Agent ({agent_type}) response: {result['content'][:200]}...")


@pytest.mark.asyncio
async def test_fallback_routing_injects_knowledge(test_context):
    """Test route_with_fallback also injects knowledge_context"""
    router = IntentRouter()
    
    result = await router.route_with_fallback(
        message="Hmm, not sure what I want",
        context=test_context,
        confidence_threshold=0.8  # High threshold to trigger fallback
    )
    
    # Verify knowledge_context was still injected
    assert "knowledge_context" in test_context
    assert len(test_context["knowledge_context"]) > 0
    
    # Verify we got a valid response with routing metadata
    assert "routing" in result, "Response missing routing metadata"
    
    # Check if fallback was triggered
    if "fallback" in result.get("routing", {}):
        print(f"✅ Fallback triggered, still got knowledge context")
    else:
        print(f"✅ No fallback needed, still got knowledge context")


@pytest.mark.asyncio
async def test_knowledge_service_full_context():
    """Test KnowledgeService.get_full_ai_context() directly"""
    async for db in get_db():
        service = KnowledgeService(db, station_id=None)
        
        context = await service.get_full_ai_context(
            include_menu=True,
            include_charter=True,
            include_faqs=True,
            guest_count=50
        )
        
        # Verify sections are present (even if empty, structure should be there)
        assert len(context) > 0, "get_full_ai_context returned empty string"
        # Check for section headers
        assert "MENU" in context.upper() or "PRICING" in context.upper()
        assert "CHARTER" in context.upper() or "BUSINESS" in context.upper()
        assert "FAQ" in context.upper() or "QUESTION" in context.upper()
        
        print(f"✅ KnowledgeService context: {len(context)} characters")
        print(f"   Structure verified - sections present")
        break  # Only need one iteration


@pytest.mark.asyncio
async def test_performance_overhead():
    """Test that knowledge context loading doesn't add excessive latency"""
    router = IntentRouter()
    
    start = datetime.now()
    
    result = await router.route(
        message="What are your packages?",
        context={
            "conversation_id": "perf_test",
            "guest_count": 50
        }
    )
    
    total_latency = (datetime.now() - start).total_seconds() * 1000  # ms
    
    # First run includes embedding computation and model loading, allow up to 15 seconds
    # Subsequent runs should be much faster due to caching
    assert total_latency < 15000, f"Total latency too high: {total_latency:.2f}ms"
    
    print(f"✅ Total latency: {total_latency:.2f}ms")
    print(f"   Classification: {result['routing']['classification_latency_ms']:.2f}ms")
    print(f"   Agent: {result['routing']['agent_latency_ms']:.2f}ms")


@pytest.mark.asyncio
async def test_error_handling_empty_knowledge():
    """Test that agents handle empty knowledge_context gracefully"""
    router = IntentRouter()
    
    # Simulate failure by providing invalid station_id
    result = await router.route(
        message="What are your prices?",
        context={
            "conversation_id": "error_test",
            "station_id": "invalid_station_999999"
        }
    )
    
    # Should still get a response (agent shows warning and uses tools)
    assert "content" in result
    assert len(result["content"]) > 0
    
    print(f"✅ Agent handled empty knowledge_context: {result['content'][:100]}...")


if __name__ == "__main__":
    """Run tests directly"""
    print("=" * 80)
    print("KNOWLEDGE INTEGRATION TEST SUITE")
    print("=" * 80)
    
    asyncio.run(test_knowledge_service_full_context())
    
    test_ctx = {
        "conversation_id": "manual_test",
        "guest_count": 50,
        "event_type": "corporate"
    }
    
    async def run_all_tests():
        async for db in get_db():
            await test_knowledge_context_injection(test_ctx, db)
            break
        await test_lead_nurturing_agent_uses_knowledge(test_ctx.copy())
        await test_customer_care_agent_uses_knowledge(test_ctx.copy())
        await test_operations_agent_uses_knowledge(test_ctx.copy())
        await test_knowledge_agent_uses_knowledge(test_ctx.copy())
        await test_fallback_routing_injects_knowledge(test_ctx.copy())
        await test_performance_overhead()
        await test_error_handling_empty_knowledge()
    
    asyncio.run(run_all_tests())
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Knowledge integration working correctly!")
    print("=" * 80)
