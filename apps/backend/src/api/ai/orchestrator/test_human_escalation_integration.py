"""
Integration tests for Human Escalation (Layer 5) with AIOrchestrator.

Tests the full flow from complexity routing to human escalation context preparation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from .ai_orchestrator import AIOrchestrator
from .schemas import OrchestratorRequest, OrchestratorConfig


@pytest.fixture
def orchestrator_config():
    """Create orchestrator configuration"""
    return OrchestratorConfig(
        enable_routing=True,
        enable_reasoning=True,  # Enable adaptive reasoning
        enable_rag=False,
        enable_voice=False,
        enable_threading=False,
        enable_identity=False,
        enable_memory=False,
        enable_emotion=False,
        admin_review_enabled=False,
        cache_enabled=False,
    )


@pytest.fixture
def mock_model_provider():
    """Mock model provider for LLM calls"""
    provider = AsyncMock()
    provider.model_name = "gpt-4"
    
    # Mock sentiment analysis response
    sentiment_response = AsyncMock()
    sentiment_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"sentiment_level": -2, "explanation": "Customer is very angry and frustrated"}'
            )
        )
    ]
    
    # Mock summarization response
    summary_response = AsyncMock()
    summary_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""{
                    "key_topics": ["refund request", "poor service"],
                    "customer_requests": ["immediate refund", "speak to manager"],
                    "ai_responses": ["Tried to help", "Offered alternatives"],
                    "sentiment_trend": "increasingly negative",
                    "frustration_indicators": ["ALL CAPS", "repeated requests", "threats"]
                }"""
            )
        )
    ]
    
    # Mock recommendations response
    recommendations_response = AsyncMock()
    recommendations_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""{
                    "primary_action": "Immediately contact customer and offer full refund",
                    "alternative_actions": ["Offer partial refund with discount", "Schedule manager callback"],
                    "things_to_avoid": ["Don't make customer repeat their story", "Don't offer generic solutions"],
                    "relevant_policies": ["30-day money back guarantee", "Customer satisfaction policy"],
                    "suggested_response_template": "I sincerely apologize for your experience..."
                }"""
            )
        )
    ]
    
    # Configure mock to return different responses based on call order
    provider.chat.completions.create = AsyncMock(
        side_effect=[sentiment_response, summary_response, recommendations_response]
    )
    
    return provider


@pytest.fixture
async def orchestrator(orchestrator_config, mock_model_provider):
    """Create AIOrchestrator instance with mocked dependencies"""
    with patch('api.ai.orchestrator.ai_orchestrator.get_provider') as mock_get_provider:
        mock_get_provider.return_value = mock_model_provider
        
        orchestrator = AIOrchestrator(orchestrator_config)
        orchestrator.model_provider = mock_model_provider
        
        # Mock the tool registry
        orchestrator.tool_registry = MagicMock()
        orchestrator.tool_registry.list_tools.return_value = []
        
        yield orchestrator


class TestHumanEscalationIntegration:
    """Test human escalation integration with orchestrator"""
    
    @pytest.mark.asyncio
    async def test_crisis_query_routes_to_human_escalation(self, orchestrator, mock_model_provider):
        """Test that a crisis query is properly routed to human escalation"""
        # Create a crisis request
        request = OrchestratorRequest(
            message="THIS IS UNACCEPTABLE! I WANT MY MONEY BACK NOW!",
            channel="web",
            customer_context={
                "name": "Angry Customer",
                "email": "angry@example.com",
                "phone": "+19161234567",
                "zipcode": "95630",
                "lifetime_value": 5000.0,
                "booking_count": 10,
                "vip_status": True,
                "previous_escalations": 2,
            },
        )
        
        # Mock the complexity router to return HUMAN level
        with patch.object(
            orchestrator.complexity_router, 'classify', 
            return_value=("HUMAN", {"confidence": 0.95, "contains_crisis_keywords": True})
        ):
            # Mock database access for escalation service
            with patch('api.ai.orchestrator.ai_orchestrator.get_db') as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = iter([mock_db])
                
                # Mock EscalationService
                with patch('api.ai.orchestrator.ai_orchestrator.EscalationService') as mock_esc_svc:
                    mock_escalation = MagicMock()
                    mock_escalation.id = "esc-123"
                    mock_esc_svc.return_value.create_escalation = AsyncMock(return_value=mock_escalation)
                    
                    # Process the request
                    response = await orchestrator.process_inquiry(request, customer_id="cust-123")
        
        # Assertions
        assert response.success is True
        assert "Phase 3 (Human Escalation - Layer 5)" in response.metadata["phase"]
        assert "escalation_id" in response.metadata
        assert response.metadata["escalation_reason"] in [
            "crisis", "explicit_request", "complex_unsolved"
        ]
        assert response.metadata["urgency_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert "sentiment" in response.metadata
        assert response.confidence_score == 0.99  # High confidence for human handling
        assert "human_escalation" in response.tools_used
        
        # Verify customer-facing message is empathetic
        assert "team member" in response.message.lower() or "contact you" in response.message.lower()
        assert "Reference ID:" in response.message
    
    @pytest.mark.asyncio
    async def test_vip_customer_gets_priority_flags(self, orchestrator, mock_model_provider):
        """Test that VIP customers get proper priority flags"""
        request = OrchestratorRequest(
            message="I need to speak with someone about my upcoming event",
            channel="sms",
            customer_context={
                "name": "VIP Customer",
                "email": "vip@example.com",
                "phone": "+19161234567",
                "zipcode": "95630",
                "lifetime_value": 10000.0,
                "booking_count": 25,
                "vip_status": True,
                "previous_escalations": 0,
            },
        )
        
        with patch.object(
            orchestrator.complexity_router, 'classify',
            return_value=("HUMAN", {"confidence": 0.90, "explicit_human_request": True})
        ):
            with patch('api.ai.orchestrator.ai_orchestrator.get_db') as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = iter([mock_db])
                
                with patch('api.ai.orchestrator.ai_orchestrator.EscalationService') as mock_esc_svc:
                    mock_escalation = MagicMock()
                    mock_escalation.id = "esc-456"
                    mock_esc_svc.return_value.create_escalation = AsyncMock(return_value=mock_escalation)
                    
                    response = await orchestrator.process_inquiry(request, customer_id="cust-vip")
        
        # Check for VIP flags
        assert response.metadata["customer_vip_status"] is True
        assert response.metadata["customer_lifetime_value"] == 10000.0
        
        # Priority flags should include VIP indicator
        priority_flags = response.metadata.get("priority_flags", [])
        assert any("VIP" in flag or "⭐" in flag for flag in priority_flags)
    
    @pytest.mark.asyncio
    async def test_escalation_includes_ai_context(self, orchestrator, mock_model_provider):
        """Test that escalation includes comprehensive AI context"""
        request = OrchestratorRequest(
            message="I've been trying to get help for 30 minutes! This is ridiculous!",
            channel="web",
            customer_context={
                "name": "Frustrated Customer",
                "email": "frustrated@example.com",
                "phone": "+19161234567",
                "zipcode": "95630",
                "lifetime_value": 1500.0,
                "booking_count": 3,
                "vip_status": False,
                "previous_escalations": 1,
            },
        )
        
        with patch.object(
            orchestrator.complexity_router, 'classify',
            return_value=("HUMAN", {"confidence": 0.85, "low_confidence": True})
        ):
            with patch('api.ai.orchestrator.ai_orchestrator.get_db') as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = iter([mock_db])
                
                with patch('api.ai.orchestrator.ai_orchestrator.EscalationService') as mock_esc_svc:
                    mock_escalation = MagicMock()
                    mock_escalation.id = "esc-789"
                    mock_esc_svc.return_value.create_escalation = AsyncMock(return_value=mock_escalation)
                    
                    response = await orchestrator.process_inquiry(request, customer_id="cust-456")
        
        # Verify AI context is included
        assert "sentiment_explanation" in response.metadata
        assert "recommended_action" in response.metadata
        assert "escalation_cost_usd" in response.metadata
        assert response.metadata["escalation_cost_usd"] == 0.030
        
        # Verify admin notes are included
        assert "admin_notes" in response.metadata
    
    @pytest.mark.asyncio
    async def test_escalation_fallback_on_error(self, orchestrator, mock_model_provider):
        """Test that escalation falls back gracefully on errors"""
        request = OrchestratorRequest(
            message="I need help urgently!",
            channel="web",
            customer_context={
                "name": "Customer",
                "email": "customer@example.com",
                "lifetime_value": 500.0,
            },
        )
        
        # Make the HumanEscalationService raise an error
        with patch.object(
            orchestrator.complexity_router, 'classify',
            return_value=("HUMAN", {"confidence": 0.95})
        ):
            with patch('api.ai.orchestrator.ai_orchestrator.HumanEscalationService') as mock_hes:
                mock_hes.return_value.prepare_escalation = AsyncMock(
                    side_effect=Exception("Service unavailable")
                )
                
                # Mock router fallback
                orchestrator._process_with_router_or_legacy = AsyncMock(
                    return_value=MagicMock(
                        success=True,
                        message="Fallback response",
                        metadata={"phase": "Fallback"}
                    )
                )
                
                response = await orchestrator.process_inquiry(request, customer_id="cust-789")
        
        # Should fall back gracefully
        assert response.success is True
        assert "Fallback" in response.metadata.get("phase", "")
    
    @pytest.mark.asyncio
    async def test_lazy_initialization_of_escalation_service(self, orchestrator):
        """Test that HumanEscalationService is lazily initialized"""
        # Initially should be None
        assert orchestrator.human_escalation_service is None
        
        request = OrchestratorRequest(
            message="URGENT! NEED MANAGER NOW!",
            channel="web",
            customer_context={
                "name": "Urgent Customer",
                "phone": "+19161234567",
            },
        )
        
        with patch.object(
            orchestrator.complexity_router, 'classify',
            return_value=("HUMAN", {"confidence": 0.95, "contains_crisis_keywords": True})
        ):
            with patch('api.ai.orchestrator.ai_orchestrator.get_db') as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = iter([mock_db])
                
                with patch('api.ai.orchestrator.ai_orchestrator.EscalationService') as mock_esc_svc:
                    mock_escalation = MagicMock()
                    mock_escalation.id = "esc-lazy"
                    mock_esc_svc.return_value.create_escalation = AsyncMock(return_value=mock_escalation)
                    
                    response = await orchestrator.process_inquiry(request, customer_id="cust-lazy")
        
        # After processing HUMAN query, service should be initialized
        assert orchestrator.human_escalation_service is not None
        assert response.success is True
