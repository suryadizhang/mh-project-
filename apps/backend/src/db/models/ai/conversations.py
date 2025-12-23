"""
Unified Conversation and Message Models - ai Schema

This module provides unified models for all conversation types across multiple channels.
Merges the best features from:
- AIConversation (emotion tracking, memory backend)
- Conversation (multi-channel support, human escalation, shadow learning)

Industry Standard: Intercom/Zendesk pattern
- Single conversation model for all channels
- Channel-specific metadata in JSONB
- Emotion tracking for customer engagement
- Human escalation for quality assurance
- Shadow learning for AI training

Business Requirements:
- Support all communication channels (web, SMS, voice, social media)
- Track customer emotions for follow-ups
- Enable seamless AI-to-human handoff
- Collect training data for model improvement
- Provide analytics and usage tracking

Schema: ai (dedicated namespace for AI features)
Tables: conversations, messages

Migration Path:
- Data from public.ai_conversations → ai.conversations
- Data from public.conversations → ai.conversations (if exists)
- Unified schema prevents duplication
"""

from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import (
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

# MIGRATED: from models.base → ...base_class (3 levels up from ai/)
from ...base_class import Base


# ============================================================================
# ENUMS - Shared across conversation and message models
# ============================================================================


class ChannelType(str, Enum):
    """
    Communication channels supported by My Hibachi.

    Business Context:
    - WEB: Customer website chat widget
    - SMS: Two-way SMS conversations
    - VOICE: Phone calls (transcribed to text)
    - FACEBOOK: Facebook Messenger
    - INSTAGRAM: Instagram DMs
    - EMAIL: Email conversations
    - WHATSAPP: WhatsApp Business API (future)
    """

    WEB = "web"
    SMS = "sms"
    VOICE = "voice"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class ConversationStatus(str, Enum):
    """
    Conversation lifecycle status.

    Business Context:
    - ACTIVE: Ongoing conversation with AI
    - ESCALATED: Transferred to human agent
    - CLOSED: Conversation ended (resolved or timeout)
    - ARCHIVED: Historical conversation (retention)
    """

    ACTIVE = "active"
    ESCALATED = "escalated"
    CLOSED = "closed"
    ARCHIVED = "archived"


class MessageRole(str, Enum):
    """
    Message sender role in conversation.

    Business Context:
    - USER: Customer message
    - ASSISTANT: AI agent response
    - SYSTEM: System notifications (booking confirmed, etc.)
    - HUMAN: Human agent response (after escalation)
    - TOOL: Function call result (internal)
    """

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    HUMAN = "human"
    TOOL = "tool"


class EmotionTrend(str, Enum):
    """
    Customer emotion trend over conversation.

    Business Context:
    - IMPROVING: Customer getting happier (good sign)
    - STABLE: Neutral throughout
    - DECLINING: Customer getting frustrated (escalate?)
    """

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class EmotionLabel(str, Enum):
    """
    Simplified emotion classification.

    Business Context:
    - POSITIVE: Happy, satisfied customer
    - NEUTRAL: Informational conversation
    - NEGATIVE: Frustrated, upset (trigger follow-up)
    """

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


# ============================================================================
# UNIFIED CONVERSATION MODEL
# ============================================================================


class UnifiedConversation(Base):
    """
    Unified conversation model for all channels.

    Merges features from:
    - AIConversation: emotion tracking, memory backend
    - Conversation: multi-channel, escalation, shadow learning

    Schema: ai.conversations

    Business Logic:
    1. Single source of truth for all conversations
    2. Supports all communication channels
    3. Tracks customer emotions for engagement
    4. Enables AI-to-human escalation
    5. Collects data for shadow learning
    6. Provides analytics foundation

    Key Features:
    - Channel-agnostic design (JSONB metadata per channel)
    - Emotion tracking (average score, trend, escalation triggers)
    - Human handoff (escalation tracking, agent assignment)
    - Shadow learning (student/teacher responses, RLHF scores)
    - Performance indexes (user lookups, emotion queries, analytics)

    Indexes:
    - Composite: (user_id, is_active) - Active conversations by user
    - Composite: (channel, status) - Channel analytics
    - Composite: (average_emotion_score, emotion_trend) - Emotion queries
    - GIN: context, channel_metadata - JSONB searches
    - Single: last_message_at, escalated_at, closed_at - Time-based queries
    """

    __tablename__ = "conversations"
    __table_args__ = (
        # User and status lookups (most common queries)
        Index("idx_conversations_user_active", "user_id", "is_active"),
        Index("idx_conversations_user_channel", "user_id", "channel"),
        # Channel and status analytics
        Index("idx_conversations_channel_status", "channel", "status"),
        Index("idx_conversations_status_updated", "status", "updated_at"),
        # Emotion-based queries (for scheduler and analytics)
        Index("idx_conversations_emotion_trend", "average_emotion_score", "emotion_trend"),
        Index("idx_conversations_emotion_active", "average_emotion_score", "is_active"),
        # Escalation tracking
        Index("idx_conversations_escalated", "escalated", "escalated_at"),
        Index("idx_conversations_assigned_agent", "assigned_agent_id", "status"),
        # Time-based queries (inactive detection, analytics)
        Index("idx_conversations_last_message", "last_message_at"),
        Index("idx_conversations_created", "created_at"),
        Index("idx_conversations_closed", "closed_at"),
        # JSONB indexes for flexible queries
        Index("idx_conversations_context", "context", postgresql_using="gin"),
        Index("idx_conversations_channel_metadata", "channel_metadata", postgresql_using="gin"),
        # Shadow learning lookups
        Index("idx_conversations_route_decision", "route_decision", "confidence_score"),
        # Foreign key index
        Index("idx_conversations_customer_id", "customer_id"),
        {"schema": "ai"},
    )

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================

    id = Column(
        String(100),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique conversation identifier (UUID)",
    )

    # ========================================================================
    # USER & CHANNEL IDENTIFICATION
    # ========================================================================

    user_id = Column(
        String(255),
        nullable=True,  # Nullable for anonymous users
        index=True,
        comment="User identifier (from auth system or anonymous session)",
    )

    customer_id = Column(
        String(36),
        ForeignKey("core.customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Link to customer record (if identified)",
    )

    channel = Column(
        String(20),
        nullable=False,
        default=ChannelType.WEB.value,
        comment="Communication channel (web/sms/voice/facebook/instagram/email)",
    )

    thread_id = Column(
        String(255),
        nullable=True,
        comment="Channel-specific thread ID (SMS phone number, FB thread, etc.)",
    )

    channel_metadata = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Channel-specific metadata (phone numbers, FB page IDs, email addresses)",
    )

    # ========================================================================
    # CONVERSATION STATUS & LIFECYCLE
    # ========================================================================

    status = Column(
        String(20),
        nullable=False,
        default=ConversationStatus.ACTIVE.value,
        comment="Conversation status (active/escalated/closed/archived)",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Quick active/inactive flag (optimized queries)",
    )

    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, comment="Conversation start timestamp"
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Last update timestamp (any change)",
    )

    last_message_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Last message timestamp (for inactive detection)",
    )

    closed_at = Column(DateTime, nullable=True, comment="Conversation closure timestamp")

    closed_reason = Column(
        String(100),
        nullable=True,
        comment="Closure reason (resolved/timeout/customer_ended/escalated)",
    )

    # ========================================================================
    # CONVERSATION CONTEXT & METADATA
    # ========================================================================

    message_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total messages in conversation (performance optimization)",
    )

    context = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Conversation context (booking details, customer preferences, session data)",
    )

    # ========================================================================
    # EMOTION TRACKING (Customer Engagement)
    # ========================================================================

    average_emotion_score = Column(
        Float,
        nullable=True,
        comment="Average emotion score across all messages (0.0=negative, 1.0=positive)",
    )

    emotion_trend = Column(
        String(20), nullable=True, comment="Emotion trend (improving/stable/declining)"
    )

    # ========================================================================
    # HUMAN ESCALATION (Quality Assurance)
    # ========================================================================

    escalated = Column(
        Boolean, nullable=False, default=False, comment="Escalated to human agent flag"
    )

    escalated_at = Column(DateTime, nullable=True, comment="Escalation timestamp")

    assigned_agent_id = Column(
        String(255), nullable=True, comment="Human agent ID (after escalation)"
    )

    escalation_reason = Column(
        Text,
        nullable=True,
        comment="Why conversation was escalated (emotion/complexity/customer_request)",
    )

    # ========================================================================
    # SHADOW LEARNING (AI Training)
    # ========================================================================

    confidence_score = Column(
        Float, nullable=True, default=1.0, comment="AI confidence score (for routing decisions)"
    )

    route_decision = Column(
        String(50),
        nullable=True,
        default="teacher",
        comment="Routing decision (student/teacher/human) for shadow learning",
    )

    student_response = Column(
        Text, nullable=True, comment="Student model response (local Llama-3) for comparison"
    )

    teacher_response = Column(
        Text, nullable=True, comment="Teacher model response (OpenAI GPT-4) for training"
    )

    reward_score = Column(
        Float, nullable=True, comment="RLHF reward score (human feedback on conversation quality)"
    )

    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================

    messages = relationship(
        "UnifiedMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="UnifiedMessage.timestamp",
    )

    usage_records = relationship(
        "AIUsage", back_populates="conversation", cascade="all, delete-orphan"
    )

    # Note: Customer relationship defined in customers table
    # customer = relationship("Customer", back_populates="conversations")


