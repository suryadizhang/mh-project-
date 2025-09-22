"""
Database models for MyHibachi AI Customer Support System
Supports multi-channel conversations, knowledge base, and self-learning
"""

import uuid
from datetime import datetime
from enum import Enum

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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ChannelType(str, Enum):
    """Channel types for multi-channel support"""

    WEBSITE = "website"
    SMS = "sms"
    VOICE = "voice"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    EMAIL = "email"


class ConversationStatus(str, Enum):
    """Conversation status for AI/Human handoff"""

    AI = "ai"
    HUMAN = "human"
    CLOSED = "closed"
    ESCALATED = "escalated"


class MessageRole(str, Enum):
    """Message roles in conversation"""

    USER = "user"
    AI = "ai"
    GPT = "gpt"
    HUMAN = "human"
    SYSTEM = "system"


def generate_uuid():
    return str(uuid.uuid4())


class Conversation(Base):
    """Conversation threads across all channels"""

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    channel = Column(String(20), nullable=False)  # ChannelType enum
    user_id = Column(String(255), nullable=False)  # External user identifier
    thread_id = Column(
        String(255), nullable=False
    )  # Channel-specific thread ID
    status = Column(
        String(20), default=ConversationStatus.AI.value
    )  # ConversationStatus enum

    # Metadata for different channels
    channel_metadata = Column(
        JSON, default=dict
    )  # Phone numbers, FB page IDs, etc.

    # Conversation lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    closed_at = Column(DateTime, nullable=True)

    # Human takeover tracking
    escalated_at = Column(DateTime, nullable=True)
    assigned_agent_id = Column(String(255), nullable=True)
    escalation_reason = Column(Text, nullable=True)

    # Relationships
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_conversation_user_channel", "user_id", "channel"),
        Index("idx_conversation_thread", "thread_id"),
        Index("idx_conversation_status", "status"),
        Index("idx_conversation_created", "created_at"),
    )


class Message(Base):
    """Individual messages within conversations"""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(
        String(36), ForeignKey("conversations.id"), nullable=False
    )

    # Message content
    role = Column(String(20), nullable=False)  # MessageRole enum
    text = Column(Text, nullable=False)

    # AI/GPT metadata
    confidence = Column(Float, nullable=True)  # AI confidence score
    model_used = Column(
        String(50), nullable=True
    )  # gpt-5-nano, gpt-4-1-mini, etc.
    tokens_in = Column(Integer, nullable=True)
    tokens_out = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)

    # Processing metadata
    processing_time_ms = Column(Integer, nullable=True)
    intent_classification = Column(String(50), nullable=True)
    kb_sources_used = Column(JSON, default=list)  # List of KB chunk IDs used

    # Message lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    edited_at = Column(DateTime, nullable=True)

    # Quality tracking for self-learning
    human_feedback = Column(
        String(20), nullable=True
    )  # thumbs_up, thumbs_down
    human_correction = Column(Text, nullable=True)
    is_training_data = Column(Boolean, default=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index("idx_message_conversation", "conversation_id"),
        Index("idx_message_role", "role"),
        Index("idx_message_created", "created_at"),
        Index("idx_message_confidence", "confidence"),
        Index("idx_message_training", "is_training_data"),
    )


class KnowledgeBaseChunk(Base):
    """Knowledge base chunks for retrieval-augmented generation"""

    __tablename__ = "kb_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Content
    title = Column(String(500), nullable=False)
    text = Column(Text, nullable=False)

    # Vector embeddings (using JSON for now, will be VECTOR in production with pgvector)
    vector = Column(
        JSON, nullable=True
    )  # Will be VECTOR(384) in production with pgvector

    # Categorization
    tags = Column(JSON, default=list)  # List of tags for categorization
    category = Column(String(100), nullable=True)
    source_type = Column(
        String(50), nullable=True
    )  # faq, policy, procedure, learned

    # Quality and usage tracking
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # Based on user feedback

    # Content lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Source tracking for learned content
    source_message_id = Column(String(36), nullable=True)
    created_by_agent_id = Column(String(255), nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_kb_category", "category"),
        Index("idx_kb_source_type", "source_type"),
        Index("idx_kb_updated", "updated_at"),
        Index("idx_kb_usage", "usage_count"),
    )


class EscalationRule(Base):
    """Rules for automatic escalation to human agents"""

    __tablename__ = "escalation_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Rule definition
    rule_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Trigger conditions
    keywords = Column(JSON, default=list)  # Keywords that trigger escalation
    confidence_threshold = Column(
        Float, nullable=True
    )  # Below this confidence
    sentiment_threshold = Column(
        Float, nullable=True
    )  # Below this sentiment score

    # Rule metadata
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # Higher number = higher priority

    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Indexes
    __table_args__ = (
        Index("idx_escalation_active", "is_active"),
        Index("idx_escalation_priority", "priority"),
    )


class ConversationAnalytics(Base):
    """Analytics and metrics for conversation quality"""

    __tablename__ = "conversation_analytics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(
        String(36), ForeignKey("conversations.id"), nullable=False
    )

    # Metrics
    total_messages = Column(Integer, default=0)
    ai_messages = Column(Integer, default=0)
    human_messages = Column(Integer, default=0)

    # Quality scores
    avg_confidence = Column(Float, nullable=True)
    resolution_status = Column(
        String(20), nullable=True
    )  # resolved, unresolved, escalated
    customer_satisfaction = Column(Integer, nullable=True)  # 1-5 rating

    # Timing metrics
    first_response_time_seconds = Column(Integer, nullable=True)
    resolution_time_seconds = Column(Integer, nullable=True)

    # Cost tracking
    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)

    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Indexes
    __table_args__ = (
        Index("idx_analytics_conversation", "conversation_id"),
        Index("idx_analytics_resolution", "resolution_status"),
        Index("idx_analytics_satisfaction", "customer_satisfaction"),
    )


class TrainingData(Base):
    """High-quality Q&A pairs for model fine-tuning and knowledge base updates"""

    __tablename__ = "training_data"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Training pair
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

    # Context and metadata
    tags = Column(JSON, default=list)
    intent = Column(String(100), nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Source tracking
    source_type = Column(
        String(50), nullable=False
    )  # gpt_answer, human_answer, imported
    source_conversation_id = Column(String(36), nullable=True)
    source_message_id = Column(String(36), nullable=True)

    # Quality flags
    human_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    quality_score = Column(Float, nullable=True)  # Based on usage and feedback

    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_used_at = Column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_training_intent", "intent"),
        Index("idx_training_source", "source_type"),
        Index("idx_training_verified", "human_verified"),
        Index("idx_training_active", "is_active"),
        Index("idx_training_quality", "quality_score"),
    )
