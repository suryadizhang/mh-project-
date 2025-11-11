"""
Human Escalation Integration (Layer 5) - AI Context Preparation & Seamless Handoff

This module prepares comprehensive AI context for human agents when queries require
human intervention. It ensures seamless handoff with full context preservation.

Use Cases:
- Crisis situations (angry customers, complaints)
- Sensitive topics (refunds, cancellations, legal)
- High-value queries (large bookings, VIP customers)
- AI uncertainty (low confidence responses)
- Explicit human requests ("I want to speak to a person")

Target Accuracy: 99% (AI + Human combined)
Expected Usage: 1% of queries
Cost: ~$0.030 per escalation (AI context prep + handoff)

Author: MyHibachi AI Team
Created: November 10, 2025
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class EscalationReason(Enum):
    """Reasons for human escalation"""

    CRISIS = "crisis"  # Angry customer, urgent complaint
    SENSITIVE = "sensitive"  # Refunds, cancellations, legal matters
    HIGH_VALUE = "high_value"  # Large booking, VIP customer
    LOW_CONFIDENCE = "low_confidence"  # AI uncertain about response
    EXPLICIT_REQUEST = "explicit_request"  # Customer asks for human
    COMPLEX_UNSOLVED = "complex_unsolved"  # Multi-agent couldn't solve
    POLICY_EXCEPTION = "policy_exception"  # Requires human judgment
    TECHNICAL_ERROR = "technical_error"  # AI system error


class SentimentLevel(Enum):
    """Customer sentiment levels"""

    VERY_NEGATIVE = -2  # Angry, frustrated
    NEGATIVE = -1  # Unhappy, disappointed
    NEUTRAL = 0  # Calm, informational
    POSITIVE = 1  # Satisfied, happy
    VERY_POSITIVE = 2  # Delighted, grateful


class UrgencyLevel(Enum):
    """Escalation urgency levels"""

    LOW = 1  # Can wait, informational
    MEDIUM = 2  # Important, needs attention soon
    HIGH = 3  # Urgent, needs immediate response
    CRITICAL = 4  # Crisis, drop everything


@dataclass
class ConversationSummary:
    """Summary of conversation history"""

    message_count: int
    duration_minutes: float
    key_topics: list[str]
    customer_requests: list[str]
    ai_responses: list[str]
    sentiment_trend: str  # "improving", "declining", "stable"
    frustration_indicators: list[str]


@dataclass
class AIAttemptSummary:
    """Summary of AI's attempt to handle the query"""

    reasoning_layer_used: str  # "cache", "react", "multi_agent"
    tools_used: list[str]
    confidence_score: float  # 0-1
    quality_score: float | None  # 0-1 (from multi-agent critic)
    iterations: int
    duration_ms: int
    cost_usd: float
    failure_reason: str | None


@dataclass
class CustomerContext:
    """Detailed customer context"""

    customer_id: str
    name: str | None
    email: str | None
    phone: str | None
    location: str | None
    channel: str  # "web", "email", "sms", "phone"
    lifetime_value: float  # Total spent
    booking_count: int
    last_booking_date: str | None
    customer_since: str | None
    vip_status: bool
    previous_escalations: int


@dataclass
class RecommendedActions:
    """AI-recommended actions for human agent"""

    primary_action: str
    alternative_actions: list[str]
    things_to_avoid: list[str]
    relevant_policies: list[str]
    suggested_response_template: str | None


@dataclass
class EscalationContext:
    """
    Complete context package for human agent.
    
    This provides everything a human agent needs to seamlessly
    continue the conversation without asking the customer to repeat information.
    """

    # Core identification
    escalation_id: str
    escalation_reason: EscalationReason
    urgency_level: UrgencyLevel
    created_at: datetime

    # Customer information
    customer_context: CustomerContext
    current_sentiment: SentimentLevel
    sentiment_explanation: str

    # Conversation context
    original_query: str
    conversation_summary: ConversationSummary
    full_conversation_history: list[dict[str, str]]

    # AI attempt context
    ai_attempt: AIAttemptSummary
    what_ai_tried: list[str]
    why_ai_failed: str

    # Handoff guidance
    recommended_actions: RecommendedActions
    admin_notes: str | None
    priority_flags: list[str]

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EscalationResult:
    """Result of escalation context preparation"""

    success: bool
    context: EscalationContext | None
    escalation_record_id: int | None  # ID in database
    error: str | None = None
    duration_ms: int = 0


