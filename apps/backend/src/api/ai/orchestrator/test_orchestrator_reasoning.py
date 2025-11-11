"""
Integration tests for AIOrchestrator with adaptive reasoning.

Tests the integration between ComplexityRouter, ReActAgent, and AIOrchestrator.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from .ai_orchestrator import AIOrchestrator
from .schemas import OrchestratorRequest, OrchestratorConfig
from ..reasoning import ComplexityLevel


@pytest.fixture
def mock_model_provider():
    """Mock model provider for testing"""
    provider = MagicMock()
    provider.complete = AsyncMock(return_value="Test response")
    return provider


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry for testing"""
    registry = MagicMock()
    registry.list_tools = MagicMock(return_value=["check_availability", "calculate_price"])
    registry.get_tool = MagicMock()
    return registry


@pytest.fixture
def orchestrator_with_reasoning(mock_model_provider, mock_tool_registry):
    """Create orchestrator instance with reasoning enabled"""
    config = OrchestratorConfig(
        model="gpt-4o-mini",
        auto_admin_review=False,
    )
    
    # Mock the router to avoid initialization issues
    mock_router = MagicMock()
    mock_router.agents = {"lead_nurturing": MagicMock(tool_registry=mock_tool_registry)}
    
    orchestrator = AIOrchestrator(
        config=config,
        use_router=True,
        router=mock_router,
        provider=mock_model_provider,
        enable_reasoning=True,
    )
    
    return orchestrator


@pytest.mark.asyncio
async def test_orchestrator_initializes_with_reasoning(orchestrator_with_reasoning):
    """Test that orchestrator initializes with reasoning layers"""
    assert orchestrator_with_reasoning.enable_reasoning is True
    assert orchestrator_with_reasoning.complexity_router is not None
    # react_agent is lazy-initialized, so it should be None at start
    assert orchestrator_with_reasoning.react_agent is None


@pytest.mark.asyncio
async def test_simple_query_uses_standard_routing(orchestrator_with_reasoning):
    """Test that simple queries use standard routing (CACHE level)"""
    request = OrchestratorRequest(
        message="What time do you open?",
        channel="email",
        customer_context={"email": "test@example.com"},
    )
    
    with patch.object(
        orchestrator_with_reasoning, "_process_with_router_or_legacy"
    ) as mock_router:
        mock_router.return_value = MagicMock(
            success=True,
            response="We're open 24/7!",
            metadata={},
        )
        
        response = await orchestrator_with_reasoning.process_inquiry(request)
        
        # Should have routed to standard processing
        mock_router.assert_called_once()
        assert "complexity_level" in response.metadata
        assert response.metadata["complexity_level"] == "CACHE"


@pytest.mark.asyncio
async def test_medium_query_uses_react(orchestrator_with_reasoning):
    """Test that medium complexity queries use ReAct agent"""
    request = OrchestratorRequest(
        message="I need a chef for 10 people next Saturday",
        channel="email",
        customer_context={"email": "test@example.com"},
    )
    
    with patch.object(orchestrator_with_reasoning, "_process_with_react") as mock_react:
        mock_react.return_value = MagicMock(
            success=True,
            response="I can help you with that!",
            metadata={"reasoning_iterations": 2},
        )
        
        response = await orchestrator_with_reasoning.process_inquiry(request)
        
        # Should have routed to ReAct
        mock_react.assert_called_once()
        assert "complexity_level" in response.metadata
        assert response.metadata["complexity_level"] == "REACT"


@pytest.mark.asyncio
async def test_complex_query_falls_back_to_router(orchestrator_with_reasoning):
    """Test that complex queries fall back to router (multi-agent not yet implemented)"""
    request = OrchestratorRequest(
        message="I need vegetarian options but my guests also want meat, what do you suggest?",
        channel="email",
        customer_context={"email": "test@example.com"},
    )
    
    with patch.object(
        orchestrator_with_reasoning, "_process_with_router_or_legacy"
    ) as mock_router:
        mock_router.return_value = MagicMock(
            success=True,
            response="We can accommodate both!",
            metadata={},
        )
        
        response = await orchestrator_with_reasoning.process_inquiry(request)
        
        # Should have fallen back to standard routing (multi-agent not implemented yet)
        mock_router.assert_called()
        assert "complexity_level" in response.metadata
        assert response.metadata["complexity_level"] == "MULTI_AGENT"


