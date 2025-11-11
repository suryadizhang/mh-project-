"""
Abstract Memory Backend Interface
=================================

Provider-agnostic interface for conversation memory storage and retrieval.
Inspired by ModelProvider architecture for zero-code backend swapping.

Supported Backends:
- PostgreSQL (with JSONB storage) - Production
- Neo4j (graph-based) - Option 2 stub

Key Features:
- Cross-channel conversation history
- Emotion tracking integration
- Semantic search (future)
- Context window management
- User profile integration
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# EXCEPTIONS
# =============================================================================


class MemoryBackendError(Exception):
    """Base exception for memory backend errors"""


class MemoryNotFoundError(MemoryBackendError):
    """Raised when conversation or message not found"""


class MemoryConnectionError(MemoryBackendError):
    """Raised when backend connection fails"""


# =============================================================================
# DATA MODELS
# =============================================================================


class MessageRole(str, Enum):
    """Message role in conversation"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ConversationChannel(str, Enum):
    """Communication channel"""

    WEB = "web"
    EMAIL = "email"
    SMS = "sms"
    VOICE = "voice"
    WHATSAPP = "whatsapp"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class ConversationMessage(BaseModel):
    """Single message in a conversation"""

    id: str | None = None
    conversation_id: str
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)
    channel: ConversationChannel = ConversationChannel.WEB

    # Emotion tracking (from EmotionService)
    emotion_score: float | None = None  # 0.0-1.0
    emotion_label: str | None = None  # negative/neutral/positive
    detected_emotions: list[str] | None = None

    # Token tracking
    input_tokens: int | None = None
    output_tokens: int | None = None

    # Tool usage
    tool_calls: list[dict] | None = None
    tool_results: list[dict] | None = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ConversationMetadata(BaseModel):
    """Conversation-level metadata"""

    conversation_id: str
    user_id: str | None = None
    channel: ConversationChannel
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0

    # Context
    context: dict[str, Any] = Field(default_factory=dict)

    # Emotion tracking
    average_emotion_score: float | None = None
    emotion_trend: str | None = None  # improving/declining/stable
    escalated: bool = False
    escalated_at: datetime | None = None

    # Status
    is_active: bool = True
    closed_at: datetime | None = None
    closed_reason: str | None = None


class MemorySearchResult(BaseModel):
    """Search result with relevance scoring"""

    message: ConversationMessage
    relevance_score: float  # 0.0-1.0 (for semantic search)
    conversation_metadata: ConversationMetadata | None = None


# =============================================================================
# ABSTRACT MEMORY BACKEND
# =============================================================================


