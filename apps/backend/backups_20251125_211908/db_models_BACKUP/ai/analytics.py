"""
AI Analytics and Usage Tracking Models - ai Schema

This module handles conversation analytics, AI usage tracking, and training data collection.

Business Requirements:
- Conversation quality metrics
- AI performance tracking (tokens, cost, response time)
- Training data collection for model improvement
- ROI analytics (cost per conversation, resolution rates)
- Customer satisfaction tracking

Schema: ai
Tables: conversation_analytics, ai_usage, training_data
"""

from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from models.base import Base


# ============================================================================
# ENUMS
# ============================================================================


class ResolutionStatus(str, Enum):
    """
    Conversation resolution status.

    Business Context:
    - RESOLVED: Customer satisfied, issue resolved
    - UNRESOLVED: Customer left unsatisfied
    - ESCALATED: Transferred to human agent
    - ABANDONED: Customer left mid-conversation
    """
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    ESCALATED = "escalated"
    ABANDONED = "abandoned"


# ============================================================================
# CONVERSATION ANALYTICS MODEL
# ============================================================================


class ConversationAnalytics(Base):
    """
    Analytics and metrics for conversation quality.

    Schema: ai.conversation_analytics

    Business Logic:
    1. Track conversation quality (resolution, satisfaction)
    2. Measure AI performance (confidence, response time)
    3. Calculate costs (tokens, USD)
    4. Identify improvement opportunities
    5. Support ROI reporting

    Key Metrics:
    - Resolution status (resolved/unresolved/escalated)
    - Customer satisfaction (1-5 rating)
    - Response times (first response, total resolution)
    - Token usage and cost tracking
    - Message count breakdown (AI vs human)

    Indexes:
    - Composite: (conversation_id) - Link to conversation
    - Composite: (resolution_status, created_at) - Resolution analytics
    - Composite: (customer_satisfaction, created_at) - Satisfaction trends
    - Single: total_cost_usd - Cost analytics

    Example Usage:
    ```python
    analytics = ConversationAnalytics(
        conversation_id="conv_abc123",
        total_messages=12,
        ai_messages=10,
        human_messages=2,
        avg_confidence=0.87,
        resolution_status=ResolutionStatus.RESOLVED,
        customer_satisfaction=5,
        first_response_time_seconds=2,
        resolution_time_seconds=180,
        total_tokens=1250,
        total_cost_usd=0.025
    )
    ```
    """

    __tablename__ = "conversation_analytics"
    __table_args__ = (
        # Conversation linkage (most critical)
        Index("idx_analytics_conversation", "conversation_id"),

        # Resolution analytics
        Index("idx_analytics_resolution", "resolution_status", "created_at"),

        # Satisfaction tracking
        Index("idx_analytics_satisfaction", "customer_satisfaction", "created_at"),

        # Cost analytics
        Index("idx_analytics_cost", "total_cost_usd", "created_at"),

        # Performance analytics
        Index("idx_analytics_response_time", "first_response_time_seconds"),
        Index("idx_analytics_resolution_time", "resolution_time_seconds"),

        # Confidence tracking
        Index("idx_analytics_confidence", "avg_confidence"),

        {"schema": "ai"}
    )

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique analytics record identifier (UUID)"
    )

    conversation_id = Column(
        String(100),
        ForeignKey("ai.conversations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One analytics record per conversation
        comment="Parent conversation ID (CASCADE delete)"
    )

    # ========================================================================
    # MESSAGE COUNTS
    # ========================================================================

    total_messages = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total messages in conversation"
    )

    ai_messages = Column(
        Integer,
        nullable=False,
        default=0,
        comment="AI-generated messages (assistant role)"
    )

    human_messages = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Human agent messages (after escalation)"
    )

    # ========================================================================
    # QUALITY SCORES
    # ========================================================================

    avg_confidence = Column(
        Float,
        nullable=True,
        comment="Average AI confidence across all messages (0.0-1.0)"
    )

    resolution_status = Column(
        String(20),
        nullable=True,
        comment="Resolution status (resolved/unresolved/escalated/abandoned)"
    )

    customer_satisfaction = Column(
        Integer,
        nullable=True,
        comment="""
        Customer satisfaction rating (1-5):
        5 = Very satisfied
        4 = Satisfied
        3 = Neutral
        2 = Dissatisfied
        1 = Very dissatisfied
        NULL = No rating provided
        """
    )

    # ========================================================================
    # TIMING METRICS
    # ========================================================================

    first_response_time_seconds = Column(
        Integer,
        nullable=True,
        comment="Time from first user message to first AI response (seconds)"
    )

    resolution_time_seconds = Column(
        Integer,
        nullable=True,
        comment="Time from conversation start to resolution/closure (seconds)"
    )

    # ========================================================================
    # COST TRACKING
    # ========================================================================

    total_tokens = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total tokens consumed (input + output)"
    )

    total_cost_usd = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Total cost in USD (calculated from token usage)"
    )

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Analytics record creation timestamp"
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Last update timestamp (recalculated metrics)"
    )


