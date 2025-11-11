"""
Conversation Service for AI Orchestrator

Phase 1: Basic conversation context (message only)
Phase 3: Full threading with conversation history (IF follow_up_rate >50%)

This service provides conversation context to the AI. In Phase 1, it only
tracks the current message. In Phase 3, it will maintain full conversation
threads with history and context merging.

Author: MyHibachi Development Team
Created: October 31, 2025
"""

from datetime import datetime
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Manage conversation context and threading.

    Phase 1 (Current):
    - Single message context
    - No history tracking
    - Simple conversation ID

    Phase 3 (Future - IF follow_up_rate >50%):
    - Full conversation threading
    - Multi-message history
    - Context summarization
    - Follow-up detection
    - Conversation merging across channels

    Decision Criteria for Phase 3:
    - Build ONLY if >50% of inquiries have follow-ups
    - Data collection in Phase 2 will validate need
    - Investment: $3,000, Timeline: 1 week
    """

    def __init__(self, enable_threading: bool = False):
        """
        Initialize conversation service.

        Args:
            enable_threading: Enable Phase 3 threading features (default: False)
        """
        self.enable_threading = enable_threading
        self.logger = logging.getLogger(__name__)

        if enable_threading:
            self.logger.warning(
                "Threading is enabled but not yet implemented. "
                "This will be built in Phase 3 if follow_up_rate >50%"
            )

    async def get_conversation_history(
        self, conversation_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get conversation history for context.

        Phase 1: Returns empty list (no history tracking)
        Phase 3: Returns last N messages in conversation

        Args:
            conversation_id: Conversation identifier
            limit: Maximum messages to return

        Returns:
            List of conversation messages (empty in Phase 1)
        """
        if not self.enable_threading:
            # Phase 1: No history tracking
            self.logger.debug(f"Threading disabled - returning empty history for {conversation_id}")
            return []

        # Phase 3: Full history retrieval (placeholder)
        self.logger.info(f"Would retrieve history for conversation {conversation_id} (Phase 3)")
        return []

    async def create_conversation(self, customer_id: str | None, channel: str, message: str) -> str:
        """
        Create new conversation thread.

        Phase 1: Generates simple conversation ID
        Phase 3: Creates thread in database with metadata

        Args:
            customer_id: Customer identifier (if known)
            channel: Communication channel (email, phone, etc.)
            message: Initial message

        Returns:
            Conversation ID
        """
        # Phase 1: Simple timestamp-based ID
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.logger.info(
            f"Created conversation: {conversation_id}",
            extra={
                "customer_id": customer_id,
                "channel": channel,
                "threading_enabled": self.enable_threading,
            },
        )

        return conversation_id

    async def add_message(
        self, conversation_id: str, role: str, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Add message to conversation.

        Phase 1: No-op (messages not stored)
        Phase 3: Stores message in database

        Args:
            conversation_id: Conversation identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional metadata
        """
        if not self.enable_threading:
            # Phase 1: Don't store messages
            self.logger.debug(f"Threading disabled - not storing message for {conversation_id}")
            return

        # Phase 3: Store message (placeholder)
        self.logger.info(
            f"Would store message in conversation {conversation_id} (Phase 3)", extra={"role": role}
        )

    async def detect_follow_up(self, conversation_id: str, message: str) -> bool:
        """
        Detect if message is a follow-up to existing conversation.

        Phase 1: Always returns False (no follow-up detection)
        Phase 3: Analyzes message for follow-up indicators

        Args:
            conversation_id: Conversation identifier
            message: New message

        Returns:
            True if message is a follow-up
        """
        if not self.enable_threading:
            # Phase 1: No follow-up detection
            return False

        # Phase 3: Follow-up detection (placeholder)
        # Would analyze for keywords like:
        # - "also", "additionally", "and"
        # - References to previous topics
        # - Time proximity to last message
        return False

    async def summarize_conversation(self, conversation_id: str) -> str | None:
        """
        Generate conversation summary for AI context.

        Phase 1: Returns None (no summarization)
        Phase 3: Uses GPT to summarize long conversations

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation summary or None
        """
        if not self.enable_threading:
            # Phase 1: No summarization
            return None

        # Phase 3: Summarization (placeholder)
        # Would use GPT-4 to create concise summary of:
        # - Customer requirements
        # - Decisions made
        # - Open questions
        return None

    def get_service_status(self) -> dict[str, Any]:
        """
        Get conversation service status.

        Returns:
            Service status information
        """
        return {
            "service": "ConversationService",
            "phase": "Phase 1" if not self.enable_threading else "Phase 3",
            "threading_enabled": self.enable_threading,
            "features": {
                "conversation_history": self.enable_threading,
                "follow_up_detection": self.enable_threading,
                "summarization": self.enable_threading,
            },
            "phase_3_requirements": {
                "build_if": "follow_up_rate > 50%",
                "investment": "$3,000",
                "timeline": "1 week",
                "data_collection": "Phase 2 (Month 1-2)",
            },
        }


# Singleton instance
_conversation_service: ConversationService | None = None


def get_conversation_service(enable_threading: bool = False) -> ConversationService:
    """
    Get conversation service singleton.

    Args:
        enable_threading: Enable Phase 3 threading (default: False)

    Returns:
        ConversationService instance
    """
    global _conversation_service

    if _conversation_service is None:
        _conversation_service = ConversationService(enable_threading=enable_threading)

    return _conversation_service
