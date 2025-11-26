"""
AI Schema Models - Consolidated Export

This module provides a unified entry point for all AI-related database models.
All tables use schema='ai' for clear separation from business logic.

Architecture:
- Schema: ai (dedicated namespace for AI/ML features)
- Organization: Business function based (conversations, engagement, knowledge, analytics)
- Implementation: Models defined in ai/ subdirectory, re-exported here

Business Domains:
1. Conversations: Multi-channel customer conversations (web, SMS, voice, social)
2. Engagement: Automated follow-ups and re-engagement campaigns
3. Knowledge: RAG knowledge base and escalation rules
4. Analytics: Usage tracking, metrics, training data collection
5. Shadow Learning: AI training, RLHF scoring, teacher-student pairs

Enterprise Features:
- Dedicated schema for isolation and scalability
- Optimized indexes for AI workloads
- JSONB for flexible metadata storage
- Comprehensive audit trail (created_at, updated_at)
- Support for horizontal scaling (separate DB if needed)

Schema Declaration:
All models use: __table_args__ = {"schema": "ai"}

Migration Path:
- Phase 0: Database cleanup (64 migrations, merged heads)
- Phase 1A: Critical fixes (Bug #13, GSM, timezone bugs)
- Phase 1B: Multi-schema foundation (THIS FILE)
- Phase 2: AI agents (distance, menu, pricing, booking, availability)

Usage Example:
```python
from db.models.ai import (
    UnifiedConversation,
    UnifiedMessage,
    CustomerEngagementFollowUp,
    KnowledgeBaseChunk,
    AIUsage,
)

# Create conversation
conversation = UnifiedConversation(
    user_id="user_123",
    channel=ChannelType.WEB,
    status=ConversationStatus.ACTIVE,
)
session.add(conversation)
```

Note: All model definitions are in ai/ subdirectory.
This file serves as the schema-level export point for Phase 1B validation.
"""

# Conversations - Multi-channel customer conversations
from db.models.ai.conversations import (
    UnifiedConversation,
    UnifiedMessage,
    ChannelType,
    ConversationStatus,
    MessageRole,
    EmotionTrend,
    EmotionLabel,
)

# Engagement - Automated follow-ups and campaigns
from db.models.ai.engagement import (
    CustomerEngagementFollowUp,
    FollowUpTriggerType,
    FollowUpStatus,
    calculate_post_event_schedule_time,
    calculate_reengagement_schedule_time,
    should_send_followup,
)

# Knowledge - RAG knowledge base and escalation
from db.models.ai.knowledge import (
    KnowledgeBaseChunk,
    EscalationRule,
    KnowledgeSourceType,
)

# Analytics - Usage tracking and training data
from db.models.ai.analytics import (
    ConversationAnalytics,
    AIUsage,
    TrainingData,
    ResolutionStatus,
)

# Shadow Learning - AI training and RLHF
from db.models.ai.shadow_learning import (
    AITutorPair,
    AIRLHFScore,
    AIExportJob,
    ModelType,
    ExportStatus,
)


__all__ = [
    # ========================================================================
    # CONVERSATIONS (Multi-channel customer conversations)
    # ========================================================================
    "UnifiedConversation",
    "UnifiedMessage",
    "ChannelType",
    "ConversationStatus",
    "MessageRole",
    "EmotionTrend",
    "EmotionLabel",
    # ========================================================================
    # ENGAGEMENT (Automated follow-ups and campaigns)
    # ========================================================================
    "CustomerEngagementFollowUp",
    "FollowUpTriggerType",
    "FollowUpStatus",
    "calculate_post_event_schedule_time",
    "calculate_reengagement_schedule_time",
    "should_send_followup",
    # ========================================================================
    # KNOWLEDGE (RAG knowledge base and escalation)
    # ========================================================================
    "KnowledgeBaseChunk",
    "EscalationRule",
    "KnowledgeSourceType",
    # ========================================================================
    # ANALYTICS (Usage tracking and training data)
    # ========================================================================
    "ConversationAnalytics",
    "AIUsage",
    "TrainingData",
    "ResolutionStatus",
    # ========================================================================
    # SHADOW LEARNING (AI training and RLHF)
    # ========================================================================
    "AITutorPair",
    "AIRLHFScore",
    "AIExportJob",
    "ModelType",
    "ExportStatus",
]

# Schema metadata for Phase 1B validation
__schema__ = "ai"
__table_args__ = {"schema": "ai"}  # For validation detection
__version__ = "1.0.0"
__description__ = "AI Schema Models - Multi-channel conversations, engagement, knowledge, analytics, shadow learning"
