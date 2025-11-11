"""
Tests for Human Escalation Integration (Layer 5)

Tests the AI context preparation and handoff to human agents.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock
import json

from api.ai.reasoning.human_escalation import (
    HumanEscalationService,
    EscalationReason,
    SentimentLevel,
    UrgencyLevel,
    EscalationResult,
    ConversationSummary,
    AIAttemptSummary,
    CustomerContext,
    RecommendedActions,
)


@pytest.fixture
def mock_model_provider():
    """Mock model provider for testing"""
    provider = Mock()
    provider.complete = AsyncMock()
    return provider


@pytest.fixture
def mock_escalation_service():
    """Mock escalation service for testing"""
    service = Mock()
    service.create_escalation = AsyncMock(return_value=12345)
    return service


@pytest.fixture
def human_escalation_service(mock_model_provider):
    """Human escalation service instance for testing"""
    return HumanEscalationService(mock_model_provider)


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history"""
    return [
        {"role": "user", "content": "I need a chef for Saturday"},
        {"role": "assistant", "content": "I can help! How many guests?"},
        {"role": "user", "content": "20 people"},
        {"role": "assistant", "content": "Great! Let me check availability..."},
        {"role": "user", "content": "This is taking too long! I want to speak to someone NOW!"},
    ]


@pytest.fixture
def sample_customer_context():
    """Sample customer context"""
    return {
        "name": "John Smith",
        "email": "john@example.com",
        "phone": "+19161234567",
        "zipcode": "95630",
        "lifetime_value": 3500.0,
        "booking_count": 5,
        "last_booking_date": "2025-10-15",
        "customer_since": "2024-01-01",
        "vip_status": False,
        "previous_escalations": 0,
    }


@pytest.fixture
def sample_ai_attempt():
    """Sample AI attempt metadata"""
    return {
        "phase": "Phase 3 (ReAct Agent)",
        "tools_used": ["check_availability", "get_pricing"],
        "confidence_score": 0.65,
        "reasoning_iterations": 2,
        "execution_time_ms": 2500,
        "reasoning_cost_usd": 0.005,
        "error": None,
    }


class TestSentimentAnalysis:
    """Tests for sentiment analysis"""

    @pytest.mark.asyncio
    async def test_very_negative_sentiment(
        self, human_escalation_service, mock_model_provider
    ):
        """Test detection of very negative sentiment"""
        
        # Mock response
        mock_model_provider.complete.return_value = json.dumps({
            "sentiment_level": -2,
            "explanation": "Customer using angry language and ALL CAPS"
        })
        
        conversation = [
            {"role": "user", "content": "THIS IS UNACCEPTABLE! I WANT A REFUND NOW!"}
        ]
        
        sentiment, explanation = await human_escalation_service._analyze_sentiment(
            "I AM VERY ANGRY!", conversation
        )
        
        assert sentiment == SentimentLevel.VERY_NEGATIVE
        assert "angry" in explanation.lower() or "caps" in explanation.lower()

    @pytest.mark.asyncio
    async def test_positive_sentiment(
        self, human_escalation_service, mock_model_provider
    ):
        """Test detection of positive sentiment"""
        
        mock_model_provider.complete.return_value = json.dumps({
            "sentiment_level": 2,
            "explanation": "Customer expressing gratitude and satisfaction"
        })
        
        conversation = [
            {"role": "user", "content": "Thank you so much! You've been very helpful!"}
        ]
        
        sentiment, explanation = await human_escalation_service._analyze_sentiment(
            "This is perfect!", conversation
        )
        
        assert sentiment == SentimentLevel.VERY_POSITIVE

    @pytest.mark.asyncio
    async def test_neutral_sentiment(
        self, human_escalation_service, mock_model_provider
    ):
        """Test detection of neutral sentiment"""
        
        mock_model_provider.complete.return_value = json.dumps({
            "sentiment_level": 0,
            "explanation": "Factual inquiry with calm tone"
        })
        
        conversation = [
            {"role": "user", "content": "What time do you close?"}
        ]
        
        sentiment, explanation = await human_escalation_service._analyze_sentiment(
            "I have a question", conversation
        )
        
        assert sentiment == SentimentLevel.NEUTRAL

    @pytest.mark.asyncio
    async def test_sentiment_analysis_error_handling(
        self, human_escalation_service, mock_model_provider
    ):
        """Test that sentiment analysis handles errors gracefully"""
        
        # Mock error
        mock_model_provider.complete.side_effect = Exception("API error")
        
        sentiment, explanation = await human_escalation_service._analyze_sentiment(
            "Test query", []
        )
        
        # Should default to neutral
        assert sentiment == SentimentLevel.NEUTRAL
        assert "unable" in explanation.lower()


