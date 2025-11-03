"""
PostgreSQL Memory Backend Implementation
========================================

Production-ready conversation memory storage using PostgreSQL with JSONB.

Features:
- Async SQLAlchemy with connection pooling
- JSONB storage for flexible metadata
- Cross-channel conversation retrieval
- Emotion tracking and trend analysis
- Efficient context window management
- Full-text search support (future)

Database Schema:
- ai_conversations: Conversation metadata
- ai_messages: Individual messages with emotion tracking
- ai_emotion_history: Detailed emotion tracking

Performance:
- Indexed queries for fast retrieval
- JSONB GIN indexes for metadata search
- Partial indexes for active conversations
- Connection pooling for scalability
"""

import asyncio
from datetime import datetime, timedelta
import logging
import time
from typing import Any
from uuid import uuid4

from api.ai.memory.memory_backend import (
    ConversationChannel,
    ConversationMessage,
    ConversationMetadata,
    MemoryBackend,
    MemoryBackendError,
    MemoryConnectionError,
    MemoryNotFoundError,
    MessageRole,
)
from core.database import Base, get_db_context
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
    and_,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes, relationship

logger = logging.getLogger(__name__)

# Background task tracking for emotion stats updates
_background_tasks = set()


# =============================================================================
# DATABASE MODELS
# =============================================================================


class AIConversation(Base):
    """Conversation metadata table"""

    __tablename__ = "ai_conversations"

    # Primary key
    id = Column(String(100), primary_key=True)

    # User info
    user_id = Column(String(100), nullable=True, index=True)

    # Channel
    channel = Column(String(20), nullable=False, default="web")

    # Timestamps
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Counts
    message_count = Column(Integer, nullable=False, default=0)

    # Context (JSONB for flexibility)
    context = Column(JSONB, nullable=False, default=dict)

    # Emotion tracking
    average_emotion_score = Column(Float, nullable=True)
    emotion_trend = Column(String(20), nullable=True)  # improving/declining/stable
    escalated = Column(Boolean, nullable=False, default=False)
    escalated_at = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    closed_at = Column(DateTime, nullable=True)
    closed_reason = Column(String(100), nullable=True)

    # Relationships
    messages = relationship(
        "AIMessage", back_populates="conversation", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_ai_conversations_user_active", user_id, is_active),
        Index("idx_ai_conversations_channel", channel),
        Index("idx_ai_conversations_escalated", escalated, escalated_at),
        Index("idx_ai_conversations_last_message", last_message_at),
        # GIN index for JSONB context
        Index("idx_ai_conversations_context", context, postgresql_using="gin"),
    )


class AIMessage(Base):
    """Individual message table"""

    __tablename__ = "ai_messages"

    # Primary key
    id = Column(String(100), primary_key=True, default=lambda: str(uuid4()))

    # Foreign key to conversation
    conversation_id = Column(
        String(100),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message data
    role = Column(String(20), nullable=False)  # user/assistant/system/tool
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Message metadata (JSONB) - renamed to avoid SQLAlchemy reserved word
    message_metadata = Column(JSONB, nullable=False, default=dict)
    channel = Column(String(20), nullable=False, default="web")

    # Emotion tracking
    emotion_score = Column(Float, nullable=True)
    emotion_label = Column(String(20), nullable=True)  # negative/neutral/positive
    detected_emotions = Column(JSONB, nullable=True)  # Array of emotion strings

    # Token tracking
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)

    # Tool usage (JSONB)
    tool_calls = Column(JSONB, nullable=True)
    tool_results = Column(JSONB, nullable=True)

    # Relationship
    conversation = relationship("AIConversation", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index("idx_ai_messages_conversation_timestamp", conversation_id, timestamp),
        Index("idx_ai_messages_role", role),
        Index("idx_ai_messages_emotion_score", emotion_score),
        # Composite index for emotion history lookup (optimizes scheduler queries)
        Index("idx_ai_messages_emotion_history", conversation_id, emotion_score, timestamp),
        # GIN index for JSONB metadata
        Index("idx_ai_messages_message_metadata", message_metadata, postgresql_using="gin"),
    )


# =============================================================================
# POSTGRESQL MEMORY BACKEND
# =============================================================================


