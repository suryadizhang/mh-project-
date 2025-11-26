"""
Integration Tests for Phase 1A Multi-Agent System

Tests the full integration of:
- Intent Router
- 4 Specialized Agents
- Model Provider
- AI Orchestrator

Run with:
    cd apps/backend
    $env:PYTHONPATH="$PWD/src"
    python src/api/ai/tests/test_integration.py
"""

import asyncio
from datetime import datetime, timezone
import logging

from api.ai.orchestrator import AIOrchestrator, OrchestratorRequest
from api.ai.routers import get_intent_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class IntegrationTestSuite:
    """Comprehensive integration test suite for Phase 1A"""

    def __init__(self):
        self.orchestrator = AIOrchestrator(use_router=True)
        self.router = get_intent_router()
        self.passed = 0
        self.failed = 0
        self.results: list[dict] = []

    async def test_lead_nurturing_agent(self):
        """Test 1: Lead Nurturing Agent - Sales inquiries"""

        test_cases = [
            {
                "name": "Pricing inquiry",
                "message": "How much for 50 people?",
                "expected_agent": "lead_nurturing",
                "should_use_tools": True,
            },
            {
                "name": "Package inquiry",
                "message": "What packages do you offer?",
                "expected_agent": "lead_nurturing",
                "should_use_tools": False,
            },
            {
                "name": "Upselling opportunity",
                "message": "I want Standard package but tell me about Premium",
                "expected_agent": "lead_nurturing",
                "should_use_tools": True,
            },
        ]

        for test_case in test_cases:
            await self._run_test_case("Lead Nurturing", test_case)

    async def test_customer_care_agent(self):
        """Test 2: Customer Care Agent - Support issues"""

        test_cases = [
            {
                "name": "Order status inquiry",
                "message": "Where is my order ORD-2024-1234?",
                "expected_agent": "customer_care",
                "should_use_tools": True,
            },
            {
                "name": "Complaint",
                "message": "The chef was 30 minutes late to my event!",
                "expected_agent": "customer_care",
                "should_use_tools": True,
            },
            {
                "name": "Refund request",
                "message": "I want a refund for my booking",
                "expected_agent": "customer_care",
                "should_use_tools": True,
            },
        ]

        for test_case in test_cases:
            await self._run_test_case("Customer Care", test_case)

    async def test_operations_agent(self):
        """Test 3: Operations Agent - Logistics"""

        test_cases = [
            {
                "name": "Availability check",
                "message": "Are you available on December 20th for 60 people?",
                "expected_agent": "operations",
                "should_use_tools": True,
            },
            {
                "name": "Booking modification",
                "message": "I need to change my booking date",
                "expected_agent": "operations",
                "should_use_tools": True,
            },
            {
                "name": "Chef request",
                "message": "Can I request a chef who specializes in vegetarian?",
                "expected_agent": "operations",
                "should_use_tools": False,
            },
        ]

        for test_case in test_cases:
            await self._run_test_case("Operations", test_case)

    async def test_knowledge_agent(self):
        """Test 4: Knowledge Agent - Policies & FAQs"""

        test_cases = [
            {
                "name": "Policy inquiry",
                "message": "What's your cancellation policy?",
                "expected_agent": "knowledge",
                "should_use_tools": True,
            },
            {
                "name": "FAQ question",
                "message": "How far in advance should I book?",
                "expected_agent": "knowledge",
                "should_use_tools": True,
            },
            {
                "name": "Menu inquiry",
                "message": "What dietary restrictions do you accommodate?",
                "expected_agent": "knowledge",
                "should_use_tools": True,
            },
        ]

        for test_case in test_cases:
            await self._run_test_case("Knowledge", test_case)

    async def test_multi_turn_conversation(self):
        """Test 5: Multi-turn conversation with context"""

        conversation_id = f"test_conv_{datetime.now(timezone.utc).timestamp()}"

        turns = [
            {
                "message": "I'm interested in catering for 60 people",
                "expected_agent": "lead_nurturing",
                "turn": 1,
            },
            {
                "message": "What's included in the Premium package?",
                "expected_agent": "lead_nurturing",
                "turn": 2,
            },
            {
                "message": "Actually, what's your cancellation policy?",
                "expected_agent": "knowledge",
                "turn": 3,
            },
            {
                "message": "Okay, are you available December 15th?",
                "expected_agent": "operations",
                "turn": 4,
            },
        ]

        for turn_data in turns:
            request = OrchestratorRequest(
                message=turn_data["message"],
                channel="webchat",
                conversation_id=conversation_id,
                customer_context={"email": "test@example.com"},
            )

            start_time = datetime.now(timezone.utc)
            response = await self.orchestrator.process_inquiry(request)
            latency = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            agent_type = response.metadata.get("agent_type")
            success = agent_type == turn_data["expected_agent"]

            if success:
                self.passed += 1
            else:
                self.failed += 1

            self.results.append(
                {
                    "test": f"Multi-Turn Turn {turn_data['turn']}",
                    "passed": success,
                    "latency_ms": latency,
                    "agent": agent_type,
                }
            )

    async def test_intent_transitions(self):
        """Test 6: Intent transitions (switching agents mid-conversation)"""

        conversation_id = (
            f"test_transition_{datetime.now(timezone.utc).timestamp()}"
        )

        transitions = [
            {
                "from_msg": "How much for 80 people?",
                "from_agent": "lead_nurturing",
                "to_msg": "The chef was late to my last event",
                "to_agent": "customer_care",
            },
            {
                "from_msg": "I want a refund",
                "from_agent": "customer_care",
                "to_msg": "Can I reschedule instead?",
                "to_agent": "operations",
            },
        ]

        for i, transition in enumerate(transitions, 1):

            # First message
            request1 = OrchestratorRequest(
                message=transition["from_msg"],
                channel="webchat",
                conversation_id=conversation_id,
                customer_context={},
            )
            response1 = await self.orchestrator.process_inquiry(request1)
            agent1 = response1.metadata.get("agent_type")

            # Second message
            request2 = OrchestratorRequest(
                message=transition["to_msg"],
                channel="webchat",
                conversation_id=conversation_id,
                customer_context={},
            )
            response2 = await self.orchestrator.process_inquiry(request2)
            agent2 = response2.metadata.get("agent_type")
            intent_transition = response2.metadata.get("intent_transition")

            success = (
                agent1 == transition["from_agent"]
                and agent2 == transition["to_agent"]
                and intent_transition == transition["from_agent"]
            )

            if success:
                self.passed += 1
            else:
                self.failed += 1

            self.results.append(
                {
                    "test": f"Intent Transition {i}",
                    "passed": success,
                    "from_agent": agent1,
                    "to_agent": agent2,
                }
            )

    async def test_fallback_handling(self):
        """Test 7: Fallback to Knowledge Agent for ambiguous intents"""

        ambiguous_messages = ["Hello", "Help", "I'm not sure", "What?"]

        for message in ambiguous_messages:
            # Use router's fallback method
            response = await self.router.route_with_fallback(
                message=message,
                context={
                    "conversation_id": f"test_fallback_{datetime.now(timezone.utc).timestamp()}"
                },
                confidence_threshold=0.65,
            )

            routing = response.get("routing", {})
            fallback = routing.get("fallback")
            agent_type = routing.get("agent_type")

            # Should route to knowledge agent or have low confidence
            success = agent_type == "knowledge" or (
                fallback and fallback.get("triggered")
            )

            if success:
                self.passed += 1
            else:
                self.failed += 1

            self.results.append(
                {
                    "test": f"Fallback: {message}",
                    "passed": success,
                    "agent": agent_type,
                    "fallback": (
                        fallback.get("triggered") if fallback else False
                    ),
                }
            )

    async def test_tool_calling(self):
        """Test 8: Tool calling through agents"""

        tool_test_cases = [
            {
                "message": "Can you recommend a package for 60 guests with a $4000 budget?",
                "expected_agent": "lead_nurturing",
                "should_have_tools": True,
                "expected_tool": "get_product_recommendations",
            },
            {
                "message": "Check status of order ORD-2024-5678",
                "expected_agent": "customer_care",
                "should_have_tools": True,
                "expected_tool": "check_order_status",
            },
            {
                "message": "Are you available on December 25th for 100 people?",
                "expected_agent": "operations",
                "should_have_tools": True,
                "expected_tool": "check_availability",
            },
        ]

        for test_case in tool_test_cases:
            request = OrchestratorRequest(
                message=test_case["message"],
                channel="webchat",
                conversation_id=f"test_tools_{datetime.now(timezone.utc).timestamp()}",
                customer_context={},
            )

            response = await self.orchestrator.process_inquiry(request)

            agent_type = response.metadata.get("agent_type")
            tools_used = response.tools_used

            # Check if tools were called
            has_tools = len(tools_used) > 0
            correct_agent = agent_type == test_case["expected_agent"]

            success = correct_agent and (
                has_tools == test_case["should_have_tools"]
            )

            if tools_used:
                pass

            if success:
                self.passed += 1
            else:
                self.failed += 1

            self.results.append(
                {
                    "test": f"Tool Calling: {test_case['expected_agent']}",
                    "passed": success,
                    "agent": agent_type,
                    "tools_count": len(tools_used),
                }
            )

    async def test_performance(self):
        """Test 9: Performance under concurrent load"""

        messages = [
            "How much for 50 people?",
            "What's your cancellation policy?",
            "Are you available Saturday?",
            "I want a refund",
            "What packages do you offer?",
            "Can I reschedule my booking?",
            "Where is my order?",
            "What dietary options do you have?",
            "I need a quote for 100 guests",
            "The chef was late",
        ]

        # Run concurrent requests
        start_time = datetime.now(timezone.utc)

        tasks = []
        for i, message in enumerate(messages):
            request = OrchestratorRequest(
                message=message,
                channel="webchat",
                conversation_id=f"perf_test_{i}",
                customer_context={},
            )
            tasks.append(self.orchestrator.process_inquiry(request))

        responses = await asyncio.gather(*tasks)

        total_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        avg_latency = sum(
            r.metadata.get("execution_time_ms", 0) for r in responses
        ) / len(responses)

        # All should succeed
        success = all(r.success for r in responses)

        if success:
            self.passed += 1
        else:
            self.failed += 1

        self.results.append(
            {
                "test": "Performance (Concurrent)",
                "passed": success,
                "total_time_s": total_time,
                "avg_latency_ms": avg_latency,
                "throughput": len(messages) / total_time,
            }
        )

    async def _run_test_case(self, agent_name: str, test_case: dict):
        """Helper to run a single test case"""
        request = OrchestratorRequest(
            message=test_case["message"],
            channel="webchat",
            conversation_id=f"test_{agent_name}_{datetime.now(timezone.utc).timestamp()}",
            customer_context={"email": "test@example.com"},
        )

        start_time = datetime.now(timezone.utc)
        response = await self.orchestrator.process_inquiry(request)
        latency = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() * 1000

        agent_type = response.metadata.get("agent_type")
        tools_used = len(response.tools_used)
        confidence = response.metadata.get("routing_confidence")

        # Check if correct agent
        agent_match = agent_type == test_case["expected_agent"]

        # Check if tools were used as expected
        tools_match = (tools_used > 0) == test_case.get(
            "should_use_tools", False
        )

        success = agent_match and tools_match

        if success:
            self.passed += 1
        else:
            self.failed += 1

        self.results.append(
            {
                "test": f"{agent_name}: {test_case['name']}",
                "passed": success,
                "latency_ms": latency,
                "agent": agent_type,
                "confidence": confidence,
                "tools": tools_used,
            }
        )

    def print_summary(self):
        """Print test summary"""

        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        # Calculate average latency
        latencies = [
            r.get("latency_ms") for r in self.results if r.get("latency_ms")
        ]
        if latencies:
            sum(latencies) / len(latencies)

        # Show failed tests
        failed_tests = [r for r in self.results if not r["passed"]]
        if failed_tests:
            for _test in failed_tests:
                pass

        if pass_rate == 100 or pass_rate >= 80:
            pass
        else:
            pass


async def main():
    """Run all integration tests"""

    suite = IntegrationTestSuite()

    try:
        # Run all tests
        await suite.test_lead_nurturing_agent()
        await suite.test_customer_care_agent()
        await suite.test_operations_agent()
        await suite.test_knowledge_agent()
        await suite.test_multi_turn_conversation()
        await suite.test_intent_transitions()
        await suite.test_fallback_handling()
        await suite.test_tool_calling()
        await suite.test_performance()

        # Print summary
        suite.print_summary()

    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