class TestConversationSummarization:
    """Tests for conversation summarization"""

    @pytest.mark.asyncio
    async def test_conversation_summary(
        self, human_escalation_service, mock_model_provider, sample_conversation_history
    ):
        """Test conversation summarization"""
        
        mock_model_provider.complete.return_value = json.dumps({
            "key_topics": ["booking", "availability", "frustration"],
            "customer_requests": ["Check availability for Saturday", "Speak to human"],
            "ai_responses": ["Offered to help", "Asked for guest count"],
            "sentiment_trend": "declining",
            "frustration_indicators": ["taking too long", "want to speak NOW"],
        })
        
        summary = await human_escalation_service._summarize_conversation(
            sample_conversation_history
        )
        
        assert isinstance(summary, ConversationSummary)
        assert summary.message_count == len(sample_conversation_history)
        assert len(summary.key_topics) > 0
        assert len(summary.frustration_indicators) > 0
        assert summary.sentiment_trend == "declining"

    @pytest.mark.asyncio
    async def test_empty_conversation_summary(self, human_escalation_service):
        """Test summarization of empty conversation"""
        
        summary = await human_escalation_service._summarize_conversation([])
        
        assert summary.message_count == 0
        assert len(summary.key_topics) == 0
        assert summary.sentiment_trend == "stable"

    @pytest.mark.asyncio
    async def test_summarization_error_handling(
        self, human_escalation_service, mock_model_provider
    ):
        """Test that summarization handles errors gracefully"""
        
        mock_model_provider.complete.side_effect = Exception("API error")
        
        summary = await human_escalation_service._summarize_conversation(
            [{"role": "user", "content": "test"}]
        )
        
        assert summary.message_count == 1
        assert len(summary.key_topics) > 0  # Has fallback


class TestUrgencyDetermination:
    """Tests for urgency level determination"""

    @pytest.mark.asyncio
    async def test_critical_urgency_crisis(self, human_escalation_service):
        """Test critical urgency for crisis situations"""
        
        conversation_summary = ConversationSummary(
            message_count=10,
            duration_minutes=15,
            key_topics=[],
            customer_requests=[],
            ai_responses=[],
            sentiment_trend="declining",
            frustration_indicators=["angry", "frustrated", "manager"],
        )
        
        urgency = await human_escalation_service._determine_urgency(
            "I DEMAND TO SPEAK TO YOUR MANAGER!",
            SentimentLevel.VERY_NEGATIVE,
            EscalationReason.CRISIS,
            conversation_summary,
        )
        
        assert urgency == UrgencyLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_high_urgency_explicit_request(self, human_escalation_service):
        """Test high urgency for explicit human request"""
        
        conversation_summary = ConversationSummary(
            message_count=3,
            duration_minutes=5,
            key_topics=[],
            customer_requests=[],
            ai_responses=[],
            sentiment_trend="stable",
            frustration_indicators=["speak to person"],
        )
        
        urgency = await human_escalation_service._determine_urgency(
            "I want to speak to a real person",
            SentimentLevel.NEGATIVE,
            EscalationReason.EXPLICIT_REQUEST,
            conversation_summary,
        )
        
        assert urgency in [UrgencyLevel.HIGH, UrgencyLevel.MEDIUM]

    @pytest.mark.asyncio
    async def test_low_urgency_info_request(self, human_escalation_service):
        """Test low urgency for informational queries"""
        
        conversation_summary = ConversationSummary(
            message_count=2,
            duration_minutes=1,
            key_topics=[],
            customer_requests=[],
            ai_responses=[],
            sentiment_trend="stable",
            frustration_indicators=[],
        )
        
        urgency = await human_escalation_service._determine_urgency(
            "Just need more information",
            SentimentLevel.NEUTRAL,
            EscalationReason.LOW_CONFIDENCE,
            conversation_summary,
        )
        
        assert urgency in [UrgencyLevel.LOW, UrgencyLevel.MEDIUM]