@pytest.mark.asyncio
async def test_crisis_query_falls_back_to_router(orchestrator_with_reasoning):
    """Test that crisis queries fall back to router (human escalation not yet implemented)"""
    request = OrchestratorRequest(
        message="I'm extremely angry! This is the worst service ever!!!",
        channel="email",
        customer_context={"email": "test@example.com"},
    )
    
    with patch.object(
        orchestrator_with_reasoning, "_process_with_router_or_legacy"
    ) as mock_router:
        mock_router.return_value = MagicMock(
            success=True,
            response="I apologize for the inconvenience...",
            metadata={},
        )
        
        response = await orchestrator_with_reasoning.process_inquiry(request)
        
        # Should have fallen back to standard routing
        mock_router.assert_called()
        assert "complexity_level" in response.metadata
        assert response.metadata["complexity_level"] == "HUMAN"


@pytest.mark.asyncio
async def test_reasoning_disabled_uses_standard_routing(mock_model_provider, mock_tool_registry):
    """Test that disabling reasoning uses standard routing"""
    config = OrchestratorConfig(model="gpt-4o-mini")
    
    mock_router = MagicMock()
    mock_router.agents = {"lead_nurturing": MagicMock(tool_registry=mock_tool_registry)}
    
    orchestrator = AIOrchestrator(
        config=config,
        use_router=True,
        router=mock_router,
        provider=mock_model_provider,
        enable_reasoning=False,  # Disabled
    )
    
    assert orchestrator.enable_reasoning is False
    assert orchestrator.complexity_router is None
    
    request = OrchestratorRequest(
        message="I need a chef for 10 people next Saturday",
        channel="email",
        customer_context={"email": "test@example.com"},
    )
    
    with patch.object(orchestrator, "_process_with_router_or_legacy") as mock_router_call:
        mock_router_call.return_value = MagicMock(
            success=True,
            response="Sure!",
            metadata={},
        )
        
        response = await orchestrator.process_inquiry(request)
        
        # Should use standard routing, no complexity metadata
        mock_router_call.assert_called_once()
        assert "complexity_level" not in response.metadata


@pytest.mark.asyncio
async def test_reasoning_error_falls_back_gracefully(orchestrator_with_reasoning):
    """Test that reasoning errors fall back to standard routing"""
    request = OrchestratorRequest(
        message="Test query",
        channel="email",
        customer_context={"email": "test@example.com"},
    )
    
    # Make complexity router raise an error
    with patch.object(
        orchestrator_with_reasoning.complexity_router, "classify", side_effect=Exception("Test error")
    ):
        with patch.object(
            orchestrator_with_reasoning, "_process_with_router_or_legacy"
        ) as mock_router:
            mock_router.return_value = MagicMock(
                success=True,
                response="Response",
                metadata={},
            )
            
            response = await orchestrator_with_reasoning.process_inquiry(request)
            
            # Should have fallen back gracefully
            mock_router.assert_called_once()
            assert response.success is True


@pytest.mark.asyncio
async def test_react_agent_lazy_initialization(orchestrator_with_reasoning):
    """Test that ReAct agent is initialized on first use"""
    assert orchestrator_with_reasoning.react_agent is None
    
    request = OrchestratorRequest(
        message="I need a chef for 10 people next Saturday",
        channel="email",
        customer_context={"email": "test@example.com"},
    )
    
    # Mock the ReAct agent processing
    with patch("api.ai.orchestrator.ai_orchestrator.ReActAgent") as MockReActAgent:
        mock_agent = AsyncMock()
        mock_agent.process = AsyncMock(return_value=MagicMock(
            success=True,
            response="Test response",
            tools_used=[],
            iterations=1,
            cost_usd=0.001,
            duration_ms=500,
            steps=[],
        ))
        MockReActAgent.return_value = mock_agent
        
        # This should trigger ReAct (medium complexity)
        with patch.object(
            orchestrator_with_reasoning.complexity_router, "classify"
        ) as mock_classify:
            mock_classify.return_value = ComplexityLevel.REACT
            
            response = await orchestrator_with_reasoning.process_inquiry(request)
            
            # ReAct agent should have been initialized
            MockReActAgent.assert_called_once()
            mock_agent.process.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
