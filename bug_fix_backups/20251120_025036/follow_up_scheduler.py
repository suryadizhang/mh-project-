"""
Smart Follow-Up Scheduler
========================

Automated engagement system using APScheduler for:
- Post-event follow-ups (24h after booking/event)
- Re-engagement campaigns (30+ days inactive)
- Emotion-based message templates
- Context-aware scheduling based on conversation history

Architecture:
- AsyncIOScheduler for background job execution
- PostgreSQL for follow-up persistence and state tracking
- Integration with MemoryBackend for conversation context
- Template system for personalized messages
"""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import Enum
import logging
from typing import Any

from api.ai.memory.memory_backend import MemoryBackend
from api.ai.services.emotion_service import EmotionService
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from core.database import Base, get_db_context
from pydantic import BaseModel, Field
import pytz
from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

logger = logging.getLogger(__name__)

# Background task tracking for scheduling operations
_scheduling_background_tasks = set()


# =============================================================================
# DATABASE MODEL
# =============================================================================


class ScheduledFollowUp(Base):
    """Model for scheduled follow-up messages."""

    __tablename__ = "scheduled_followups"

    id = Column(
        String(255), primary_key=True
    )  # Increased from 50 to 255 for generated IDs
    conversation_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)

    # Trigger information
    trigger_type = Column(
        String(50), nullable=False
    )  # post_event/reengagement/emotion_based
    trigger_data = Column(
        JSONB, nullable=False, default={}
    )  # Event date, booking ID, etc.

    # Scheduling
    scheduled_at = Column(DateTime, nullable=False, index=True)
    executed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending/executed/cancelled/failed

    # Message
    template_id = Column(String(50), nullable=True)
    message_content = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    __table_args__ = (
        Index(
            "idx_scheduled_followups_status_scheduled",
            "status",
            "scheduled_at",
        ),
        Index("idx_scheduled_followups_user_status", "user_id", "status"),
        # Composite index for duplicate check optimization (covers most common query pattern)
        Index(
            "idx_scheduled_followups_duplicate_check",
            "user_id",
            "trigger_type",
            "status",
            "scheduled_at",
        ),
    )


# =============================================================================
# ENUMS AND MODELS
# =============================================================================


class FollowUpTriggerType(str, Enum):
    """Follow-up trigger types"""

    POST_EVENT = "post_event"  # After booking/event (24h)
    RE_ENGAGEMENT = "reengagement"  # Inactive user (30d)
    EMOTION_BASED = "emotion_based"  # Low emotion score follow-up
    CUSTOM = "custom"  # Custom scheduled message


class FollowUpStatus(str, Enum):
    """Follow-up execution status"""

    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class FollowUpTemplate(BaseModel):
    """Follow-up message template"""

    id: str
    name: str
    trigger_type: FollowUpTriggerType
    content: str
    emotion_condition: str | None = None  # high/neutral/low
    variables: list[str] = Field(
        default_factory=list
    )  # {booking_id}, {event_date}, etc.


class FollowUpJob(BaseModel):
    """Follow-up job details"""

    id: str
    conversation_id: str
    user_id: str
    trigger_type: FollowUpTriggerType
    scheduled_at: datetime
    status: FollowUpStatus
    template_id: str | None = None
    message_preview: str | None = None


# =============================================================================
# MESSAGE TEMPLATES
# =============================================================================

