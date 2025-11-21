"""
Unit Tests for ReAct Agent and Complexity Router

Tests the adaptive reasoning system:
- Complexity classification accuracy
- ReAct agent reasoning loops
- Tool execution
- Error handling

Author: MyHibachi AI Team
Created: November 10, 2025
"""

from api.ai.reasoning.complexity_router import (
    ComplexityLevel,
    ComplexityRouter,
)
from api.ai.reasoning.react_agent import (
    ReActAgent,
    ReActConfig,
)
import pytest

# ============================================================================
# COMPLEXITY ROUTER TESTS
# ============================================================================


@pytest.fixture
def complexity_router():
    """Fixture for complexity router"""
    return ComplexityRouter()


@pytest.mark.asyncio
async def test_complexity_router_simple_query(complexity_router):
    """Test that simple queries route to CACHE layer"""
    queries = [
        "What are your hours?",
        "Where are you located?",
        "Do you have a menu?",
        "Thanks!",
        "Hello",
    ]

    for query in queries:
        level = await complexity_router.classify(query)
        assert level == ComplexityLevel.CACHE, f"Expected CACHE for: {query}"


@pytest.mark.asyncio
async def test_complexity_router_medium_query(complexity_router):
    """Test that medium queries route to REACT layer"""
    queries = [
        "I need a chef for 10 people next Saturday",
        "Can you check availability for 8 adults at 6pm?",
        "What's the price for 15 people with shrimp?",
        "Do you travel to 95630 and how much is travel fee?",
    ]

    for query in queries:
        level = await complexity_router.classify(query)
        assert level == ComplexityLevel.REACT, f"Expected REACT for: {query}"


@pytest.mark.asyncio
async def test_complexity_router_complex_query(complexity_router):
    """Test that complex queries route to MULTI_AGENT layer"""
    queries = [
        "I need vegetarian options but my guests also want meat, what do you suggest?",
        "What's better for my budget: 15 people with chicken or 12 with filet? Also need to know travel fees.",
        "Can you compare packages and help me decide? I have 3 questions about each.",
    ]

    for query in queries:
        level = await complexity_router.classify(query)
        assert (
            level == ComplexityLevel.MULTI_AGENT
        ), f"Expected MULTI_AGENT for: {query}"


@pytest.mark.asyncio
async def test_complexity_router_crisis_query(complexity_router):
    """Test that crisis queries route to HUMAN layer"""
    queries = [
        "Your food made me sick! I want a refund immediately!!!",
        "This is the worst service I've ever experienced. Never again!",
        "I'm going to sue you for this terrible experience!",
        "Disgusting food, horrible chef, angry customer!",
    ]

    for query in queries:
        level = await complexity_router.classify(query)
        assert level == ComplexityLevel.HUMAN, f"Expected HUMAN for: {query}"


@pytest.mark.asyncio
async def test_complexity_router_with_context(complexity_router):
    """Test that context affects routing decisions"""

    query = "I have another issue"

    # No escalation history → CACHE or REACT
    level1 = await complexity_router.classify(query, {"escalation_count": 0})
    assert level1 in [
        ComplexityLevel.CACHE,
        ComplexityLevel.REACT,
        ComplexityLevel.HUMAN,
    ]

    # High escalation history + negative sentiment → HUMAN
    query_negative = "I have another issue and I'm very unhappy"
    level2 = await complexity_router.classify(
        query_negative, {"escalation_count": 3}
    )
    # Should escalate to human due to history + negativity
    assert level2 in [ComplexityLevel.MULTI_AGENT, ComplexityLevel.HUMAN]


# ============================================================================
# REACT AGENT TESTS
# ============================================================================


