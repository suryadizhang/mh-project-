"""
Knowledge Base and Escalation Models - ai Schema

This module handles knowledge base management and escalation rules.

Business Requirements:
- RAG (Retrieval-Augmented Generation) knowledge base
- FAQ, policy, procedure documentation
- Learned content from high-quality interactions
- Automatic escalation to human agents
- Quality tracking (usage, success rates)

Schema: ai
Tables: kb_chunks, escalation_rules
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
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB

# MIGRATED: from models.base → ...base_class (3 levels up from ai/)
from ...base_class import Base


# ============================================================================
# ENUMS
# ============================================================================


class KnowledgeSourceType(str, Enum):
    """
    Knowledge base source types.

    Business Context:
    - FAQ: Frequently asked questions
    - POLICY: Company policies (refunds, cancellations)
    - PROCEDURE: Step-by-step procedures (booking, payment)
    - LEARNED: High-quality AI responses marked for reuse
    - MENU: Menu items and pricing information
    - CUSTOM: Custom admin-created content
    """

    FAQ = "faq"
    POLICY = "policy"
    PROCEDURE = "procedure"
    LEARNED = "learned"
    MENU = "menu"
    CUSTOM = "custom"


# ============================================================================
# KNOWLEDGE BASE CHUNK MODEL
# ============================================================================


class KnowledgeBaseChunk(Base):
    """
    Knowledge base chunks for Retrieval-Augmented Generation (RAG).

    Schema: ai.kb_chunks

    Business Logic:
    1. Store FAQ, policies, procedures for AI to reference
    2. Vector embeddings for semantic search
    3. Track usage and success rates
    4. Learn from high-quality interactions
    5. Support hierarchical categorization

    Vector Search:
    - Uses pgvector extension (VECTOR(384) for embeddings)
    - Cosine similarity search for relevant chunks
    - Hybrid search (keyword + semantic)

    Quality Tracking:
    - usage_count: How many times chunk was used
    - success_rate: Customer satisfaction when this chunk was used
    - Auto-deprecate low-performing chunks

    Key Features:
    - Vector embeddings (pgvector extension required)
    - Tagging system (flexible categorization)
    - Source tracking (learned from message_id)
    - Quality metrics (usage, success rate)
    - Lifecycle management (created, updated)

    Indexes:
    - Single: category, source_type, updated_at, usage_count
    - Vector: vector (pgvector IVFFlat or HNSW index)
    - GIN: tags (JSONB array search)

    Example Usage:
    ```python
    # FAQ chunk
    chunk = KnowledgeBaseChunk(
        id=str(uuid.uuid4()),
        title="How to book a hibachi chef?",
        text="To book a hibachi chef, visit our website...",
        vector=[0.1, 0.2, ...],  # 384-dimensional embedding
        tags=["booking", "how-to", "getting-started"],
        category="booking",
        source_type=KnowledgeSourceType.FAQ,
        usage_count=0,
        success_rate=0.0
    )
    ```
    """

    __tablename__ = "kb_chunks"
    __table_args__ = (
        # Category and source type lookups
        Index("idx_kb_category", "category"),
        Index("idx_kb_source_type", "source_type"),
        # Quality and usage tracking
        Index("idx_kb_usage_success", "usage_count", "success_rate"),
        Index("idx_kb_updated", "updated_at"),
        # Tagging system (JSONB array search)
        Index("idx_kb_tags", "tags", postgresql_using="gin"),
        # Source tracking (learned content)
        Index("idx_kb_source_message", "source_message_id"),
        # TODO: Vector index (requires pgvector extension)
        # Index("idx_kb_vector", "vector", postgresql_using="ivfflat")
        # Or: postgresql_using="hnsw" for better performance
        {"schema": "ai"},
    )

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique chunk identifier (UUID)",
    )

    # ========================================================================
    # CONTENT
    # ========================================================================

    title = Column(String(500), nullable=False, comment="Chunk title (question, heading, topic)")

    text = Column(Text, nullable=False, comment="Chunk content (answer, documentation, procedure)")

    vector = Column(
        JSON,
        nullable=True,
        comment="""
        Vector embedding (384-dimensional for all-MiniLM-L6-v2).
        TODO: Change to VECTOR(384) when pgvector extension is enabled.
        Current: JSON array [0.1, 0.2, ..., 0.384]
        Future: VECTOR(384) with IVFFlat or HNSW index
        """,
    )

    # ========================================================================
    # CATEGORIZATION
    # ========================================================================

    tags = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="""
        Tag array for flexible categorization:
        ["booking", "pricing", "menu", "cancellation", "refund"]
        GIN index for fast array searches.
        """,
    )

    category = Column(
        String(100),
        nullable=True,
        comment="""
        Primary category for hierarchical organization:
        - booking (booking flow, availability)
        - menu (dishes, pricing, ingredients)
        - policy (refunds, cancellations, guarantees)
        - procedure (step-by-step guides)
        - general (company info, contact)
        """,
    )

    source_type = Column(
        String(50), nullable=True, comment="Source type (faq/policy/procedure/learned/menu/custom)"
    )

    # ========================================================================
    # QUALITY & USAGE TRACKING
    # ========================================================================

    usage_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of times this chunk was used in AI responses",
    )

    success_rate = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="""
        Success rate based on customer feedback (0.0-1.0).
        Calculated from: positive_feedback / total_usage
        Auto-deprecate chunks with low success rates (<0.5)
        """,
    )

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, comment="Chunk creation timestamp"
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Last update timestamp",
    )

    # ========================================================================
    # SOURCE TRACKING (Learned Content)
    # ========================================================================

    source_message_id = Column(
        String(36),
        nullable=True,
        comment="""
        Source message ID for learned content.
        If this chunk was learned from a high-quality AI response,
        store the message_id here for traceability.
        """,
    )

    created_by_agent_id = Column(
        String(255),
        nullable=True,
        comment="""
        Agent/admin ID who created this chunk.
        - Admin ID: Manual creation
        - 'ai_learning': Automatically learned from conversations
        """,
    )


# ============================================================================
# ESCALATION RULE MODEL
# ============================================================================


class EscalationRule(Base):
    """
    Rules for automatic escalation to human agents.

    Schema: ai.escalation_rules

    Business Logic:
    1. Define triggers for escalation (keywords, low confidence, negative sentiment)
    2. Priority-based rule evaluation (higher priority first)
    3. Enable/disable rules without deletion
    4. Prevent customer frustration through proactive escalation

    Escalation Triggers:
    - Keywords: "speak to human", "manager", "complaint", "angry"
    - Confidence: AI confidence below threshold (e.g., <0.6)
    - Sentiment: Customer emotion score below threshold (e.g., <0.3)
    - Combination: Multiple triggers (AND/OR logic)

    Key Features:
    - Keyword matching (case-insensitive)
    - Confidence thresholds
    - Sentiment/emotion thresholds
    - Priority ordering (high-priority rules checked first)
    - Active/inactive toggle (no deletion needed)

    Indexes:
    - Composite: (is_active, priority) - Active rules in priority order
    - Single: rule_name (unique constraint)

    Example Rules:
    ```python
    # Keyword-based escalation
    rule1 = EscalationRule(
        rule_name="explicit_human_request",
        description="Customer explicitly asks for human agent",
        keywords=["speak to human", "talk to person", "real person", "manager"],
        is_active=True,
        priority=10  # Highest priority
    )

    # Confidence-based escalation
    rule2 = EscalationRule(
        rule_name="low_confidence",
        description="AI confidence below 60%",
        confidence_threshold=0.6,
        is_active=True,
        priority=5
    )

    # Sentiment-based escalation
    rule3 = EscalationRule(
        rule_name="negative_sentiment",
        description="Customer emotion score below 30%",
        sentiment_threshold=0.3,
        is_active=True,
        priority=8
    )
    ```
    """

    __tablename__ = "escalation_rules"
    __table_args__ = (
        # Active rules in priority order (most critical query)
        Index("idx_escalation_active_priority", "is_active", "priority"),
        # Rule name uniqueness (business requirement)
        # Enforced at database level + application level
        # Lifecycle tracking
        Index("idx_escalation_updated", "updated_at"),
        {"schema": "ai"},
    )

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique rule identifier (UUID)",
    )

    # ========================================================================
    # RULE DEFINITION
    # ========================================================================

    rule_name = Column(
        String(100),
        nullable=False,
        unique=True,
        comment="""
        Rule name (unique identifier):
        - explicit_human_request
        - low_confidence
        - negative_sentiment
        - complex_query
        - payment_issue
        """,
    )

    description = Column(
        Text, nullable=True, comment="Human-readable description of what triggers this rule"
    )

    # ========================================================================
    # TRIGGER CONDITIONS
    # ========================================================================

    keywords = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="""
        Keywords that trigger escalation (case-insensitive):
        ["speak to human", "manager", "complaint", "angry", "frustrated"]
        Empty array = no keyword trigger
        """,
    )

    confidence_threshold = Column(
        Float,
        nullable=True,
        comment="""
        Escalate if AI confidence below this threshold (0.0-1.0).
        Example: 0.6 = escalate if confidence <60%
        NULL = no confidence trigger
        """,
    )

    sentiment_threshold = Column(
        Float,
        nullable=True,
        comment="""
        Escalate if emotion score below this threshold (0.0-1.0).
        Example: 0.3 = escalate if emotion <30% (negative)
        NULL = no sentiment trigger
        """,
    )

    # ========================================================================
    # RULE METADATA
    # ========================================================================

    is_active = Column(
        Boolean, nullable=False, default=True, comment="Active/inactive toggle (no deletion needed)"
    )

    priority = Column(
        Integer,
        nullable=False,
        default=1,
        comment="""
        Rule priority (higher number = higher priority).
        Rules evaluated in descending priority order:
        - 10: Critical (explicit human request)
        - 8: High (severe negative sentiment)
        - 5: Medium (low confidence)
        - 1: Low (general fallbacks)
        """,
    )

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, comment="Rule creation timestamp"
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Last update timestamp",
    )