class TestRecommendationGeneration:
    """Tests for action recommendation generation"""

    @pytest.mark.asyncio
    async def test_generate_recommendations(
        self,
        human_escalation_service,
        mock_model_provider,
        sample_conversation_history,
        sample_customer_context,
    ):
        """Test recommendation generation"""
        
        mock_model_provider.complete.return_value = json.dumps({
            "primary_action": "Call customer immediately to apologize and resolve",
            "alternative_actions": ["Offer discount", "Escalate to manager"],
            "things_to_avoid": ["Making excuses", "Automated responses"],
            "relevant_policies": ["Refund policy", "Customer satisfaction guarantee"],
            "suggested_response_template": "Hi John, I sincerely apologize for the delay...",
        })
        
        ai_attempt = AIAttemptSummary(
            reasoning_layer_used="react",
            tools_used=["check_availability"],
            confidence_score=0.6,
            quality_score=None,
            iterations=2,
            duration_ms=2000,
            cost_usd=0.005,
            failure_reason=None,
        )
        
        recommendations = await human_escalation_service._generate_recommendations(
            "I need help now!",
            sample_conversation_history,
            sample_customer_context,
            ai_attempt,
            EscalationReason.CRISIS,
        )
        
        assert isinstance(recommendations, RecommendedActions)
        assert len(recommendations.primary_action) > 0
        assert len(recommendations.alternative_actions) > 0
        assert len(recommendations.things_to_avoid) > 0

    @pytest.mark.asyncio
    async def test_recommendations_error_handling(
        self, human_escalation_service, mock_model_provider
    ):
        """Test that recommendation generation handles errors gracefully"""
        
        mock_model_provider.complete.side_effect = Exception("API error")
        
        ai_attempt = AIAttemptSummary(
            reasoning_layer_used="react",
            tools_used=[],
            confidence_score=0.5,
            quality_score=None,
            iterations=1,
            duration_ms=1000,
            cost_usd=0.0,
            failure_reason=None,
        )
        
        recommendations = await human_escalation_service._generate_recommendations(
            "Test query", [], {}, ai_attempt, EscalationReason.LOW_CONFIDENCE
        )
        
        # Should have fallback recommendations
        assert len(recommendations.primary_action) > 0
        assert "review" in recommendations.primary_action.lower()