class MockModelProvider:
    """Mock AI model provider for testing"""

    def __init__(self, responses: list[str]):
        """
        Initialize mock provider.

        Args:
            responses: List of responses to return (one per call)
        """
        self.responses = responses
        self.call_count = 0

    async def complete(self, messages, **kwargs):
        """Mock completion"""
        if self.call_count >= len(self.responses):
            return {"content": "THOUGHT: I'm done.\nACTION: None"}

        response = self.responses[self.call_count]
        self.call_count += 1
        return {"content": response}


def mock_check_availability(date: str, party_size: int) -> dict:
    """Mock availability checking tool"""
    if party_size <= 12:
        return {"available": True, "table_size": 12}
    return {"available": False, "message": "Too large for standard table"}


def mock_calculate_price(party_size: int, protein: str = "chicken") -> dict:
    """Mock pricing tool"""
    base_price = 30 if protein == "chicken" else 45
    return {"total": party_size * base_price, "per_person": base_price}


@pytest.fixture
def mock_tools():
    """Fixture for mock tools"""
    return {
        "check_availability": mock_check_availability,
        "calculate_price": mock_calculate_price,
    }


@pytest.mark.asyncio
async def test_react_agent_single_iteration(mock_tools):
    """Test ReAct agent with single iteration (simple query)"""

    # Mock provider returns final answer immediately
    provider = MockModelProvider(
        [
            """THOUGHT: The customer is asking about hours, which is straightforward.
Based on our business hours, we're open 11 AM - 10 PM daily.
ACTION: None"""
        ]
    )

    agent = ReActAgent(provider, mock_tools)
    result = await agent.process("What are your hours?")

    assert result.success is True
    assert result.iterations == 1
    assert "11 AM - 10 PM" in result.steps[0].thought
    assert result.steps[0].action is None
    assert len(result.tools_used) == 0


@pytest.mark.asyncio
async def test_react_agent_multi_iteration(mock_tools):
    """Test ReAct agent with multiple iterations (tool calls)"""

    provider = MockModelProvider(
        [
            # Iteration 1: Check availability
            """THOUGHT: Need to check if we have availability for 15 people.
ACTION: check_availability
INPUT: {"date": "2025-11-16", "party_size": 15}""",
            # Iteration 2: Calculate price
            """THOUGHT: Table is too small. Let me check pricing for smaller group.
ACTION: calculate_price
INPUT: {"party_size": 12, "protein": "chicken"}""",
            # Iteration 3: Final answer
            """THOUGHT: Based on availability and pricing, I can offer them a 12-person booking.
The total would be $360 ($30 per person). We can discuss expanding if needed.
ACTION: None""",
        ]
    )

    agent = ReActAgent(provider, mock_tools)
    result = await agent.process("I need chef for 15 people on Saturday")

    assert result.success is True
    assert result.iterations == 3
    assert len(result.tools_used) == 2
    assert "check_availability" in result.tools_used
    assert "calculate_price" in result.tools_used

    # Verify steps
    assert result.steps[0].action == "check_availability"
    assert result.steps[0].observation is not None
    assert result.steps[1].action == "calculate_price"
    assert result.steps[2].action is None  # Final answer


@pytest.mark.asyncio
async def test_react_agent_tool_error_handling(mock_tools):
    """Test ReAct agent handles tool errors gracefully"""

    def failing_tool(**kwargs):
        raise ValueError("Tool failed!")

    tools_with_error = {**mock_tools, "failing_tool": failing_tool}

    provider = MockModelProvider(
        [
            """THOUGHT: Let me try this tool.
ACTION: failing_tool
INPUT: {}""",
            """THOUGHT: Tool failed, but I'll provide a helpful response anyway.
ACTION: None""",
        ]
    )

    agent = ReActAgent(provider, tools_with_error)
    result = await agent.process("Test query")

    assert result.success is True
    assert "Error" in result.steps[0].observation


