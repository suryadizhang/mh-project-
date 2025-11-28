"""
Customer Engagement and Follow-Up Models - ai Schema

This module handles scheduled customer engagement and automated follow-ups.

Business Requirements:
- Post-event follow-ups (24h after booking completion)
- Re-engagement campaigns (30+ days inactive users)
- Emotion-based outreach (low emotion score detection)
- Custom admin-scheduled messages
- Template-based messaging with emotion awareness
- APScheduler integration for background execution

Schema: ai
Table: customer_engagement_followups

Previous name: scheduled_followups (renamed for clarity)
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

# MIGRATED: from models.base → ...base_class (3 levels up from ai/)
from ...base_class import Base


# ============================================================================
# ENUMS
# ============================================================================


class FollowUpTriggerType(str, Enum):
    """
    Follow-up trigger types.

    Business Context:
    - POST_EVENT: Sent 24h after booking/event completion
    - RE_ENGAGEMENT: Sent to users inactive for 30+ days
    - EMOTION_BASED: Triggered by low emotion score in conversation
    - CUSTOM: Manually scheduled by admin for specific users
    """

    POST_EVENT = "post_event"
    RE_ENGAGEMENT = "reengagement"
    EMOTION_BASED = "emotion_based"
    CUSTOM = "custom"


class FollowUpStatus(str, Enum):
    """
    Follow-up execution status.

    Business Context:
    - PENDING: Scheduled, waiting to execute
    - EXECUTED: Successfully sent to customer
    - CANCELLED: Cancelled before execution (user opted out, booking cancelled)
    - FAILED: Failed to send (retry if retry_count < 3)
    """

    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"


# ============================================================================
# CUSTOMER ENGAGEMENT FOLLOWUP MODEL
# ============================================================================


class CustomerEngagementFollowUp(Base):
    """
    Scheduled customer engagement and follow-up messages.

    Schema: ai.customer_engagement_followups

    Business Logic:
    1. Schedule messages based on customer triggers
    2. Support emotion-aware templates
    3. Track execution status and retries
    4. Prevent duplicate follow-ups
    5. Enable admin manual scheduling

    Trigger Types:
    - POST_EVENT: 24h after event (emotion-aware templates)
    - RE_ENGAGEMENT: 30+ days inactive (win-back campaign)
    - EMOTION_BASED: Low emotion score detected (recovery message)
    - CUSTOM: Admin-scheduled (special occasions, promotions)

    Key Features:
    - Duplicate prevention (composite index on user + trigger + status + scheduled_at)
    - Retry logic (max 3 retries with exponential backoff)
    - Template system (emotion-aware message selection)
    - APScheduler integration (background job execution)
    - JSONB trigger_data (flexible metadata storage)

    Indexes:
    - Composite: (status, scheduled_at) - Scheduler queries (most critical)
    - Composite: (user_id, status) - User follow-up history
    - Composite: (user_id, trigger_type, status, scheduled_at) - Duplicate check
    - Single: conversation_id - Conversation tracking

    Business Rules:
    1. Max 1 follow-up per user per trigger type per 24h
    2. Auto-cancel if user opts out or booking cancelled
    3. Max 3 retry attempts on failure
    4. Execute between 9 AM - 9 PM local time (respect quiet hours)
    5. Emotion-aware template selection (high/neutral/low emotion)

    Example Usage:
    ```python
    # Schedule post-event follow-up
    followup = CustomerEngagementFollowUp(
        id=str(uuid.uuid4()),
        conversation_id="conv_abc123",
        user_id="user_xyz789",
        trigger_type=FollowUpTriggerType.POST_EVENT,
        trigger_data={
            "booking_id": "book_456",
            "event_date": "2025-11-20",
            "emotion_score": 0.85,  # High emotion
            "chef_name": "Chef Mike"
        },
        scheduled_at=datetime(2025, 11, 21, 10, 0),  # 24h after event
        status=FollowUpStatus.PENDING,
        template_id="post_event_high_emotion",
        message_content="Hi! 🎉 I hope your event on 2025-11-20 was amazing..."
    )
    ```
    """

    __tablename__ = "customer_engagement_followups"
    __table_args__ = (
        # CRITICAL: Scheduler queries (most frequent operation)
        # Finds all pending messages ready to send
        Index("idx_followups_status_scheduled", "status", "scheduled_at"),
        # User follow-up history (admin dashboard, analytics)
        Index("idx_followups_user_status", "user_id", "status"),
        # Duplicate prevention (UNIQUE constraint enforced by business logic)
        # Prevents multiple follow-ups for same user + trigger within 24h
        Index("idx_followups_duplicate_check", "user_id", "trigger_type", "status", "scheduled_at"),
        # Conversation tracking (link follow-ups to original conversation)
        Index("idx_followups_conversation", "conversation_id"),
        # Trigger type analytics (measure campaign effectiveness)
        Index("idx_followups_trigger_type", "trigger_type", "status"),
        # Time-based analytics (execution rates, delays)
        Index("idx_followups_created", "created_at"),
        Index("idx_followups_executed", "executed_at"),
        # Schema assignment
        {"schema": "ai"},
    )

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================

    id = Column(
        String(255),
        primary_key=True,
        comment="Unique follow-up identifier (UUID, max 255 for compatibility)",
    )

    # ========================================================================
    # RELATIONSHIP IDENTIFIERS
    # ========================================================================

    conversation_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Original conversation ID that triggered this follow-up",
    )

    user_id = Column(
        String(255), nullable=False, index=True, comment="User ID to send follow-up to"
    )

    # ========================================================================
    # TRIGGER INFORMATION
    # ========================================================================

    trigger_type = Column(
        String(50),
        nullable=False,
        comment="Trigger type (post_event/reengagement/emotion_based/custom)",
    )

    trigger_data = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="""
        Trigger-specific data (JSONB for flexibility):
        - POST_EVENT: {booking_id, event_date, emotion_score, chef_name}
        - RE_ENGAGEMENT: {last_active_date, booking_count, total_spent}
        - EMOTION_BASED: {emotion_score, emotion_trend, message_id}
        - CUSTOM: {admin_id, campaign_name, promo_code}
        """,
    )

    # ========================================================================
    # SCHEDULING
    # ========================================================================

    scheduled_at = Column(
        DateTime,
        nullable=False,
        index=True,
        comment="When to send this follow-up (scheduler queries this field)",
    )

    executed_at = Column(
        DateTime,
        nullable=True,
        comment="When follow-up was actually sent (NULL if not executed yet)",
    )

    cancelled_at = Column(
        DateTime, nullable=True, comment="When follow-up was cancelled (NULL if not cancelled)"
    )

    status = Column(
        String(20),
        nullable=False,
        default=FollowUpStatus.PENDING.value,
        comment="Execution status (pending/executed/cancelled/failed)",
    )

    # ========================================================================
    # MESSAGE CONTENT
    # ========================================================================

    template_id = Column(
        String(50),
        nullable=True,
        comment="""
        Template ID for message generation:
        - post_event_high_emotion
        - post_event_neutral_emotion
        - post_event_low_emotion
        - reengagement_general
        - emotion_recovery
        - custom_admin
        """,
    )

    message_content = Column(
        Text,
        nullable=True,
        comment="""
        Pre-rendered message content (template variables replaced).
        NULL if not yet rendered. Rendered at scheduling time or execution time.
        """,
    )

    # ========================================================================
    # METADATA & ERROR TRACKING
    # ========================================================================

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When follow-up was created/scheduled",
    )

    error_message = Column(
        Text, nullable=True, comment="Error message if execution failed (for debugging)"
    )

    retry_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of retry attempts (max 3, exponential backoff)",
    )


# ============================================================================
# HELPER FUNCTIONS (Business Logic)
# ============================================================================


def calculate_post_event_schedule_time(event_date: datetime) -> datetime:
    """
    Calculate when to send post-event follow-up.

    Business Rule: 24 hours after event, between 9 AM - 9 PM local time.

    Args:
        event_date: Event datetime

    Returns:
        Scheduled datetime (24h after, adjusted to business hours)

    Example:
        Event: 2025-11-20 19:00 (7 PM)
        Initial: 2025-11-21 19:00 (24h later)
        Adjusted: 2025-11-21 10:00 (next morning, 9-9 window)
    """
    from datetime import timedelta

    # 24 hours after event
    scheduled = event_date + timedelta(hours=24)

    # Adjust to business hours (9 AM - 9 PM)
    if scheduled.hour < 9:
        # Too early → move to 10 AM same day
        scheduled = scheduled.replace(hour=10, minute=0, second=0)
    elif scheduled.hour >= 21:
        # Too late → move to 10 AM next day
        scheduled = (scheduled + timedelta(days=1)).replace(hour=10, minute=0, second=0)

    return scheduled


def calculate_reengagement_schedule_time(last_active: datetime) -> datetime:
    """
    Calculate when to send re-engagement message.

    Business Rule: 30 days after last activity, sent at 10 AM local time.

    Args:
        last_active: Last activity datetime

    Returns:
        Scheduled datetime (30 days later, 10 AM)
    """
    from datetime import timedelta

    scheduled = last_active + timedelta(days=30)
    scheduled = scheduled.replace(hour=10, minute=0, second=0, microsecond=0)

    return scheduled


def should_send_followup(
    user_id: str, trigger_type: FollowUpTriggerType, scheduled_at: datetime, session
) -> bool:
    """
    Check if follow-up should be sent (duplicate prevention).

    Business Rule: Max 1 follow-up per user per trigger type per 24h.

    Args:
        user_id: User identifier
        trigger_type: Trigger type
        scheduled_at: Proposed scheduled time
        session: Database session

    Returns:
        True if safe to schedule, False if duplicate detected
    """
    from datetime import timedelta

    # Check for existing follow-ups within 24h window
    window_start = scheduled_at - timedelta(hours=12)
    window_end = scheduled_at + timedelta(hours=12)

    existing = (
        session.query(CustomerEngagementFollowUp)
        .filter(
            CustomerEngagementFollowUp.user_id == user_id,
            CustomerEngagementFollowUp.trigger_type == trigger_type.value,
            CustomerEngagementFollowUp.status.in_(
                [FollowUpStatus.PENDING.value, FollowUpStatus.EXECUTED.value]
            ),
            CustomerEngagementFollowUp.scheduled_at.between(window_start, window_end),
        )
        .first()
    )

    return existing is None