class TestFullEscalationFlow:
    """Tests for complete escalation preparation"""

    @pytest.mark.asyncio
    async def test_prepare_escalation_success(
        self,
        human_escalation_service,
        mock_model_provider,
        sample_conversation_history,
        sample_customer_context,
        sample_ai_attempt,
    ):
        """Test successful escalation context preparation"""
        
        # Mock all LLM responses
        mock_model_provider.complete.side_effect = [
            # Sentiment analysis
            json.dumps({
                "sentiment_level": -1,
                "explanation": "Customer is frustrated with delay"
            }),
            # Conversation summary
            json.dumps({
                "key_topics": ["booking", "delay"],
                "customer_requests": ["Speak to human"],
                "ai_responses": ["Checking availability"],
                "sentiment_trend": "declining",
                "frustration_indicators": ["taking too long"],
            }),
            # Recommendations
            json.dumps({
                "primary_action": "Call customer to resolve",
                "alternative_actions": ["Expedite booking"],
                "things_to_avoid": ["Further delays"],
                "relevant_policies": ["Response time SLA"],
                "suggested_response_template": "Hi John, I apologize...",
            }),
        ]
        
        result = await human_escalation_service.prepare_escalation(
            query="I want to speak to someone NOW!",
            customer_id="C123",
            customer_context=sample_customer_context,
            conversation_history=sample_conversation_history,
            ai_attempt=sample_ai_attempt,
            escalation_reason=EscalationReason.EXPLICIT_REQUEST,
            channel="web",
        )
        
        # Verify result
        assert isinstance(result, EscalationResult)
        assert result.success is True
        assert result.context is not None
        assert result.duration_ms >= 0  # Can be 0 in fast unit tests
        
        # Verify context
        context = result.context
        assert context.escalation_reason == EscalationReason.EXPLICIT_REQUEST
        assert context.urgency_level in [UrgencyLevel.HIGH, UrgencyLevel.MEDIUM]
        assert context.current_sentiment == SentimentLevel.NEGATIVE
        assert context.customer_context.customer_id == "C123"
        assert context.customer_context.name == "John Smith"
        assert len(context.what_ai_tried) > 0
        assert len(context.why_ai_failed) > 0
        assert len(context.recommended_actions.primary_action) > 0

    @pytest.mark.asyncio
    async def test_prepare_escalation_crisis(
        self,
        human_escalation_service,
        mock_model_provider,
        sample_conversation_history,
        sample_customer_context,
        sample_ai_attempt,
    ):
        """Test escalation for crisis situation"""
        
        # Mock responses
        mock_model_provider.complete.side_effect = [
            json.dumps({"sentiment_level": -2, "explanation": "Very angry"}),
            json.dumps({
                "key_topics": ["complaint", "refund"],
                "customer_requests": ["Refund", "Manager"],
                "ai_responses": ["Checking policy"],
                "sentiment_trend": "declining",
                "frustration_indicators": ["ANGRY", "UNACCEPTABLE"],
            }),
            json.dumps({
                "primary_action": "Immediate callback from manager",
                "alternative_actions": ["Full refund offer"],
                "things_to_avoid": ["Delays", "Excuses"],
                "relevant_policies": ["Satisfaction guarantee"],
                "suggested_response_template": "Mr. Smith, I sincerely apologize...",
            }),
        ]
        
        result = await human_escalation_service.prepare_escalation(
            query="THIS IS UNACCEPTABLE!",
            customer_id="C123",
            customer_context=sample_customer_context,
            conversation_history=sample_conversation_history,
            ai_attempt=sample_ai_attempt,
            escalation_reason=EscalationReason.CRISIS,
            channel="phone",
        )
        
        assert result.success is True
        assert result.context.urgency_level == UrgencyLevel.CRITICAL
        assert result.context.current_sentiment == SentimentLevel.VERY_NEGATIVE
        assert any("CRITICAL" in flag for flag in result.context.priority_flags)

    @pytest.mark.asyncio
    async def test_prepare_escalation_vip_customer(
        self,
        human_escalation_service,
        mock_model_provider,
        sample_conversation_history,
        sample_ai_attempt,
    ):
        """Test escalation for VIP customer"""
        
        vip_context = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+19165551234",
            "lifetime_value": 15000.0,
            "booking_count": 25,
            "vip_status": True,
            "previous_escalations": 0,
        }
        
        # Mock responses
        mock_model_provider.complete.side_effect = [
            json.dumps({"sentiment_level": 0, "explanation": "Neutral"}),
            json.dumps({
                "key_topics": ["special request"],
                "customer_requests": ["Custom menu"],
                "ai_responses": ["Let me check"],
                "sentiment_trend": "stable",
                "frustration_indicators": [],
            }),
            json.dumps({
                "primary_action": "Prioritize VIP request",
                "alternative_actions": ["Custom solution"],
                "things_to_avoid": ["Standard response"],
                "relevant_policies": ["VIP policy"],
                "suggested_response_template": "Ms. Doe, thank you for...",
            }),
        ]
        
        result = await human_escalation_service.prepare_escalation(
            query="I need a custom menu for my event",
            customer_id="C456",
            customer_context=vip_context,
            conversation_history=sample_conversation_history,
            ai_attempt=sample_ai_attempt,
            escalation_reason=EscalationReason.HIGH_VALUE,
            channel="email",
        )
        
        assert result.success is True
        assert result.context.customer_context.vip_status is True
        assert any("VIP" in flag for flag in result.context.priority_flags)
        assert any("High value" in flag for flag in result.context.priority_flags)

    @pytest.mark.asyncio
    async def test_prepare_escalation_error_handling(
        self, human_escalation_service, mock_model_provider
    ):
        """Test that escalation preparation handles errors gracefully"""
        
        # Mock error
        mock_model_provider.complete.side_effect = Exception("Critical API error")
        
        result = await human_escalation_service.prepare_escalation(
            query="Test query",
            customer_id="C789",
            customer_context={},
            conversation_history=[],
            ai_attempt={},
            escalation_reason=EscalationReason.TECHNICAL_ERROR,
            channel="web",
        )
        
        # Should return result with fallback values (service is resilient)
        assert isinstance(result, EscalationResult)
        assert result.success is True  # Service handles errors gracefully
        assert result.context is not None
        # Context should have fallback/default values
        assert result.context.current_sentiment == SentimentLevel.NEUTRAL
        assert "unable" in result.context.sentiment_explanation.lower()