# ============================================================================
# AI USAGE MODEL
# ============================================================================


class AIUsage(Base):
    """
    Detailed AI usage tracking per conversation.

    Schema: ai.ai_usage

    Business Logic:
    1. Track model usage per conversation
    2. Calculate costs (token-based pricing)
    3. Support multi-model deployments
    4. Enable usage analytics and ROI reporting
    5. Detect cost anomalies

    Key Features:
    - Per-model tracking (GPT-4, GPT-3.5, Llama-3)
    - Token breakdown (input vs output)
    - Cost calculation (model-specific pricing)
    - Performance metrics (response time)
    - Relationship to conversation

    Indexes:
    - Composite: (conversation_id, created_at) - Usage history
    - Composite: (model_name, created_at) - Model analytics
    - Single: total_cost_usd - Cost queries

    Example Usage:
    ```python
    usage = AIUsage(
        conversation_id="conv_abc123",
        model_name="gpt-4-turbo-preview",
        input_tokens=500,
        output_tokens=300,
        total_tokens=800,
        cost_usd=0.016,  # GPT-4 pricing
        response_time_ms=1200
    )
    ```
    """

    __tablename__ = "ai_usage"
    __table_args__ = (
        # Conversation usage history
        Index("idx_usage_conversation", "conversation_id", "created_at"),

        # Model analytics
        Index("idx_usage_model", "model_name", "created_at"),

        # Cost analytics
        Index("idx_usage_cost", "cost_usd", "created_at"),

        # Performance analytics
        Index("idx_usage_performance", "response_time_ms"),

        {"schema": "ai"}
    )

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique usage record identifier (UUID)"
    )

    conversation_id = Column(
        String(100),
        ForeignKey("ai.conversations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent conversation ID (CASCADE delete)"
    )

    # ========================================================================
    # MODEL INFORMATION
    # ========================================================================

    model_name = Column(
        String(50),
        nullable=False,
        comment="""
        AI model used:
        - gpt-4-turbo-preview
        - gpt-3.5-turbo
        - llama-3-8b-instruct
        - claude-3-sonnet
        """
    )

    # ========================================================================
    # TOKEN USAGE
    # ========================================================================

    input_tokens = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Input tokens (prompt + context)"
    )

    output_tokens = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Output tokens (generated response)"
    )

    total_tokens = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total tokens (input + output)"
    )

    # ========================================================================
    # COST TRACKING
    # ========================================================================

    cost_usd = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="""
        Cost in USD (calculated from tokens):
        GPT-4 Turbo: $0.01/1K input, $0.03/1K output
        GPT-3.5 Turbo: $0.0005/1K input, $0.0015/1K output
        Llama-3: Free (local model)
        """
    )

    # ========================================================================
    # PERFORMANCE METRICS
    # ========================================================================

    response_time_ms = Column(
        Integer,
        nullable=True,
        comment="API response time in milliseconds"
    )

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Usage record creation timestamp"
    )

    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================

    conversation = relationship(
        "UnifiedConversation",
        back_populates="usage_records"
    )


# ============================================================================
# TRAINING DATA MODEL
# ============================================================================