class HumanEscalationService:
    """
    Prepares comprehensive context for human agent handoff.

    This service analyzes the conversation, AI attempts, and customer context
    to provide a complete picture for the human agent taking over.
    """

    def __init__(self, model_provider, escalation_service=None):
        self.model_provider = model_provider
        self.escalation_service = escalation_service
        self.logger = logging.getLogger(__name__)

    async def prepare_escalation(
        self,
        query: str,
        customer_id: str,
        customer_context: dict[str, Any],
        conversation_history: list[dict[str, str]],
        ai_attempt: dict[str, Any],
        escalation_reason: EscalationReason,
        channel: str = "web",
    ) -> EscalationResult:
        """
        Prepare complete escalation context for human handoff.

        Args:
            query: Current customer query
            customer_id: Customer identifier
            customer_context: Customer information
            conversation_history: Full conversation history
            ai_attempt: Details of AI's attempt to handle query
            escalation_reason: Why escalation is needed
            channel: Communication channel

        Returns:
            EscalationResult with complete context package
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Step 1: Analyze sentiment
            sentiment, sentiment_explanation = await self._analyze_sentiment(
                query, conversation_history
            )

            # Step 2: Summarize conversation
            conversation_summary = await self._summarize_conversation(conversation_history)

            # Step 3: Determine urgency
            urgency = await self._determine_urgency(
                query, sentiment, escalation_reason, conversation_summary
            )

            # Step 4: Analyze AI attempt
            ai_attempt_summary = self._extract_ai_attempt(ai_attempt)

            # Step 5: Generate recommended actions
            recommended_actions = await self._generate_recommendations(
                query,
                conversation_history,
                customer_context,
                ai_attempt_summary,
                escalation_reason,
            )

            # Step 6: Build customer context
            customer_ctx = self._build_customer_context(
                customer_id, customer_context, channel
            )

            # Step 7: Generate escalation ID
            escalation_id = self._generate_escalation_id(customer_id)

            # Step 8: Explain why AI failed
            why_failed = self._explain_ai_failure(ai_attempt_summary, escalation_reason)

            # Step 9: Extract what AI tried
            what_tried = self._extract_ai_actions(ai_attempt_summary, conversation_history)

            # Step 10: Create escalation context
            context = EscalationContext(
                escalation_id=escalation_id,
                escalation_reason=escalation_reason,
                urgency_level=urgency,
                created_at=start_time,
                customer_context=customer_ctx,
                current_sentiment=sentiment,
                sentiment_explanation=sentiment_explanation,
                original_query=query,
                conversation_summary=conversation_summary,
                full_conversation_history=conversation_history,
                ai_attempt=ai_attempt_summary,
                what_ai_tried=what_tried,
                why_ai_failed=why_failed,
                recommended_actions=recommended_actions,
                admin_notes=None,
                priority_flags=self._generate_priority_flags(
                    urgency, sentiment, customer_ctx
                ),
                metadata={
                    "channel": channel,
                    "customer_id": customer_id,
                    "escalation_reason": escalation_reason.value,
                },
            )

            # Step 11: Save to escalation service (if available)
            escalation_record_id = None
            if self.escalation_service:
                try:
                    escalation_record_id = await self._save_to_escalation_service(context)
                except Exception as e:
                    self.logger.warning(f"Failed to save escalation record: {e}")

            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            self.logger.info(
                f"Escalation context prepared: {escalation_id}, "
                f"reason={escalation_reason.value}, urgency={urgency.name}"
            )

            return EscalationResult(
                success=True,
                context=context,
                escalation_record_id=escalation_record_id,
                duration_ms=duration_ms,
            )

        except Exception as e:
            self.logger.error(f"Failed to prepare escalation context: {e}", exc_info=True)
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            return EscalationResult(
                success=False,
                context=None,
                escalation_record_id=None,
                error=str(e),
                duration_ms=duration_ms,
            )

    async def _analyze_sentiment(
        self, query: str, conversation_history: list[dict[str, str]]
    ) -> tuple[SentimentLevel, str]:
        """Analyze customer sentiment from conversation"""
        
        # Build conversation text
        conversation_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in conversation_history[-5:]  # Last 5 messages
        ])
        conversation_text += f"\nuser: {query}"

        system_prompt = """You are a sentiment analysis expert for customer service.