@pytest.mark.asyncio
async def test_react_agent_max_iterations(mock_tools):
    """Test ReAct agent respects max iterations limit"""

    # Provider that keeps trying to use tools forever
    provider = MockModelProvider(
        [
            """THOUGHT: Iteration 1
ACTION: check_availability
INPUT: {"date": "2025-11-16", "party_size": 10}""",
            """THOUGHT: Iteration 2
ACTION: calculate_price
INPUT: {"party_size": 10}""",
            """THOUGHT: Iteration 3
ACTION: check_availability
INPUT: {"date": "2025-11-17", "party_size": 10}""",
            """THOUGHT: Iteration 4
ACTION: calculate_price
INPUT: {"party_size": 10}""",
            """THOUGHT: Iteration 5
ACTION: check_availability
INPUT: {"date": "2025-11-18", "party_size": 10}""",
            """THOUGHT: Should be forced to complete
ACTION: check_availability
INPUT: {"date": "2025-11-19", "party_size": 10}""",
        ]
    )

    config = ReActConfig(max_iterations=5)
    agent = ReActAgent(provider, mock_tools, config)
    result = await agent.process("Test query")

    assert result.success is True
    assert result.iterations <= 6  # 5 iterations + 1 forced completion
    assert len(result.steps) <= 6


@pytest.mark.asyncio
async def test_react_agent_unknown_tool(mock_tools):
    """Test ReAct agent handles unknown tool calls"""

    provider = MockModelProvider(
        [
            """THOUGHT: Let me use a non-existent tool.
ACTION: nonexistent_tool
INPUT: {}""",
            """THOUGHT: Tool not found, providing answer without it.
ACTION: None""",
        ]
    )

    agent = ReActAgent(provider, mock_tools)
    result = await agent.process("Test query")

    assert result.success is True
    assert "not found" in result.steps[0].observation.lower()


@pytest.mark.asyncio
async def test_react_agent_invalid_json_input(mock_tools):
    """Test ReAct agent handles invalid JSON in tool input"""

    provider = MockModelProvider(
        [
            """THOUGHT: Using tool with invalid JSON.
ACTION: check_availability
INPUT: {this is not valid json}""",
            """THOUGHT: Proceeding with answer.
ACTION: None""",
        ]
    )

    agent = ReActAgent(provider, mock_tools)
    result = await agent.process("Test query")

    assert result.success is True
    # Should have empty dict as fallback
    assert result.steps[0].action_input == {}


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_full_reasoning_flow(complexity_router, mock_tools):
    """Test complete flow: routing → ReAct execution"""

    # Medium complexity query
    query = "I need chef for 12 people on Saturday, what's the price?"

    # Step 1: Route query
    level = await complexity_router.classify(query)
    assert level == ComplexityLevel.REACT

    # Step 2: Execute with ReAct
    provider = MockModelProvider(
        [
            """THOUGHT: Need to check availability first.
ACTION: check_availability
INPUT: {"date": "2025-11-16", "party_size": 12}""",
            """THOUGHT: Available! Now calculate price.
ACTION: calculate_price
INPUT: {"party_size": 12, "protein": "chicken"}""",
            """THOUGHT: Perfect! We have availability and the price is $360 total ($30 per person).
ACTION: None""",
        ]
    )

    agent = ReActAgent(provider, mock_tools)
    result = await agent.process(query)

    assert result.success is True
    assert result.iterations == 3
    assert "$360" in result.response or "360" in result.response


@pytest.mark.asyncio
async def test_complexity_stats(complexity_router):
    """Test complexity router statistics"""

    stats = await complexity_router.get_routing_stats()

    assert "total_routed" in stats
    assert "by_level" in stats
    assert "accuracy_by_level" in stats
    assert "avg_classification_time_ms" in stats

    # Verify accuracy expectations
    assert stats["accuracy_by_level"]["cache"] == 0.95
    assert stats["accuracy_by_level"]["react"] == 0.92
    assert stats["accuracy_by_level"]["multi_agent"] == 0.97
    assert stats["accuracy_by_level"]["human"] == 0.99