class MemoryBackend(ABC):
    """
    Abstract base class for conversation memory backends.

    Inspired by ModelProvider architecture for consistent interface
    across different storage backends (PostgreSQL, Neo4j, etc.)

    Implementations must:
    1. Store and retrieve conversation messages
    2. Support cross-channel history
    3. Track emotion scores
    4. Manage context windows
    5. Provide health checks
    """

    def __init__(self, **kwargs):
        """Initialize memory backend with configuration"""
        self._initialized = False
        logger.info(f"Initializing {self.__class__.__name__} memory backend")

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize backend connection and resources.
        Called once at startup.
        """

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """
        Check backend health and connection status.

        Returns:
            {
                "status": "healthy" | "degraded" | "unhealthy",
                "backend": "postgresql" | "neo4j",
                "latency_ms": 123,
                "message_count": 45678,
                "error": "optional error message"
            }
        """

    @abstractmethod
    async def close(self) -> None:
        """Close backend connection and cleanup resources"""

    # =========================================================================
    # MESSAGE OPERATIONS
    # =========================================================================

    @abstractmethod
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
        """
        Store a single message in conversation history.

        Args:
            conversation_id: Unique conversation identifier
            role: Message role (user/assistant/system/tool)
            content: Message content
            metadata: Additional metadata (tool calls, context, etc.)
            channel: Communication channel
            emotion_score: Emotion score from EmotionService (0.0-1.0)
            emotion_label: Emotion label (negative/neutral/positive)
            detected_emotions: List of detected emotions
            user_id: User identifier for cross-conversation tracking

        Returns:
            Created ConversationMessage with generated ID
        """

    @abstractmethod
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int | None = None,
        offset: int = 0,
        include_system: bool = True,
    ) -> list[ConversationMessage]:
        """
        Retrieve conversation history.

        Args:
            conversation_id: Conversation ID
            limit: Maximum messages to return (None = all)
            offset: Number of messages to skip
            include_system: Include system messages

        Returns:
            List of messages ordered by timestamp (oldest first)
        """

    @abstractmethod
    async def get_recent_messages(
        self, conversation_id: str, count: int = 10
    ) -> list[ConversationMessage]:
        """
        Get N most recent messages in conversation.
        Optimized for context window management.

        Args:
            conversation_id: Conversation ID
            count: Number of recent messages

        Returns:
            List of recent messages (newest first)
        """

    # =========================================================================
    # CROSS-CHANNEL OPERATIONS
    # =========================================================================

    @abstractmethod
    async def get_user_history(
        self,
        user_id: str,
        channels: list[ConversationChannel] | None = None,
        limit: int = 50,
        days: int | None = None,
    ) -> list[ConversationMessage]:
        """
        Get user's conversation history across all channels.
        Critical for maintaining context when users switch channels.

        Args:
            user_id: User identifier
            channels: Filter by specific channels (None = all)
            limit: Maximum messages to return
            days: Only messages from last N days (None = all time)

        Returns:
            Combined history from all channels, ordered by timestamp
        """

    @abstractmethod
    async def get_user_conversations(
        self, user_id: str, include_inactive: bool = False
    ) -> list[ConversationMetadata]:
        """
        Get all conversations for a user.

        Args:
            user_id: User identifier
            include_inactive: Include closed conversations

        Returns:
            List of conversation metadata
        """

    # =========================================================================
    # CONVERSATION MANAGEMENT
    # =========================================================================

    @abstractmethod
    async def get_conversation_metadata(self, conversation_id: str) -> ConversationMetadata | None:
        """
        Get conversation metadata.

        Args:
            conversation_id: Conversation ID

        Returns:
            ConversationMetadata or None if not found
        """

    @abstractmethod
    async def update_conversation_metadata(
        self,
        conversation_id: str,
        context: dict[str, Any] | None = None,
        emotion_score: float | None = None,
        escalated: bool | None = None,
    ) -> None:
        """
        Update conversation metadata.

        Args:
            conversation_id: Conversation ID
            context: Update context dictionary
            emotion_score: Update emotion score (triggers trend calculation)
            escalated: Mark conversation as escalated
        """

    @abstractmethod
    async def close_conversation(self, conversation_id: str, reason: str | None = None) -> None:
        """
        Mark conversation as closed.

        Args:
            conversation_id: Conversation ID
            reason: Closure reason (completed/abandoned/escalated)
        """

    # =========================================================================
    # EMOTION TRACKING
    # =========================================================================

    @abstractmethod
    async def get_emotion_history(
        self, conversation_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get emotion score history for conversation.
        Used for emotion trend analysis.

        Args:
            conversation_id: Conversation ID
            limit: Maximum emotion records

        Returns:
            List of emotion records with timestamps
            [
                {
                    "timestamp": datetime,
                    "score": 0.75,
                    "label": "positive",
                    "emotions": ["joy", "satisfaction"]
                },
                ...
            ]
        """

    @abstractmethod
    async def get_escalated_conversations(
        self, channel: ConversationChannel | None = None, hours: int = 24
    ) -> list[ConversationMetadata]:
        """
        Get conversations that were escalated to human agents.

        Args:
            channel: Filter by channel (None = all)
            hours: From last N hours

        Returns:
            List of escalated conversation metadata
        """

    # =========================================================================
    # CONTEXT MANAGEMENT
    # =========================================================================

    @abstractmethod
    async def get_context_window(
        self, conversation_id: str, max_tokens: int = 4000
    ) -> list[ConversationMessage]:
        """
        Get messages that fit within token budget.
        Intelligent context window management for LLM APIs.

        Args:
            conversation_id: Conversation ID
            max_tokens: Maximum tokens (approximate)

        Returns:
            Most recent messages that fit in budget
        """

    # =========================================================================
    # SEARCH (Optional - for future semantic search)
    # =========================================================================

    async def search_conversations(
        self, query: str, user_id: str | None = None, limit: int = 10
    ) -> list[MemorySearchResult]:
        """
        Semantic search across conversations (optional, future feature).

        Args:
            query: Search query
            user_id: Filter by user
            limit: Maximum results

        Returns:
            Search results with relevance scores
        """
        # Default implementation returns empty (not all backends support search)
        logger.warning(f"{self.__class__.__name__} does not support semantic search")
        return []

    # =========================================================================
    # STATISTICS
    # =========================================================================

    @abstractmethod
    async def get_statistics(self, user_id: str | None = None, days: int = 30) -> dict[str, Any]:
        """
        Get memory usage statistics.

        Args:
            user_id: Filter by user (None = all users)
            days: Time period

        Returns:
            {
                "total_conversations": 123,
                "total_messages": 4567,
                "active_conversations": 45,
                "average_messages_per_conversation": 37.2,
                "average_emotion_score": 0.65,
                "escalation_rate": 0.08,
                "channels": {
                    "web": 2000,
                    "email": 1500,
                    "sms": 1067
                }
            }
        """