Analyze the customer's sentiment and explain why you assessed it that way.

Output JSON:
{
    "sentiment_level": -2 to 2 (-2=very negative, -1=negative, 0=neutral, 1=positive, 2=very positive),
    "explanation": "Brief explanation of sentiment indicators"
}

Look for:
- Negative: angry words, frustration, complaints, threats, ALL CAPS
- Positive: gratitude, satisfaction, praise
- Neutral: factual questions, calm tone"""

        try:
            response = await self.model_provider.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Conversation:\n{conversation_text}\n\nAnalyze sentiment:"},
                ],
                temperature=0.3,
            )

            data = json.loads(response)
            level_value = data["sentiment_level"]
            explanation = data["explanation"]

            # Map to enum
            if level_value <= -2:
                sentiment = SentimentLevel.VERY_NEGATIVE
            elif level_value == -1:
                sentiment = SentimentLevel.NEGATIVE
            elif level_value == 0:
                sentiment = SentimentLevel.NEUTRAL
            elif level_value == 1:
                sentiment = SentimentLevel.POSITIVE
            else:
                sentiment = SentimentLevel.VERY_POSITIVE

            return sentiment, explanation

        except Exception as e:
            self.logger.warning(f"Sentiment analysis failed: {e}")
            # Default to neutral
            return SentimentLevel.NEUTRAL, "Unable to determine sentiment"

    async def _summarize_conversation(
        self, conversation_history: list[dict[str, str]]
    ) -> ConversationSummary:
        """Generate conversation summary"""

        if not conversation_history:
            return ConversationSummary(
                message_count=0,
                duration_minutes=0,
                key_topics=[],
                customer_requests=[],
                ai_responses=[],
                sentiment_trend="stable",
                frustration_indicators=[],
            )

        # Build conversation text
        conversation_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in conversation_history
        ])

        system_prompt = """Summarize this customer service conversation.

Output JSON:
{
    "key_topics": ["topic1", "topic2", ...],
    "customer_requests": ["request1", "request2", ...],
    "ai_responses": ["response1", "response2", ...],
    "sentiment_trend": "improving" or "declining" or "stable",
    "frustration_indicators": ["indicator1", ...]
}