# ============================================================================
# UNIFIED MESSAGE MODEL
# ============================================================================


class UnifiedMessage(Base):
    """
    Unified message model for all channels.

    Merges features from:
    - AIMessage: emotion tracking, token tracking, tool calls
    - Message: confidence scores, KB sources, human feedback

    Schema: ai.messages

    Business Logic:
    1. Store all messages from all channels
    2. Track AI performance (tokens, cost, model used)
    3. Track customer emotions (per message)
    4. Enable self-learning (human feedback, corrections)
    5. Support tool use (function calls, integrations)
    6. Provide training data for shadow learning

    Key Features:
    - Multi-channel support (same schema for all channels)
    - Dual content fields (content for AI, text for display)
    - Emotion tracking per message
    - Token and cost tracking (usage analytics)
    - Knowledge base source tracking (transparency)
    - Human feedback collection (training data)
    - Tool call tracking (agent capabilities)

    Indexes:
    - Composite: (conversation_id, timestamp) - Message history
    - Composite: (conversation_id, emotion_score, timestamp) - Emotion history
    - Single: role, emotion_score, is_training_data - Analytics
    - GIN: message_metadata, kb_sources_used, tool_calls - JSONB searches
    """

    __tablename__ = "messages"
    __table_args__ = (
        # Conversation message lookups (most common)
        Index("idx_messages_conversation_timestamp", "conversation_id", "timestamp"),
        Index("idx_messages_conversation_role", "conversation_id", "role"),
        # Emotion history (for scheduler emotion-based follow-ups)
        Index("idx_messages_emotion_history", "conversation_id", "emotion_score", "timestamp"),
        Index("idx_messages_emotion_label", "emotion_label"),
        # Analytics queries
        Index("idx_messages_role_created", "role", "timestamp"),
        Index("idx_messages_model_used", "model_used", "timestamp"),
        Index("idx_messages_channel", "channel"),
        # Training data collection
        Index("idx_messages_training_data", "is_training_data", "timestamp"),
        Index("idx_messages_human_feedback", "human_feedback", "timestamp"),
        # JSONB indexes for complex queries
        Index("idx_messages_metadata", "message_metadata", postgresql_using="gin"),
        Index("idx_messages_kb_sources", "kb_sources_used", postgresql_using="gin"),
        Index("idx_messages_tool_calls", "tool_calls", postgresql_using="gin"),
        Index("idx_messages_detected_emotions", "detected_emotions", postgresql_using="gin"),
        {"schema": "ai"},
    )

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================

    id = Column(
        String(100),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique message identifier (UUID)",
    )

    # ========================================================================
    # CONVERSATION RELATIONSHIP
    # ========================================================================

    conversation_id = Column(
        String(100),
        ForeignKey("ai.conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent conversation ID (CASCADE delete)",
    )

    # ========================================================================
    # MESSAGE CONTENT
    # ========================================================================

    role = Column(
        String(20), nullable=False, comment="Message role (user/assistant/system/human/tool)"
    )

    content = Column(
        Text, nullable=False, comment="Message content (primary field for AI processing)"
    )

    text = Column(
        Text, nullable=True, comment="Display text (may differ from content for tool calls)"
    )

    channel = Column(
        String(20),
        nullable=False,
        default=ChannelType.WEB.value,
        comment="Message channel (inherited from conversation)",
    )

    # ========================================================================
    # TIMESTAMPS
    # ========================================================================

    timestamp = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="Message creation timestamp",
    )

    edited_at = Column(
        DateTime, nullable=True, comment="Message edit timestamp (if edited by human)"
    )

    # ========================================================================
    # METADATA & CONTEXT
    # ========================================================================

    message_metadata = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Message-specific metadata (attachments, formatting, channel-specific data)",
    )

    # ========================================================================
    # EMOTION TRACKING
    # ========================================================================

    emotion_score = Column(
        Float, nullable=True, comment="Emotion score for this message (0.0=negative, 1.0=positive)"
    )

    emotion_label = Column(
        String(20), nullable=True, comment="Simplified emotion label (positive/neutral/negative)"
    )

    detected_emotions = Column(
        JSONB, nullable=True, comment="Detailed emotion detection (joy, anger, sadness, fear, etc.)"
    )

    # ========================================================================
    # AI PERFORMANCE TRACKING
    # ========================================================================

    model_used = Column(
        String(50),
        nullable=True,
        comment="AI model used (gpt-4-turbo, gpt-3.5-turbo, llama-3-8b, etc.)",
    )

    confidence = Column(Float, nullable=True, comment="AI confidence score (0.0-1.0)")

    input_tokens = Column(
        Integer, nullable=True, comment="Input tokens consumed (for cost tracking)"
    )

    output_tokens = Column(
        Integer, nullable=True, comment="Output tokens generated (for cost tracking)"
    )

    cost_usd = Column(Float, nullable=True, comment="Message cost in USD (calculated from tokens)")

    processing_time_ms = Column(
        Integer, nullable=True, comment="Processing time in milliseconds (performance monitoring)"
    )

    # ========================================================================
    # KNOWLEDGE BASE & INTENT
    # ========================================================================

    intent_classification = Column(
        String(50), nullable=True, comment="Detected intent (booking/menu/pricing/complaint/etc.)"
    )

    kb_sources_used = Column(
        JSONB,
        nullable=True,
        default=list,
        comment="Knowledge base chunk IDs used (for transparency and training)",
    )

    # ========================================================================
    # TOOL USE (Function Calling)
    # ========================================================================

    tool_calls = Column(
        JSONB, nullable=True, comment="Tool/function calls made by AI (structured data)"
    )

    tool_results = Column(JSONB, nullable=True, comment="Tool call results (structured data)")

    # ========================================================================
    # HUMAN FEEDBACK (Training Data)
    # ========================================================================

    human_feedback = Column(
        String(20), nullable=True, comment="Human feedback (thumbs_up/thumbs_down/neutral)"
    )

    human_correction = Column(
        Text, nullable=True, comment="Human correction of AI response (for training)"
    )

    is_training_data = Column(
        Boolean, nullable=False, default=False, comment="Flag for high-quality training data"
    )

    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================

    conversation = relationship("UnifiedConversation", back_populates="messages")