class TrainingData(Base):
    """
    High-quality training data collection for model improvement.

    Schema: ai.training_data

    Business Logic:
    1. Collect high-quality AI responses
    2. Include human corrections/feedback
    3. Support fine-tuning pipelines
    4. Enable shadow learning comparisons
    5. Build domain-specific training datasets

    Selection Criteria:
    - High customer satisfaction (4-5 rating)
    - High AI confidence (>0.8)
    - Positive human feedback (thumbs up)
    - Human-corrected responses (learn from mistakes)

    Key Features:
    - Source tracking (conversation, message)
    - Human feedback integration
    - Export-ready format (JSONL compatible)
    - Quality indicators (confidence, satisfaction)
    - Categorization (booking, menu, support)

    Indexes:
    - Composite: (is_approved, created_at) - Approved data for export
    - Composite: (category, is_approved) - Category-specific datasets
    - Single: quality_score - High-quality filtering

    Example Usage:
    ```python
    training = TrainingData(
        conversation_id="conv_abc123",
        message_id="msg_xyz789",
        prompt="How do I book a hibachi chef?",
        response="To book a hibachi chef, visit...",
        human_correction=None,  # No correction needed
        quality_score=0.95,
        category="booking",
        is_approved=True,
        metadata={
            "customer_satisfaction": 5,
            "ai_confidence": 0.92,
            "human_feedback": "thumbs_up"
        }
    )
    ```
    """

    __tablename__ = "training_data"
    __table_args__ = (
        # Approved data for export
        Index("idx_training_approved", "is_approved", "created_at"),

        # Category-specific datasets
        Index("idx_training_category", "category", "is_approved"),

        # Quality filtering
        Index("idx_training_quality", "quality_score", "is_approved"),

        # Source tracking
        Index("idx_training_conversation", "conversation_id"),
        Index("idx_training_message", "message_id"),

        {"schema": "ai"}
    )

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique training data identifier (UUID)"
    )

    # ========================================================================
    # SOURCE TRACKING
    # ========================================================================

    conversation_id = Column(
        String(100),
        ForeignKey("ai.conversations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Source conversation ID (SET NULL on delete)"
    )

    message_id = Column(
        String(100),
        ForeignKey("ai.messages.id", ondelete="SET NULL"),
        nullable=True,
        comment="Source message ID (SET NULL on delete)"
    )

    # ========================================================================
    # TRAINING CONTENT
    # ========================================================================

    prompt = Column(
        Text,
        nullable=False,
        comment="User prompt/question (training input)"
    )

    response = Column(
        Text,
        nullable=False,
        comment="AI response (training output - original or corrected)"
    )

    human_correction = Column(
        Text,
        nullable=True,
        comment="""
        Human-corrected response (if original was wrong).
        NULL = original response was good
        Non-NULL = use this instead of 'response' field
        """
    )

    # ========================================================================
    # QUALITY INDICATORS
    # ========================================================================

    quality_score = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="""
        Overall quality score (0.0-1.0):
        Calculated from:
        - AI confidence
        - Customer satisfaction
        - Human feedback
        - Resolution status
        """
    )

    category = Column(
        String(100),
        nullable=True,
        comment="""
        Training data category:
        - booking (booking flow, availability)
        - menu (dishes, pricing)
        - support (general questions)
        - policy (refunds, cancellations)
        """
    )

    # ========================================================================
    # APPROVAL & METADATA
    # ========================================================================

    is_approved = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="""
        Human approval flag:
        True = Ready for training/export
        False = Needs review
        """
    )

    # Renamed from 'metadata' to 'training_metadata' to avoid SQLAlchemy reserved word
    training_metadata = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="""
        Additional metadata (JSONB):
        {
            "customer_satisfaction": 5,
            "ai_confidence": 0.92,
            "human_feedback": "thumbs_up",
            "model_used": "gpt-4-turbo",
            "tokens": 150
        }
        """
    )

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Training data collection timestamp"
    )

    approved_at = Column(
        DateTime,
        nullable=True,
        comment="Human approval timestamp"
    )

    approved_by = Column(
        String(255),
        nullable=True,
        comment="Admin ID who approved this training data"
    )