class PostgreSQLMemory(MemoryBackend):
    """
    PostgreSQL-based conversation memory with JSONB storage.

    Features:
    - Async SQLAlchemy for high performance
    - JSONB for flexible metadata
    - Cross-channel conversation tracking
    - Emotion history and trend analysis
    - Efficient context window management

    Usage:
        memory = PostgreSQLMemory()
        await memory.initialize()

        # Store message with emotion
        await memory.store_message(
            conversation_id="conv_123",
            role=MessageRole.USER,
            content="I'm frustrated with this!",
            emotion_score=0.25,
            emotion_label="negative"
        )
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._db_context = None
        logger.info("PostgreSQL memory backend created")

    async def initialize(self) -> None:
        """Initialize database connection"""
        try:
            # Test connection
            async with get_db_context() as db:
                result = await db.execute(select(func.count()).select_from(AIConversation))
                count = result.scalar()
                logger.info(f"PostgreSQL memory initialized - {count} conversations in database")

            self._initialized = True

        except Exception as e:
            logger.exception(f"Failed to initialize PostgreSQL memory: {e}")
            raise MemoryConnectionError(f"PostgreSQL initialization failed: {e}")

    async def health_check(self) -> dict[str, Any]:
        """Check database health"""
        start_time = time.time()

        try:
            async with get_db_context() as db:
                # Count messages
                result = await db.execute(select(func.count()).select_from(AIMessage))
                message_count = result.scalar()

                # Count active conversations
                result = await db.execute(
                    select(func.count()).select_from(AIConversation).where(AIConversation.is_active)
                )
                active_count = result.scalar()

            latency = int((time.time() - start_time) * 1000)

            return {
                "status": "healthy",
                "backend": "postgresql",
                "latency_ms": latency,
                "message_count": message_count,
                "active_conversations": active_count,
            }

        except Exception as e:
            logger.exception(f"PostgreSQL health check failed: {e}")
            return {"status": "unhealthy", "backend": "postgresql", "error": str(e)}

    async def close(self) -> None:
        """Close database connection"""
        logger.info("PostgreSQL memory backend closed")
        self._initialized = False

    # =========================================================================
    # MESSAGE OPERATIONS
    # =========================================================================

    async def store_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        metadata: dict[str, Any] | None = None,
        channel: ConversationChannel = ConversationChannel.WEB,
        emotion_score: float | None = None,
        emotion_label: str | None = None,
        detected_emotions: list[str] | None = None,
        user_id: str | None = None,
    ) -> ConversationMessage:
        """Store a message in the database (optimized with UPSERT)"""

        try:
            async with get_db_context() as db:
                from sqlalchemy.dialects.postgresql import insert

                message_id = str(uuid4())
                message_timestamp = datetime.utcnow()
                message_metadata = metadata or {}

                # OPTIMIZATION: Use UPSERT to create/update conversation in one query
                # This eliminates the SELECT + conditional INSERT (saves ~180ms)
                upsert_stmt = (
                    insert(AIConversation)
                    .values(
                        id=conversation_id,
                        user_id=user_id,
                        channel=channel.value,
                        started_at=message_timestamp,
                        last_message_at=message_timestamp,
                        message_count=1,
                        context={},
                        is_active=True,
                    )
                    .on_conflict_do_update(
                        index_elements=["id"],
                        set_={
                            "last_message_at": message_timestamp,
                            "message_count": AIConversation.message_count + 1,
                        },
                    )
                )

                await db.execute(upsert_stmt)

                # Create message
                message = AIMessage(
                    id=message_id,
                    conversation_id=conversation_id,
                    role=role.value,
                    content=content,
                    timestamp=message_timestamp,
                    message_metadata=message_metadata,
                    channel=channel.value,
                    emotion_score=emotion_score,
                    emotion_label=emotion_label,
                    detected_emotions=detected_emotions,
                )
                db.add(message)

                await db.commit()

                # OPTIMIZATION: Defer emotion stats calculation to background task
                # This saves ~530ms by not blocking the message storage
                if emotion_score is not None:
                    task = asyncio.create_task(
                        self._update_emotion_stats_background(conversation_id, emotion_score)
                    )
                    # Keep reference to prevent garbage collection
                    _background_tasks.add(task)
                    task.add_done_callback(_background_tasks.discard)

                # OPTIMIZATION: Construct ConversationMessage directly from insert data
                # instead of refreshing from DB (saves ~280ms round-trip)
                logger.debug(f"Stored message {message_id} in conversation {conversation_id}")

                return ConversationMessage(
                    id=message_id,
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    timestamp=message_timestamp,
                    metadata=message_metadata,
                    channel=channel,
                    emotion_score=emotion_score,
                    emotion_label=emotion_label,
                    detected_emotions=detected_emotions,
                    input_tokens=None,  # Not set on insert
                    output_tokens=None,  # Not set on insert
                    tool_calls=None,  # Not set on insert
                    tool_results=None,  # Not set on insert
                )

        except Exception as e:
            logger.exception(f"Failed to store message: {e}")
            raise MemoryBackendError(f"Failed to store message: {e}")

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int | None = None,
        offset: int = 0,
        include_system: bool = True,
    ) -> list[ConversationMessage]:
        """Retrieve conversation history"""

        try:
            async with get_db_context() as db:
                # Build query
                query = select(AIMessage).where(AIMessage.conversation_id == conversation_id)

                if not include_system:
                    query = query.where(AIMessage.role != "system")

                query = query.order_by(AIMessage.timestamp.asc())

                if offset > 0:
                    query = query.offset(offset)

                if limit:
                    query = query.limit(limit)

                result = await db.execute(query)
                messages = result.scalars().all()

                return [self._db_message_to_model(msg) for msg in messages]

        except Exception as e:
            logger.exception(f"Failed to get conversation history: {e}")
            raise MemoryBackendError(f"Failed to get history: {e}")

    async def get_recent_messages(
        self, conversation_id: str, count: int = 10
    ) -> list[ConversationMessage]:
        """Get N most recent messages"""

        try:
            async with get_db_context() as db:
                query = (
                    select(AIMessage)
                    .where(AIMessage.conversation_id == conversation_id)
                    .order_by(AIMessage.timestamp.desc())
                    .limit(count)
                )

                result = await db.execute(query)
                messages = result.scalars().all()

                # Return in chronological order (oldest first)
                return [self._db_message_to_model(msg) for msg in reversed(messages)]

        except Exception as e:
            logger.exception(f"Failed to get recent messages: {e}")
            raise MemoryBackendError(f"Failed to get recent messages: {e}")

    # =========================================================================
    # CROSS-CHANNEL OPERATIONS
    # =========================================================================

    async def get_user_history(
        self,
        user_id: str,
        channels: list[ConversationChannel] | None = None,
        limit: int = 50,
        days: int | None = None,
    ) -> list[ConversationMessage]:
        """Get user's conversation history across all channels"""

        try:
            async with get_db_context() as db:
                # Get user's conversations
                conv_query = select(AIConversation.id).where(AIConversation.user_id == user_id)

                if channels:
                    channel_values = [ch.value for ch in channels]
                    conv_query = conv_query.where(AIConversation.channel.in_(channel_values))

                result = await db.execute(conv_query)
                conversation_ids = [row[0] for row in result.all()]

                if not conversation_ids:
                    return []

                # Get messages from these conversations
                msg_query = select(AIMessage).where(AIMessage.conversation_id.in_(conversation_ids))

                if days:
                    cutoff = datetime.utcnow() - timedelta(days=days)
                    msg_query = msg_query.where(AIMessage.timestamp >= cutoff)

                msg_query = msg_query.order_by(AIMessage.timestamp.desc()).limit(limit)

                result = await db.execute(msg_query)
                messages = result.scalars().all()

                # Return in chronological order
                return [self._db_message_to_model(msg) for msg in reversed(messages)]

        except Exception as e:
            logger.exception(f"Failed to get user history: {e}")
            raise MemoryBackendError(f"Failed to get user history: {e}")

    async def get_user_conversations(
        self, user_id: str, include_inactive: bool = False
    ) -> list[ConversationMetadata]:
        """Get all conversations for a user"""

        try:
            async with get_db_context() as db:
                query = select(AIConversation).where(AIConversation.user_id == user_id)

                if not include_inactive:
                    query = query.where(AIConversation.is_active)

                query = query.order_by(AIConversation.last_message_at.desc())

                result = await db.execute(query)
                conversations = result.scalars().all()

                return [self._db_conversation_to_metadata(conv) for conv in conversations]

        except Exception as e:
            logger.exception(f"Failed to get user conversations: {e}")
            raise MemoryBackendError(f"Failed to get user conversations: {e}")

    # =========================================================================
    # CONVERSATION MANAGEMENT
    # =========================================================================

    async def get_conversation_metadata(self, conversation_id: str) -> ConversationMetadata | None:
        """Get conversation metadata"""

        try:
            async with get_db_context() as db:
                conversation = await db.get(AIConversation, conversation_id)

                if not conversation:
                    return None

                return self._db_conversation_to_metadata(conversation)

        except Exception as e:
            logger.exception(f"Failed to get conversation metadata: {e}")
            raise MemoryBackendError(f"Failed to get metadata: {e}")

    async def update_conversation_metadata(
        self,
        conversation_id: str,
        context: dict[str, Any] | None = None,
        emotion_score: float | None = None,
        escalated: bool | None = None,
    ) -> None:
        """Update conversation metadata"""

        try:
            async with get_db_context() as db:
                conversation = await db.get(AIConversation, conversation_id)

                if not conversation:
                    raise MemoryNotFoundError(f"Conversation {conversation_id} not found")

                if context is not None:
                    # Update context and mark as modified for SQLAlchemy to track JSONB changes
                    conversation.context.update(context)
                    attributes.flag_modified(conversation, "context")

                if emotion_score is not None:
                    await self._update_emotion_stats(db, conversation, emotion_score)

                if escalated is not None and escalated and not conversation.escalated:
                    conversation.escalated = True
                    conversation.escalated_at = datetime.utcnow()
                    logger.warning(f"Conversation {conversation_id} escalated to human agent")

                await db.commit()

        except MemoryNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Failed to update conversation metadata: {e}")
            raise MemoryBackendError(f"Failed to update metadata: {e}")

    async def close_conversation(self, conversation_id: str, reason: str | None = None) -> None:
        """Mark conversation as closed"""

        try:
            async with get_db_context() as db:
                conversation = await db.get(AIConversation, conversation_id)

                if not conversation:
                    raise MemoryNotFoundError(f"Conversation {conversation_id} not found")

                conversation.is_active = False
                conversation.closed_at = datetime.utcnow()
                conversation.closed_reason = reason

                await db.commit()

                logger.info(f"Closed conversation {conversation_id}: {reason}")

        except MemoryNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Failed to close conversation: {e}")
            raise MemoryBackendError(f"Failed to close conversation: {e}")

    # =========================================================================
    # EMOTION TRACKING
    # =========================================================================

    async def get_emotion_history(
        self, conversation_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get emotion score history for conversation.
        Optimized to only SELECT emotion columns for faster query execution.
        """

        try:
            async with get_db_context() as db:
                # OPTIMIZATION: Only select needed columns to enable covering index
                query = (
                    select(
                        AIMessage.timestamp,
                        AIMessage.emotion_score,
                        AIMessage.emotion_label,
                        AIMessage.detected_emotions,
                    )
                    .where(
                        and_(
                            AIMessage.conversation_id == conversation_id,
                            AIMessage.emotion_score.isnot(None),
                        )
                    )
                    .order_by(AIMessage.timestamp.desc())
                    .limit(limit)
                )

                result = await db.execute(query)
                rows = result.all()

                # Return emotion history in chronological order
                emotion_history = []
                for row in reversed(rows):  # Reverse for chronological order
                    emotion_history.append(
                        {
                            "timestamp": row.timestamp,
                            "score": row.emotion_score,
                            "label": row.emotion_label,
                            "emotions": row.detected_emotions or [],
                        }
                    )

                return emotion_history

        except Exception as e:
            logger.exception(f"Failed to get emotion history: {e}")
            raise MemoryBackendError(f"Failed to get emotion history: {e}")

    async def get_escalated_conversations(
        self, channel: ConversationChannel | None = None, hours: int = 24
    ) -> list[ConversationMetadata]:
        """Get conversations escalated to human agents"""

        try:
            async with get_db_context() as db:
                cutoff = datetime.utcnow() - timedelta(hours=hours)

                query = select(AIConversation).where(
                    and_(AIConversation.escalated, AIConversation.escalated_at >= cutoff)
                )

                if channel:
                    query = query.where(AIConversation.channel == channel.value)

                query = query.order_by(AIConversation.escalated_at.desc())

                result = await db.execute(query)
                conversations = result.scalars().all()

                return [self._db_conversation_to_metadata(conv) for conv in conversations]

        except Exception as e:
            logger.exception(f"Failed to get escalated conversations: {e}")
            raise MemoryBackendError(f"Failed to get escalated conversations: {e}")

    # =========================================================================
    # CONTEXT MANAGEMENT
    # =========================================================================

    async def get_context_window(
        self, conversation_id: str, max_tokens: int = 4000
    ) -> list[ConversationMessage]:
        """
        Get messages that fit within token budget.
        Uses simple heuristic: ~4 characters = 1 token
        """

        try:
            # Get recent messages (newest first)
            async with get_db_context() as db:
                query = (
                    select(AIMessage)
                    .where(AIMessage.conversation_id == conversation_id)
                    .order_by(AIMessage.timestamp.desc())
                    .limit(50)  # Maximum to consider
                )

                result = await db.execute(query)
                messages = result.scalars().all()

                # Calculate tokens and build context window
                context = []
                estimated_tokens = 0

                for msg in messages:
                    # Estimate tokens (rough approximation)
                    msg_tokens = len(msg.content) // 4

                    if estimated_tokens + msg_tokens > max_tokens:
                        break

                    context.append(msg)
                    estimated_tokens += msg_tokens

                # Return in chronological order
                return [self._db_message_to_model(msg) for msg in reversed(context)]

        except Exception as e:
            logger.exception(f"Failed to get context window: {e}")
            raise MemoryBackendError(f"Failed to get context window: {e}")

    # =========================================================================
    # STATISTICS
    # =========================================================================

    async def get_statistics(self, user_id: str | None = None, days: int = 30) -> dict[str, Any]:
        """Get memory usage statistics"""

        try:
            async with get_db_context() as db:
                cutoff = datetime.utcnow() - timedelta(days=days)

                # Base query filters
                conv_filter = AIConversation.started_at >= cutoff
                msg_filter = AIMessage.timestamp >= cutoff

                if user_id:
                    conv_filter = and_(conv_filter, AIConversation.user_id == user_id)

                # Total conversations
                result = await db.execute(
                    select(func.count()).select_from(AIConversation).where(conv_filter)
                )
                total_conversations = result.scalar()

                # Active conversations
                result = await db.execute(
                    select(func.count())
                    .select_from(AIConversation)
                    .where(and_(conv_filter, AIConversation.is_active))
                )
                active_conversations = result.scalar()

                # Total messages
                query = select(func.count()).select_from(AIMessage).where(msg_filter)
                if user_id:
                    query = query.join(AIConversation).where(AIConversation.user_id == user_id)

                result = await db.execute(query)
                total_messages = result.scalar()

                # Average emotion score
                query = select(func.avg(AIMessage.emotion_score)).where(
                    and_(msg_filter, AIMessage.emotion_score.isnot(None))
                )
                if user_id:
                    query = query.join(AIConversation).where(AIConversation.user_id == user_id)

                result = await db.execute(query)
                avg_emotion = result.scalar() or 0.5

                # Escalation rate
                result = await db.execute(
                    select(func.count())
                    .select_from(AIConversation)
                    .where(and_(conv_filter, AIConversation.escalated))
                )
                escalated_count = result.scalar()
                escalation_rate = (
                    escalated_count / total_conversations if total_conversations > 0 else 0
                )

                # Channel breakdown
                query = (
                    select(AIMessage.channel, func.count())
                    .where(msg_filter)
                    .group_by(AIMessage.channel)
                )
                if user_id:
                    query = query.join(AIConversation).where(AIConversation.user_id == user_id)

                result = await db.execute(query)
                channels = {row[0]: row[1] for row in result.all()}

                return {
                    "total_conversations": total_conversations,
                    "total_messages": total_messages,
                    "active_conversations": active_conversations,
                    "average_messages_per_conversation": (
                        total_messages / total_conversations if total_conversations > 0 else 0
                    ),
                    "average_emotion_score": float(avg_emotion),
                    "escalation_rate": float(escalation_rate),
                    "channels": channels,
                    "period_days": days,
                }

        except Exception as e:
            logger.exception(f"Failed to get statistics: {e}")
            raise MemoryBackendError(f"Failed to get statistics: {e}")

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    async def _update_emotion_stats(
        self, db: AsyncSession, conversation: AIConversation, new_score: float
    ) -> None:
        """Update conversation emotion statistics"""

        # Get recent emotion scores (DESC order - newest first)
        query = (
            select(AIMessage.emotion_score)
            .where(
                and_(
                    AIMessage.conversation_id == conversation.id,
                    AIMessage.emotion_score.isnot(None),
                )
            )
            .order_by(AIMessage.timestamp.desc())
            .limit(10)
        )

        result = await db.execute(query)
        existing_scores = [row[0] for row in result.all()]

        # Add new score at the beginning (it's the newest)
        all_scores = [new_score, *existing_scores]

        # Calculate average
        conversation.average_emotion_score = sum(all_scores) / len(all_scores)

        # Determine trend (need at least 4 scores to compare recent vs older)
        if len(all_scores) >= 4:
            # Compare 2 most recent vs 2 older scores
            recent_avg = sum(all_scores[:2]) / 2
            older_avg = sum(all_scores[2:4]) / 2

            diff = recent_avg - older_avg

            # More sensitive threshold for better detection
            if diff > 0.15:
                conversation.emotion_trend = "improving"
            elif diff < -0.15:
                conversation.emotion_trend = "declining"
            else:
                conversation.emotion_trend = "stable"
        elif len(all_scores) >= 2:
            # With only 2-3 scores, compare first vs last
            diff = all_scores[0] - all_scores[-1]
            if diff > 0.15:
                conversation.emotion_trend = "improving"
            elif diff < -0.15:
                conversation.emotion_trend = "declining"
            else:
                conversation.emotion_trend = "stable"
        else:
            # Not enough data for trend
            conversation.emotion_trend = "stable"

    async def _update_emotion_stats_background(
        self, conversation_id: str, new_score: float
    ) -> None:
        """
        Background task to update emotion statistics without blocking message storage.
        This runs asynchronously after the message is stored.
        """
        try:
            async with get_db_context() as db:
                # Get conversation
                conversation = await db.get(AIConversation, conversation_id)
                if not conversation:
                    logger.warning(
                        f"Conversation {conversation_id} not found for emotion stats update"
                    )
                    return

                # Update emotion stats
                await self._update_emotion_stats(db, conversation, new_score)
                await db.commit()

                logger.debug(
                    f"Updated emotion stats for conversation {conversation_id} in background"
                )

        except Exception as e:
            logger.exception(
                f"Failed to update emotion stats in background for {conversation_id}: {e}"
            )
            # Don't raise - this is a background task, failures are logged but don't affect user

    def _db_message_to_model(self, db_message: AIMessage) -> ConversationMessage:
        """Convert database message to ConversationMessage model"""
        return ConversationMessage(
            id=db_message.id,
            conversation_id=db_message.conversation_id,
            role=MessageRole(db_message.role),
            content=db_message.content,
            timestamp=db_message.timestamp,
            metadata=db_message.message_metadata,
            channel=ConversationChannel(db_message.channel),
            emotion_score=db_message.emotion_score,
            emotion_label=db_message.emotion_label,
            detected_emotions=db_message.detected_emotions,
            input_tokens=db_message.input_tokens,
            output_tokens=db_message.output_tokens,
            tool_calls=db_message.tool_calls,
            tool_results=db_message.tool_results,
        )

    def _db_conversation_to_metadata(self, db_conv: AIConversation) -> ConversationMetadata:
        """Convert database conversation to ConversationMetadata model"""
        return ConversationMetadata(
            conversation_id=db_conv.id,
            user_id=db_conv.user_id,
            channel=ConversationChannel(db_conv.channel),
            started_at=db_conv.started_at,
            last_message_at=db_conv.last_message_at,
            message_count=db_conv.message_count,
            context=db_conv.context,
            average_emotion_score=db_conv.average_emotion_score,
            emotion_trend=db_conv.emotion_trend,
            escalated=db_conv.escalated,
            escalated_at=db_conv.escalated_at,
            is_active=db_conv.is_active,
            closed_at=db_conv.closed_at,
            closed_reason=db_conv.closed_reason,
        )