FOLLOW_UP_TEMPLATES = {
    # Post-Event Templates (emotion-aware)
    "post_event_high_emotion": FollowUpTemplate(
        id="post_event_high_emotion",
        name="Post-Event Follow-Up (Enthusiastic)",
        trigger_type=FollowUpTriggerType.POST_EVENT,
        emotion_condition="high",
        content="""
Hi! 🎉 I hope your event on {event_date} was absolutely amazing!

I'd love to hear how everything went. Did our catering service exceed your expectations?
Any special moments or feedback you'd like to share?

Looking forward to hearing from you!
        """.strip(),
        variables=["event_date"],
    ),
    "post_event_neutral_emotion": FollowUpTemplate(
        id="post_event_neutral_emotion",
        name="Post-Event Follow-Up (Standard)",
        trigger_type=FollowUpTriggerType.POST_EVENT,
        emotion_condition="neutral",
        content="""
Hello! I wanted to check in about your event on {event_date}.

How did everything go? We'd appreciate any feedback about our catering service -
it helps us improve and serve you better.

Feel free to reach out if you have any questions or need assistance with future events.
        """.strip(),
        variables=["event_date"],
    ),
    "post_event_low_emotion": FollowUpTemplate(
        id="post_event_low_emotion",
        name="Post-Event Follow-Up (Empathetic)",
        trigger_type=FollowUpTriggerType.POST_EVENT,
        emotion_condition="low",
        content="""
Hi there. I wanted to follow up on your event from {event_date}.

I noticed you had some concerns during our conversation, and I want to make sure
everything went smoothly. If there were any issues, please let me know -
we're committed to making things right.

Your satisfaction is our top priority.
        """.strip(),
        variables=["event_date"],
    ),
    # Re-engagement Templates
    "reengagement_general": FollowUpTemplate(
        id="reengagement_general",
        name="Re-engagement (General)",
        trigger_type=FollowUpTriggerType.RE_ENGAGEMENT,
        content="""
Hi! It's been a while since we last connected.

I wanted to reach out and see if you're planning any upcoming events.
We've added some new menu options and services that might interest you.

Would you like to discuss your catering needs? I'm here to help!
        """.strip(),
        variables=[],
    ),
    "reengagement_past_customer": FollowUpTemplate(
        id="reengagement_past_customer",
        name="Re-engagement (Past Customer)",
        trigger_type=FollowUpTriggerType.RE_ENGAGEMENT,
        content="""
Hello! I hope you're doing well.

We loved working with you on your previous event, and I wanted to check in
to see if you have any upcoming occasions where we could assist again.

As a valued customer, we'd be happy to discuss special arrangements for your next event.
        """.strip(),
        variables=[],
    ),
    # Emotion-Based Templates
    "emotion_check_in": FollowUpTemplate(
        id="emotion_check_in",
        name="Low Emotion Check-In",
        trigger_type=FollowUpTriggerType.EMOTION_BASED,
        emotion_condition="low",
        content="""
Hi, I wanted to check in with you.

I noticed you seemed a bit concerned during our last conversation.
Is there anything I can help clarify or any issues I can address?

I'm here to make sure you have the best experience possible.
        """.strip(),
        variables=[],
    ),
}


# =============================================================================
# FOLLOW-UP SCHEDULER
# =============================================================================