class TestHelperMethods:
    """Tests for helper methods"""

    def test_extract_ai_attempt(self, human_escalation_service):
        """Test AI attempt extraction"""
        
        ai_data = {
            "phase": "Phase 3 (Multi-Agent)",
            "tools_used": ["tool1", "tool2"],
            "confidence_score": 0.75,
            "multi_agent_quality_score": 0.88,
            "reasoning_iterations": 3,
            "execution_time_ms": 5000,
            "reasoning_cost_usd": 0.015,
            "error": None,
        }
        
        summary = human_escalation_service._extract_ai_attempt(ai_data)
        
        assert isinstance(summary, AIAttemptSummary)
        assert summary.reasoning_layer_used == "Phase 3 (Multi-Agent)"
        assert len(summary.tools_used) == 2
        assert summary.confidence_score == 0.75
        assert summary.quality_score == 0.88

    def test_build_customer_context(self, human_escalation_service):
        """Test customer context building"""
        
        customer_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+19165551234",
            "zipcode": "95630",
            "lifetime_value": 2500.0,
            "booking_count": 3,
            "vip_status": False,
        }
        
        context = human_escalation_service._build_customer_context(
            "C999", customer_data, "sms"
        )
        
        assert isinstance(context, CustomerContext)
        assert context.customer_id == "C999"
        assert context.name == "Test User"
        assert context.channel == "sms"
        assert context.lifetime_value == 2500.0

    def test_generate_escalation_id(self, human_escalation_service):
        """Test escalation ID generation"""
        
        escalation_id = human_escalation_service._generate_escalation_id("C123456789")
        
        assert escalation_id.startswith("ESC-C1234567-")
        assert len(escalation_id) > 20

    def test_explain_ai_failure_crisis(self, human_escalation_service):
        """Test AI failure explanation for crisis"""
        
        ai_attempt = AIAttemptSummary(
            reasoning_layer_used="react",
            tools_used=[],
            confidence_score=0.5,
            quality_score=None,
            iterations=1,
            duration_ms=1000,
            cost_usd=0.0,
            failure_reason=None,
        )
        
        explanation = human_escalation_service._explain_ai_failure(
            ai_attempt, EscalationReason.CRISIS
        )
        
        assert "angry" in explanation.lower() or "frustrated" in explanation.lower()

    def test_generate_priority_flags(self, human_escalation_service):
        """Test priority flag generation"""
        
        customer = CustomerContext(
            customer_id="C123",
            name="Test",
            email=None,
            phone=None,
            location=None,
            channel="web",
            lifetime_value=8000.0,
            booking_count=15,
            last_booking_date=None,
            customer_since=None,
            vip_status=True,
            previous_escalations=3,
        )
        
        flags = human_escalation_service._generate_priority_flags(
            UrgencyLevel.CRITICAL,
            SentimentLevel.VERY_NEGATIVE,
            customer,
        )
        
        assert len(flags) > 0
        assert any("CRITICAL" in flag for flag in flags)
        assert any("angry" in flag.lower() for flag in flags)
        assert any("VIP" in flag for flag in flags)
        assert any("value" in flag.lower() for flag in flags)
        assert any("Repeat" in flag for flag in flags)
