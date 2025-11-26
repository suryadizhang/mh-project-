"""
AI Models Package - ai Schema

This package contains all AI/ML-related database models organized by business function.

## Schema Organization (Industry Standard)

Following best practices from Stripe, Shopify, and Salesforce:
- Dedicated `ai` schema for all AI-related tables
- Clear separation from business logic (public schema)
- Optimized for AI workloads (dedicated connection pools)
- Independent backup/restore capabilities
- Secure permissions (AI service account access only)

## Package Structure

```
db/models/ai/
├── __init__.py              # This file - exports all models
├── conversations.py         # UnifiedConversation, UnifiedMessage (multi-channel)
├── engagement.py            # CustomerEngagementFollowUp (automated follow-ups)
├── knowledge.py             # KnowledgeBaseChunk, EscalationRule (RAG + escalation)
├── analytics.py             # ConversationAnalytics, AIUsage, TrainingData
└── shadow_learning.py       # AITutorPair, AIRLHFScore, AIExportJob
```

## Unified Conversation Model

**Problem Solved**: Previously had duplicate models (AIConversation vs Conversation)
**Solution**: Merged into UnifiedConversation with best features from both:
- ✅ Multi-channel support (web, SMS, voice, Facebook, Instagram, email)
- ✅ Emotion tracking for customer engagement
- ✅ Human escalation for quality assurance
- ✅ Shadow learning integration (student/teacher responses)
- ✅ Comprehensive analytics and usage tracking

## Business Requirements

### Customer Engagement
- Post-event follow-ups (24h after booking)
- Re-engagement campaigns (30+ days inactive)
- Emotion-based outreach (low emotion score recovery)
- Custom admin-scheduled messages

### Knowledge Management
- RAG (Retrieval-Augmented Generation) knowledge base
- FAQ, policies, procedures
- Learned content from high-quality interactions
- Automatic escalation rules

### Analytics & Training
- Conversation quality metrics
- AI performance tracking (tokens, cost, response time)
- Training data collection for model improvement
- Shadow learning (teacher-student comparison)
- RLHF scoring for production readiness

## Migration Path

### From Previous Models
- `public.ai_conversations` → `ai.conversations` (UnifiedConversation)
- `public.ai_messages` → `ai.messages` (UnifiedMessage)
- `scheduled_followups` → `ai.customer_engagement_followups`
- `conversations` → Merged into `ai.conversations` (unified)
- `messages` → Merged into `ai.messages` (unified)

### Data Preservation
All migrations preserve existing data:
1. Create ai schema
2. Create new unified tables
3. Migrate data from old tables
4. Keep old tables as *_legacy (rollback safety)
5. Update application imports
6. Test thoroughly
7. Remove legacy tables (after verification period)

## Usage Examples

### Create Conversation (Web Chat)
```python
from db.models.ai import UnifiedConversation, ChannelType

conversation = UnifiedConversation(
    id=str(uuid.uuid4()),
    user_id="user_123",
    channel=ChannelType.WEB,
    status=ConversationStatus.ACTIVE,
    context={"booking_id": "book_456", "event_date": "2025-12-01"}
)
session.add(conversation)
```

### Add Message with Emotion
```python
from db.models.ai import UnifiedMessage, MessageRole

message = UnifiedMessage(
    id=str(uuid.uuid4()),
    conversation_id=conversation.id,
    role=MessageRole.USER,
    content="I'm frustrated with the booking process",
    emotion_score=0.25,  # Low emotion (negative)
    emotion_label=EmotionLabel.NEGATIVE,
    detected_emotions={"frustration": 0.8, "anger": 0.3}
)
session.add(message)
```

### Schedule Follow-Up
```python
from db.models.ai import CustomerEngagementFollowUp, FollowUpTriggerType

followup = CustomerEngagementFollowUp(
    id=str(uuid.uuid4()),
    conversation_id=conversation.id,
    user_id="user_123",
    trigger_type=FollowUpTriggerType.EMOTION_BASED,
    trigger_data={"emotion_score": 0.25, "message_id": message.id},
    scheduled_at=datetime.now(timezone.utc) + timedelta(hours=1),
    status=FollowUpStatus.PENDING,
    template_id="emotion_recovery"
)
session.add(followup)
```

### Track AI Usage
```python
from db.models.ai import AIUsage

usage = AIUsage(
    conversation_id=conversation.id,
    model_name="gpt-4-turbo-preview",
    input_tokens=150,
    output_tokens=75,
    total_tokens=225,
    cost_usd=0.00675,  # GPT-4 pricing
    response_time_ms=1200
)
session.add(usage)
```

## Enterprise Features

### Performance
- Optimized indexes for all query patterns
- GIN indexes for JSONB fields
- Composite indexes for common joins
- Vector indexes for semantic search (pgvector)

### Scalability
- Dedicated schema (move to separate DB if needed)
- Partitioning support (by date for analytics)
- Connection pool optimization
- Read replicas ready

### Security
- Schema-level permissions
- Row-level security support
- Audit trail (created_at, updated_at)
- Soft delete support

### Observability
- Usage tracking per conversation
- Cost tracking per model
- Performance metrics (response time)
- Quality metrics (satisfaction, resolution)

## Dependencies

### Database Extensions
- PostgreSQL 12+ required
- pgvector extension (for semantic search) - OPTIONAL
  - `CREATE EXTENSION IF NOT EXISTS vector;`
  - Change KnowledgeBaseChunk.vector from JSON to VECTOR(384)

### Python Libraries
- SQLAlchemy 2.0+
- psycopg2 or asyncpg (database driver)
- alembic (migrations)

## Testing

### Unit Tests
```python
from db.models.ai import UnifiedConversation, UnifiedMessage

def test_conversation_creation():
    conversation = UnifiedConversation(
        id="test_123",
        user_id="user_456",
        channel="web"
    )
    assert conversation.status == ConversationStatus.ACTIVE.value
    assert conversation.is_active == True
```

### Integration Tests
```python
async def test_conversation_with_messages(session):
    conversation = UnifiedConversation(...)
    session.add(conversation)
    await session.commit()

    message = UnifiedMessage(conversation_id=conversation.id, ...)
    session.add(message)
    await session.commit()

    # Verify relationship
    messages = await session.execute(
        select(UnifiedMessage).where(UnifiedMessage.conversation_id == conversation.id)
    )
    assert len(messages.scalars().all()) == 1
```

## Support

For questions or issues:
1. Check model docstrings (comprehensive documentation)
2. Review business logic comments in each file
3. Consult migration files for data transformation logic
4. Contact: #mh-backend-dev channel
"""