class FollowUpScheduler:
    """
    Smart Follow-Up Scheduler with emotion awareness

    Features:
    - Post-event follow-ups (24 hours after event date)
    - Re-engagement campaigns (30+ days inactive)
    - Emotion-based scheduling (low scores trigger check-ins)
    - Duplicate prevention
    - Job persistence in PostgreSQL
    - Integration with MemoryBackend for context

    Usage:
        scheduler = FollowUpScheduler(memory_backend, emotion_service)
        await scheduler.start()

        # Schedule post-event follow-up
        job_id = await scheduler.schedule_post_event_followup(
            conversation_id="conv_123",
            user_id="user_456",
            event_date=datetime(2025, 11, 5, 18, 0, 0)
        )

        # Schedule re-engagement
        job_id = await scheduler.schedule_reengagement(
            user_id="user_789",
            last_activity=datetime(2025, 10, 1)
        )
    """

    def __init__(
        self,
        memory: "MemoryBackend",
        emotion_service: "EmotionService",
        timezone: str = "UTC",
        orchestrator_callback: Callable | None = None,
    ):
        """
        Initialize the follow-up scheduler.

        Args:
            memory: Memory backend for conversation history
            emotion_service: Emotion detection service
            timezone: Timezone for scheduler (default: UTC)
            orchestrator_callback: Optional callback to send messages (for production use)
        """
        self.memory = memory
        self.emotion_service = emotion_service
        self.orchestrator_callback = orchestrator_callback
        self.timezone = pytz.timezone(timezone)
        self.scheduler = AsyncIOScheduler(timezone=self.timezone)
        self._running = False

        # Performance optimization: Cache health check results
        self._health_cache: dict[str, Any] | None = None
        self._health_cache_time: datetime | None = None
        self._health_cache_ttl = 30  # Cache for 30 seconds

        logger.info("FollowUpScheduler initialized")

    async def start(self) -> None:
        """Start the scheduler"""
        if not self._running:
            self.scheduler.start()
            self._running = True
            # Clear health cache on start
            self._health_cache = None
            self._health_cache_time = None
            await self._restore_pending_jobs()
            logger.info("FollowUpScheduler started")

    async def stop(self) -> None:
        """Stop the scheduler"""
        if self._running:
            self.scheduler.shutdown(wait=True)
            self._running = False
            # Clear health cache on stop
            self._health_cache = None
            self._health_cache_time = None
            logger.info("FollowUpScheduler stopped")

    async def _restore_pending_jobs(self) -> None:
        """Restore pending jobs from database after restart"""
        try:
            async with get_db_context() as db:
                from sqlalchemy import select

                # Use timezone-naive datetime since scheduled_at column is TIMESTAMP WITHOUT TIME ZONE
                now_utc = datetime.now(UTC).replace(tzinfo=None)

                # Get all pending jobs
                stmt = select(ScheduledFollowUp).where(
                    ScheduledFollowUp.status == FollowUpStatus.PENDING.value,
                    ScheduledFollowUp.scheduled_at > now_utc,
                )
                result = await db.execute(stmt)
                pending_jobs = result.scalars().all()

                # Reschedule each job
                for job in pending_jobs:
                    self.scheduler.add_job(
                        self._execute_followup,
                        trigger=DateTrigger(
                            run_date=job.scheduled_at, timezone=self.timezone
                        ),
                        args=[job.id],
                        id=job.id,
                        replace_existing=True,
                    )

                logger.info(
                    f"Restored {len(pending_jobs)} pending follow-up jobs"
                )

        except Exception as e:
            logger.exception(f"Failed to restore pending jobs: {e}")

    async def schedule_post_event_followup(
        self,
        conversation_id: str,
        user_id: str,
        event_date: datetime,
        booking_id: str | None = None,
        followup_delay: timedelta = timedelta(hours=24),
    ) -> str:
        """
        Schedule a post-event follow-up message

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            event_date: Date of the event
            booking_id: Optional booking ID for context
            followup_delay: Delay after event (default: 24 hours)

        Returns:
            Job ID
        """
        try:
            # Calculate scheduled time (event_date + delay)
            scheduled_at = event_date + followup_delay

            # Check for duplicates
            if await self._has_pending_followup(
                user_id, FollowUpTriggerType.POST_EVENT, event_date
            ):
                logger.warning(
                    f"Post-event follow-up already scheduled for user {user_id}"
                )
                return None

            # Get emotion history to select template
            emotion_history = await self.memory.get_emotion_history(
                conversation_id, limit=5
            )
            template = await self._select_template_by_emotion(
                FollowUpTriggerType.POST_EVENT, emotion_history
            )

            # Create follow-up record
            job_id = f"followup_{user_id}_{int(scheduled_at.timestamp())}"

            async with get_db_context() as db:
                followup = ScheduledFollowUp(
                    id=job_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    trigger_type=FollowUpTriggerType.POST_EVENT.value,
                    trigger_data={
                        "event_date": event_date.isoformat(),
                        "booking_id": booking_id,
                        "followup_delay_hours": followup_delay.total_seconds()
                        / 3600,
                    },
                    scheduled_at=scheduled_at,
                    status=FollowUpStatus.PENDING.value,
                    template_id=template.id,
                    message_content=self._render_template(
                        template,
                        {"event_date": event_date.strftime("%B %d, %Y")},
                    ),
                )
                db.add(followup)
                await db.commit()

            # Schedule the job
            self.scheduler.add_job(
                self._execute_followup,
                trigger=DateTrigger(
                    run_date=scheduled_at, timezone=self.timezone
                ),
                args=[job_id],
                id=job_id,
                replace_existing=True,
            )

            logger.info(
                f"Scheduled post-event follow-up: {job_id} at {scheduled_at}"
            )
            return job_id

        except Exception as e:
            logger.exception(f"Failed to schedule post-event follow-up: {e}")
            raise

    async def schedule_post_event_followup_background(
        self,
        conversation_id: str,
        user_id: str,
        event_date: datetime,
        booking_id: str | None = None,
        followup_delay: timedelta = timedelta(hours=24),
    ) -> None:
        """
        Schedule post-event follow-up in background (non-blocking)

        This is a fire-and-forget wrapper around schedule_post_event_followup
        that doesn't block the caller. Perfect for booking confirmation endpoints.

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            event_date: Date of the event
            booking_id: Optional booking ID for context
            followup_delay: Delay after event (default: 24 hours)
        """
        try:
            job_id = await self.schedule_post_event_followup(
                conversation_id=conversation_id,
                user_id=user_id,
                event_date=event_date,
                booking_id=booking_id,
                followup_delay=followup_delay,
            )
            logger.debug(f"Background scheduling completed: {job_id}")
        except Exception as e:
            # Log errors but don't raise - this is a background task
            logger.error(
                f"Background scheduling failed for user {user_id}: {e}",
                exc_info=True,
            )

    async def schedule_reengagement(
        self,
        user_id: str,
        last_activity: datetime,
        inactive_threshold: timedelta = timedelta(days=30),
    ) -> str:
        """
        Schedule a re-engagement message for inactive user

        Args:
            user_id: User ID
            last_activity: Last activity timestamp
            inactive_threshold: Inactivity threshold (default: 30 days)

        Returns:
            Job ID
        """
        try:
            # Calculate scheduled time (last_activity + threshold)
            scheduled_at = last_activity + inactive_threshold

            # Check for duplicates
            if await self._has_pending_followup(
                user_id, FollowUpTriggerType.RE_ENGAGEMENT
            ):
                logger.warning(
                    f"Re-engagement already scheduled for user {user_id}"
                )
                return None

            # Select template (check if past customer)
            conversations = await self.memory.get_user_conversations(
                user_id, include_inactive=True
            )
            has_past_bookings = len(conversations) > 1

            template = (
                FOLLOW_UP_TEMPLATES["reengagement_past_customer"]
                if has_past_bookings
                else FOLLOW_UP_TEMPLATES["reengagement_general"]
            )

            # Create follow-up record
            job_id = f"reengagement_{user_id}_{int(scheduled_at.timestamp())}"

            async with get_db_context() as db:
                followup = ScheduledFollowUp(
                    id=job_id,
                    conversation_id="",  # No specific conversation
                    user_id=user_id,
                    trigger_type=FollowUpTriggerType.RE_ENGAGEMENT.value,
                    trigger_data={
                        "last_activity": last_activity.isoformat(),
                        "inactive_days": inactive_threshold.days,
                        "past_conversations": len(conversations),
                    },
                    scheduled_at=scheduled_at,
                    status=FollowUpStatus.PENDING.value,
                    template_id=template.id,
                    message_content=template.content,
                )
                db.add(followup)
                await db.commit()

            # Schedule the job
            self.scheduler.add_job(
                self._execute_followup,
                trigger=DateTrigger(
                    run_date=scheduled_at, timezone=self.timezone
                ),
                args=[job_id],
                id=job_id,
                replace_existing=True,
            )

            logger.info(f"Scheduled re-engagement: {job_id} at {scheduled_at}")
            return job_id

        except Exception as e:
            logger.exception(f"Failed to schedule re-engagement: {e}")
            raise

    async def cancel_followup(self, job_id: str) -> bool:
        """
        Cancel a scheduled follow-up

        Args:
            job_id: Follow-up job ID

        Returns:
            True if cancelled, False if not found
        """
        try:
            # Remove from scheduler
            try:
                self.scheduler.remove_job(job_id)
            except:
                pass  # Job may not exist in scheduler

            # Update database
            async with get_db_context() as db:
                from sqlalchemy import select

                stmt = select(ScheduledFollowUp).where(
                    ScheduledFollowUp.id == job_id
                )
                result = await db.execute(stmt)
                followup = result.scalar_one_or_none()

                if not followup:
                    return False

                followup.status = FollowUpStatus.CANCELLED.value
                followup.cancelled_at = datetime.now(UTC)
                await db.commit()

            logger.info(f"Cancelled follow-up: {job_id}")
            return True

        except Exception as e:
            logger.exception(f"Failed to cancel follow-up: {e}")
            return False

    async def get_scheduled_followups(
        self,
        user_id: str | None = None,
        status: FollowUpStatus | None = None,
        limit: int = 50,
    ) -> list[FollowUpJob]:
        """
        Get scheduled follow-ups

        Args:
            user_id: Filter by user ID (optional)
            status: Filter by status (optional)
            limit: Maximum results

        Returns:
            List of follow-up jobs
        """
        try:
            async with get_db_context() as db:
                from sqlalchemy import select

                stmt = select(ScheduledFollowUp)

                if user_id:
                    stmt = stmt.where(ScheduledFollowUp.user_id == user_id)

                if status:
                    stmt = stmt.where(ScheduledFollowUp.status == status.value)

                stmt = stmt.order_by(
                    ScheduledFollowUp.scheduled_at.desc()
                ).limit(limit)

                result = await db.execute(stmt)
                followups = result.scalars().all()

                # Convert to FollowUpJob models
                jobs = []
                for f in followups:
                    jobs.append(
                        FollowUpJob(
                            id=f.id,
                            conversation_id=f.conversation_id,
                            user_id=f.user_id,
                            trigger_type=FollowUpTriggerType(f.trigger_type),
                            scheduled_at=f.scheduled_at,
                            status=FollowUpStatus(f.status),
                            template_id=f.template_id,
                            message_preview=(
                                f.message_content[:100]
                                if f.message_content
                                else None
                            ),
                        )
                    )

                return jobs

        except Exception as e:
            logger.exception(f"Failed to get scheduled follow-ups: {e}")
            return []

    async def _execute_followup(self, job_id: str) -> None:
        """
        Execute a scheduled follow-up (called by APScheduler)

        Args:
            job_id: Follow-up job ID
        """
        try:
            logger.info(f"Executing follow-up: {job_id}")

            # Get follow-up from database
            async with get_db_context() as db:
                from sqlalchemy import select

                stmt = select(ScheduledFollowUp).where(
                    ScheduledFollowUp.id == job_id
                )
                result = await db.execute(stmt)
                followup = result.scalar_one_or_none()

                if (
                    not followup
                    or followup.status != FollowUpStatus.PENDING.value
                ):
                    logger.warning(
                        f"Follow-up {job_id} not found or not pending"
                    )
                    return

                # Send message via orchestrator callback if available
                if self.orchestrator_callback:
                    try:
                        await self.orchestrator_callback(
                            user_id=followup.user_id,
                            conversation_id=followup.conversation_id
                            or f"followup_{followup.id}",
                            content=followup.message_content,
                            metadata={
                                "type": "automated_followup",
                                "followup_id": job_id,
                                "trigger_type": followup.trigger_type,
                                "template_id": followup.template_id,
                                "scheduled_at": followup.scheduled_at.isoformat(),
                                "executed_at": datetime.now(UTC).isoformat(),
                            },
                        )
                        logger.info(f"Message sent for follow-up: {job_id}")
                    except Exception as e:
                        logger.exception(
                            f"Failed to send message for follow-up {job_id}: {e}"
                        )
                        raise  # Re-raise to mark as failed
                else:
                    # No callback - just log (useful for testing)
                    logger.info(
                        f"No orchestrator callback - follow-up {job_id} marked as executed (testing mode)"
                    )

                # Update status
                followup.status = FollowUpStatus.EXECUTED.value
                followup.executed_at = datetime.now(UTC)
                await db.commit()

                logger.info(f"Successfully executed follow-up: {job_id}")

        except Exception as e:
            logger.exception(f"Failed to execute follow-up {job_id}: {e}")

            # Update status to failed
            try:
                async with get_db_context() as db:
                    from sqlalchemy import select

                    stmt = select(ScheduledFollowUp).where(
                        ScheduledFollowUp.id == job_id
                    )
                    result = await db.execute(stmt)
                    followup = result.scalar_one_or_none()

                    if followup:
                        followup.status = FollowUpStatus.FAILED.value
                        followup.error_message = str(e)
                        followup.retry_count += 1
                        await db.commit()
            except:
                pass

    async def _has_pending_followup(
        self,
        user_id: str,
        trigger_type: FollowUpTriggerType,
        event_date: datetime | None = None,
    ) -> bool:
        """Check if user already has pending follow-up of this type"""
        try:
            async with get_db_context() as db:
                from sqlalchemy import and_, select

                conditions = [
                    ScheduledFollowUp.user_id == user_id,
                    ScheduledFollowUp.trigger_type == trigger_type.value,
                    ScheduledFollowUp.status == FollowUpStatus.PENDING.value,
                ]

                if event_date:
                    # Check if event date matches (within 1 day tolerance)
                    date_start = event_date - timedelta(days=1)
                    date_end = event_date + timedelta(days=1)
                    conditions.append(
                        and_(
                            ScheduledFollowUp.scheduled_at >= date_start,
                            ScheduledFollowUp.scheduled_at <= date_end,
                        )
                    )

                stmt = select(ScheduledFollowUp).where(and_(*conditions))
                result = await db.execute(stmt)
                return result.scalar_one_or_none() is not None

        except Exception as e:
            logger.exception(f"Failed to check for pending follow-up: {e}")
            return False

    async def _select_template_by_emotion(
        self,
        trigger_type: FollowUpTriggerType,
        emotion_history: list[dict[str, Any]],
    ) -> FollowUpTemplate:
        """Select appropriate template based on emotion history"""
        try:
            if not emotion_history:
                # No emotion data, use neutral template
                if trigger_type == FollowUpTriggerType.POST_EVENT:
                    return FOLLOW_UP_TEMPLATES["post_event_neutral_emotion"]
                else:
                    return FOLLOW_UP_TEMPLATES["reengagement_general"]

            # Calculate average emotion score
            scores = [e["score"] for e in emotion_history if e.get("score")]
            if not scores:
                if trigger_type == FollowUpTriggerType.POST_EVENT:
                    return FOLLOW_UP_TEMPLATES["post_event_neutral_emotion"]
                else:
                    return FOLLOW_UP_TEMPLATES["reengagement_general"]

            avg_score = sum(scores) / len(scores)

            # Select template based on emotion
            if trigger_type == FollowUpTriggerType.POST_EVENT:
                if avg_score >= 0.7:
                    return FOLLOW_UP_TEMPLATES["post_event_high_emotion"]
                elif avg_score < 0.4:
                    return FOLLOW_UP_TEMPLATES["post_event_low_emotion"]
                else:
                    return FOLLOW_UP_TEMPLATES["post_event_neutral_emotion"]
            else:
                return FOLLOW_UP_TEMPLATES["reengagement_general"]

        except Exception as e:
            logger.exception(f"Failed to select template by emotion: {e}")
            # Fallback to neutral
            if trigger_type == FollowUpTriggerType.POST_EVENT:
                return FOLLOW_UP_TEMPLATES["post_event_neutral_emotion"]
            else:
                return FOLLOW_UP_TEMPLATES["reengagement_general"]

    def _render_template(
        self, template: FollowUpTemplate, variables: dict[str, str]
    ) -> str:
        """Render template with variables"""
        content = template.content
        for key, value in variables.items():
            content = content.replace(f"{{{key}}}", str(value))
        return content

    async def health_check(self) -> dict[str, Any]:
        """
        Health check for scheduler (cached for 30 seconds to improve performance)

        Returns:
            Health status with metrics
        """
        # Return cached result if still valid
        if self._health_cache and self._health_cache_time:
            cache_age = (
                datetime.now(UTC) - self._health_cache_time
            ).total_seconds()
            if cache_age < self._health_cache_ttl:
                logger.debug(
                    f"Returning cached health check (age: {cache_age:.1f}s)"
                )
                return self._health_cache

        # Cache expired or missing - fetch new data
        try:
            async with get_db_context() as db:
                from sqlalchemy import func, select

                # Count pending jobs
                stmt = select(func.count(ScheduledFollowUp.id)).where(
                    ScheduledFollowUp.status == FollowUpStatus.PENDING.value
                )
                result = await db.execute(stmt)
                pending_count = result.scalar()

                # Count executed today
                today = datetime.now(UTC).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                stmt = select(func.count(ScheduledFollowUp.id)).where(
                    ScheduledFollowUp.status == FollowUpStatus.EXECUTED.value,
                    ScheduledFollowUp.executed_at >= today,
                )
                result = await db.execute(stmt)
                executed_today = result.scalar()

                # Update cache
                self._health_cache = {
                    "status": "healthy",
                    "scheduler_running": self.scheduler.running,
                    "pending_followups": pending_count,
                    "executed_today": executed_today,
                    "timezone": str(self.timezone),
                    "background_tasks_active": len(
                        _scheduling_background_tasks
                    ),
                }
                self._health_cache_time = datetime.now(UTC)

                return self._health_cache

        except Exception as e:
            logger.exception(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "scheduler_running": (
                    self.scheduler.running if self.scheduler else False
                ),
                "background_tasks_active": len(_scheduling_background_tasks),
            }