Focus on:
- What the customer wants
- What the AI tried to do
- Any signs of frustration or escalation"""

        try:
            response = await self.model_provider.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Conversation:\n{conversation_text}"},
                ],
                temperature=0.3,
            )

            data = json.loads(response)

            return ConversationSummary(
                message_count=len(conversation_history),
                duration_minutes=0,  # Would need timestamps to calculate
                key_topics=data.get("key_topics", []),
                customer_requests=data.get("customer_requests", []),
                ai_responses=data.get("ai_responses", []),
                sentiment_trend=data.get("sentiment_trend", "stable"),
                frustration_indicators=data.get("frustration_indicators", []),
            )

        except Exception as e:
            self.logger.warning(f"Conversation summarization failed: {e}")
            return ConversationSummary(
                message_count=len(conversation_history),
                duration_minutes=0,
                key_topics=["Unable to summarize"],
                customer_requests=[],
                ai_responses=[],
                sentiment_trend="stable",
                frustration_indicators=[],
            )

    async def _determine_urgency(
        self,
        query: str,
        sentiment: SentimentLevel,
        escalation_reason: EscalationReason,
        conversation_summary: ConversationSummary,
    ) -> UrgencyLevel:
        """Determine escalation urgency"""

        # Rule-based urgency determination
        urgency_score = 0

        # Sentiment impact
        if sentiment == SentimentLevel.VERY_NEGATIVE:
            urgency_score += 3
        elif sentiment == SentimentLevel.NEGATIVE:
            urgency_score += 2

        # Escalation reason impact
        if escalation_reason == EscalationReason.CRISIS:
            urgency_score += 4
        elif escalation_reason in [
            EscalationReason.SENSITIVE,
            EscalationReason.EXPLICIT_REQUEST,
        ]:
            urgency_score += 2
        elif escalation_reason == EscalationReason.HIGH_VALUE:
            urgency_score += 2

        # Frustration indicators
        if len(conversation_summary.frustration_indicators) > 2:
            urgency_score += 2

        # Conversation length (longer = more frustrated)
        if conversation_summary.message_count > 10:
            urgency_score += 1

        # Map score to urgency level
        if urgency_score >= 6:
            return UrgencyLevel.CRITICAL
        elif urgency_score >= 4:
            return UrgencyLevel.HIGH
        elif urgency_score >= 2:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW

    def _extract_ai_attempt(self, ai_attempt: dict[str, Any]) -> AIAttemptSummary:
        """Extract AI attempt details"""
        
        return AIAttemptSummary(
            reasoning_layer_used=ai_attempt.get("phase", "unknown"),
            tools_used=ai_attempt.get("tools_used", []),
            confidence_score=ai_attempt.get("confidence_score", 0.5),
            quality_score=ai_attempt.get("multi_agent_quality_score"),
            iterations=ai_attempt.get("reasoning_iterations", 0),
            duration_ms=ai_attempt.get("execution_time_ms", 0),
            cost_usd=ai_attempt.get("reasoning_cost_usd", 0.0),
            failure_reason=ai_attempt.get("error"),
        )

    async def _generate_recommendations(
        self,
        query: str,
        conversation_history: list[dict[str, str]],
        customer_context: dict[str, Any],
        ai_attempt: AIAttemptSummary,
        escalation_reason: EscalationReason,
    ) -> RecommendedActions:
        """Generate action recommendations for human agent"""

        context_text = f"""
Query: {query}
Customer: {customer_context.get('name', 'Unknown')}
Escalation Reason: {escalation_reason.value}
AI Tried: {', '.join(ai_attempt.tools_used) or 'No tools'}
Failure: {ai_attempt.failure_reason or 'Uncertain'}
"""

        system_prompt = """You are a customer service expert advisor.

Based on the escalation, recommend actions for the human agent.

Output JSON:
{
    "primary_action": "Main action to take",
    "alternative_actions": ["Alternative 1", "Alternative 2", ...],
    "things_to_avoid": ["Don't do this", ...],
    "relevant_policies": ["Policy 1", "Policy 2", ...],
    "suggested_response_template": "Hi [name], I understand..."
}