# ============================================================================
# CONVERSATIONS MODULE
# ============================================================================

from .conversations import (
    # Models
    UnifiedConversation,
    UnifiedMessage,

    # Enums
    ChannelType,
    ConversationStatus,
    MessageRole,
    EmotionTrend,
    EmotionLabel,
)

# ============================================================================
# ENGAGEMENT MODULE
# ============================================================================

from .engagement import (
    # Models
    CustomerEngagementFollowUp,

    # Enums
    FollowUpTriggerType,
    FollowUpStatus,

    # Helper Functions
    calculate_post_event_schedule_time,
    calculate_reengagement_schedule_time,
    should_send_followup,
)

# ============================================================================
# KNOWLEDGE MODULE
# ============================================================================

from .knowledge import (
    # Models
    KnowledgeBaseChunk,
    EscalationRule,

    # Enums
    KnowledgeSourceType,
)

# ============================================================================
# ANALYTICS MODULE
# ============================================================================

from .analytics import (
    # Models
    ConversationAnalytics,
    AIUsage,
    TrainingData,

    # Enums
    ResolutionStatus,
)

# ============================================================================
# SHADOW LEARNING MODULE
# ============================================================================

from .shadow_learning import (
    # Models
    AITutorPair,
    AIRLHFScore,
    AIExportJob,

    # Enums
    ModelType,
    ExportStatus,
)


# ============================================================================
# PACKAGE EXPORTS
# ============================================================================

__all__ = [
    # ========================================================================
    # UNIFIED CONVERSATION MODELS (conversations.py)
    # ========================================================================
    "UnifiedConversation",          # Main conversation model (all channels)
    "UnifiedMessage",                # Message model (all roles, emotions, tokens)

    # Conversation Enums
    "ChannelType",                   # web/sms/voice/facebook/instagram/email
    "ConversationStatus",            # active/escalated/closed/archived
    "MessageRole",                   # user/assistant/system/human/tool
    "EmotionTrend",                  # improving/stable/declining
    "EmotionLabel",                  # positive/neutral/negative

    # ========================================================================
    # CUSTOMER ENGAGEMENT MODELS (engagement.py)
    # ========================================================================
    "CustomerEngagementFollowUp",    # Scheduled follow-up messages

    # Engagement Enums
    "FollowUpTriggerType",           # post_event/reengagement/emotion_based/custom
    "FollowUpStatus",                # pending/executed/cancelled/failed

    # Engagement Helper Functions
    "calculate_post_event_schedule_time",      # Business logic helper
    "calculate_reengagement_schedule_time",    # Business logic helper
    "should_send_followup",                    # Duplicate prevention

    # ========================================================================
    # KNOWLEDGE BASE MODELS (knowledge.py)
    # ========================================================================
    "KnowledgeBaseChunk",            # RAG knowledge base chunks
    "EscalationRule",                # Auto-escalation rules

    # Knowledge Enums
    "KnowledgeSourceType",           # faq/policy/procedure/learned/menu/custom

    # ========================================================================
    # ANALYTICS MODELS (analytics.py)
    # ========================================================================
    "ConversationAnalytics",         # Conversation quality metrics
    "AIUsage",                       # AI usage tracking (tokens, cost)
    "TrainingData",                  # High-quality training data collection

    # Analytics Enums
    "ResolutionStatus",              # resolved/unresolved/escalated/abandoned

    # ========================================================================
    # SHADOW LEARNING MODELS (shadow_learning.py)
    # ========================================================================
    "AITutorPair",                   # Teacher-student response pairs
    "AIRLHFScore",                   # Human feedback scores (RLHF)
    "AIExportJob",                   # Training data export jobs

    # Shadow Learning Enums
    "ModelType",                     # teacher/student
    "ExportStatus",                  # pending/in_progress/completed/failed
]


# ============================================================================
# VERSION
# ============================================================================

__version__ = "1.0.0"
__schema__ = "ai"
__description__ = "AI Models Package - Unified conversation, engagement, knowledge, analytics, and shadow learning"