# =============================================================================
# HELPER FUNCTIONS FOR BACKGROUND SCHEDULING
# =============================================================================


def schedule_followup_in_background(
    scheduler: FollowUpScheduler,
    conversation_id: str,
    user_id: str,
    event_date: datetime,
    booking_id: str | None = None,
) -> None:
    """
    Helper function to schedule follow-up in background without blocking

    Use this in booking endpoints to avoid waiting for scheduling to complete.

    Usage in booking endpoint:
        ```python
        # After creating booking (booking returns immediately)
        schedule_followup_in_background(
            scheduler=get_scheduler(),
            conversation_id=ai_conversation_id,
            user_id=user_id,
            event_date=booking_date,
            booking_id=booking_id
        )
        return booking_response  # Returns immediately, scheduling happens in background
        ```

    Args:
        scheduler: FollowUpScheduler instance
        conversation_id: AI conversation ID
        user_id: User ID
        event_date: Event/booking date
        booking_id: Booking ID for context
    """
    task = asyncio.create_task(
        scheduler.schedule_post_event_followup_background(
            conversation_id=conversation_id,
            user_id=user_id,
            event_date=event_date,
            booking_id=booking_id,
        )
    )

    # Track task to prevent garbage collection
    _scheduling_background_tasks.add(task)
    task.add_done_callback(_scheduling_background_tasks.discard)

    logger.debug(
        f"Queued follow-up scheduling for user {user_id}, booking {booking_id}"
    )