Be specific and actionable."""

        try:
            response = await self.model_provider.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context_text},
                ],
                temperature=0.4,
            )

            data = json.loads(response)

            return RecommendedActions(
                primary_action=data.get("primary_action", "Review and respond"),
                alternative_actions=data.get("alternative_actions", []),
                things_to_avoid=data.get("things_to_avoid", []),
                relevant_policies=data.get("relevant_policies", []),
                suggested_response_template=data.get("suggested_response_template"),
            )

        except Exception as e:
            self.logger.warning(f"Recommendation generation failed: {e}")
            return RecommendedActions(
                primary_action="Review customer inquiry and respond appropriately",
                alternative_actions=["Call customer directly", "Escalate to manager"],
                things_to_avoid=["Making promises without checking", "Rushing response"],
                relevant_policies=["Standard refund policy", "Cancellation policy"],
                suggested_response_template=None,
            )

    def _build_customer_context(
        self, customer_id: str, customer_context: dict[str, Any], channel: str
    ) -> CustomerContext:
        """Build customer context from data"""
        
        return CustomerContext(
            customer_id=customer_id,
            name=customer_context.get("name"),
            email=customer_context.get("email"),
            phone=customer_context.get("phone"),
            location=customer_context.get("address") or customer_context.get("zipcode"),
            channel=channel,
            lifetime_value=customer_context.get("lifetime_value", 0.0),
            booking_count=customer_context.get("booking_count", 0),
            last_booking_date=customer_context.get("last_booking_date"),
            customer_since=customer_context.get("customer_since"),
            vip_status=customer_context.get("vip_status", False),
            previous_escalations=customer_context.get("previous_escalations", 0),
        )

    def _generate_escalation_id(self, customer_id: str) -> str:
        """Generate unique escalation ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"ESC-{customer_id[:8]}-{timestamp}"

    def _explain_ai_failure(
        self, ai_attempt: AIAttemptSummary, escalation_reason: EscalationReason
    ) -> str:
        """Explain why AI couldn't handle the query"""
        
        if escalation_reason == EscalationReason.CRISIS:
            return "Customer is angry/frustrated and needs empathetic human response"
        elif escalation_reason == EscalationReason.SENSITIVE:
            return "Query involves sensitive topics requiring human judgment"
        elif escalation_reason == EscalationReason.EXPLICIT_REQUEST:
            return "Customer explicitly requested to speak with a human agent"
        elif escalation_reason == EscalationReason.LOW_CONFIDENCE:
            return f"AI confidence too low ({ai_attempt.confidence_score:.0%}) to provide reliable answer"
        elif escalation_reason == EscalationReason.COMPLEX_UNSOLVED:
            return "Multi-agent system couldn't find satisfactory solution"
        elif escalation_reason == EscalationReason.POLICY_EXCEPTION:
            return "Query requires exception to standard policy - needs human approval"
        elif escalation_reason == EscalationReason.TECHNICAL_ERROR:
            return f"AI system error: {ai_attempt.failure_reason or 'Unknown error'}"
        else:
            return "AI determined human assistance would provide better outcome"

    def _extract_ai_actions(
        self, ai_attempt: AIAttemptSummary, conversation_history: list[dict[str, str]]
    ) -> list[str]:
        """Extract what actions AI attempted"""
        
        actions = []
        
        if ai_attempt.tools_used:
            actions.extend([f"Used tool: {tool}" for tool in ai_attempt.tools_used])
        
        if ai_attempt.iterations > 1:
            actions.append(f"Performed {ai_attempt.iterations} reasoning iterations")
        
        if ai_attempt.reasoning_layer_used:
            actions.append(f"Used {ai_attempt.reasoning_layer_used} reasoning layer")
        
        if not actions:
            actions.append("Attempted to provide direct response")
        
        return actions

    def _generate_priority_flags(
        self, urgency: UrgencyLevel, sentiment: SentimentLevel, customer: CustomerContext
    ) -> list[str]:
        """Generate priority flags for admin attention"""
        
        flags = []
        
        if urgency == UrgencyLevel.CRITICAL:
            flags.append("🚨 CRITICAL - Immediate response required")
        elif urgency == UrgencyLevel.HIGH:
            flags.append("⚠️ HIGH PRIORITY - Respond within 1 hour")
        
        if sentiment == SentimentLevel.VERY_NEGATIVE:
            flags.append("😤 Very angry customer")
        
        if customer.vip_status:
            flags.append("⭐ VIP Customer")
        
        if customer.lifetime_value > 5000:
            flags.append(f"💰 High value customer (${customer.lifetime_value:,.0f})")
        
        if customer.previous_escalations > 2:
            flags.append(f"🔄 Repeat escalation ({customer.previous_escalations} previous)")
        
        return flags

    async def _save_to_escalation_service(self, context: EscalationContext) -> int:
        """Save escalation to database via escalation service"""
        
        if not self.escalation_service:
            return None
        
        # This would integrate with existing EscalationService
        # For now, return mock ID
        return 12345
