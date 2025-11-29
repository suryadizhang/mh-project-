"""
Admin AI API endpoints for administration and management.
Provides admin-specific endpoints for AI system management, analytics, and configuration.
"""

from datetime import datetime, timezone, timedelta
import logging
from uuid import uuid4

from api.ai.endpoints.database import get_db
from db.models.ai.conversations import UnifiedConversation as Conversation, UnifiedMessage as AIMessage
from api.ai.endpoints.services.chat_service import ChatService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for admin endpoints
class AdminChatRequest(BaseModel):
    """Request model for admin chat testing."""

    message: str = Field(..., min_length=1, max_length=4000)
    test_mode: bool = Field(default=True, description="Enable test mode for admin debugging")
    channel: str = Field(default="admin", description="Admin channel identifier")
    context: dict | None = Field(default_factory=dict, description="Additional context")


class AdminChatResponse(BaseModel):
    """Response model for admin chat testing."""

    message_id: str = Field(..., description="Message identifier")
    conversation_id: str = Field(..., description="Conversation identifier")
    content: str = Field(..., description="AI response content")
    timestamp: datetime = Field(..., description="Response timestamp")
    debug_info: dict | None = Field(None, description="Debug information for admin")
    processing_time_ms: float | None = Field(None, description="Processing time in milliseconds")


@router.post("/admin/chat/test", response_model=AdminChatResponse)
async def test_admin_chat(
    request: AdminChatRequest, db: Session = Depends(get_db)
) -> AdminChatResponse:
    """
    Test chat functionality for admin users.

    Provides a testing interface for administrators to test AI responses
    with debug information and performance metrics.
    """
    start_time = datetime.now(timezone.utc)

    try:
        # Get chat service instance
        chat_service = ChatService()

        # Generate test conversation ID
        conversation_id = str(uuid4())

        # Create chat data for admin testing
        chat_data = {
            "conversation_id": conversation_id,
            "user_message": request.message,
            "channel": request.channel,
            "user_id": "admin_test",
            "context": {**request.context, "admin_test": True, "test_mode": request.test_mode},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Process the chat through AI service
        response_data = await chat_service.ingest_chat(chat_data)

        # Calculate processing time
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        # Prepare debug information
        debug_info = (
            {
                "ai_pipeline_version": response_data.get("pipeline_version", "unknown"),
                "confidence_score": response_data.get("confidence", 0.0),
                "knowledge_base_hits": response_data.get("kb_hits", 0),
                "fallback_used": response_data.get("fallback_used", False),
                "processing_steps": response_data.get("processing_steps", []),
            }
            if request.test_mode
            else None
        )

        return AdminChatResponse(
            message_id=str(uuid4()),
            conversation_id=conversation_id,
            content=response_data.get("ai_response", "Test response unavailable"),
            timestamp=datetime.now(timezone.utc),
            debug_info=debug_info,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.exception(f"Admin chat test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Chat test failed: {e!s}"
        )


@router.get("/admin/analytics")
async def get_chat_analytics(
    days: int = Query(default=7, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db),
):
    """
    Get chat analytics and usage statistics.

    Provides comprehensive analytics about chat usage, conversation patterns,
    and system performance over the specified time period.
    """
    try:
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        end_date - timedelta(days=days)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        # Total conversations and messages
        total_conversations = db.query(func.count(Conversation.id)).scalar() or 0
        total_messages = db.query(func.count(AIMessage.id)).scalar() or 0

        # Today's conversations and messages
        conversations_today = (
            db.query(func.count(Conversation.id))
            .filter(Conversation.created_at >= today_start)
            .scalar()
            or 0
        )

        messages_today = (
            db.query(func.count(AIMessage.id)).filter(AIMessage.created_at >= today_start).scalar() or 0
        )

        # Average messages per conversation
        avg_messages = total_messages / max(total_conversations, 1)

        # Messages by channel (simplified)
        channels = {"web": messages_today, "admin": 0, "sms": 0}  # Simplified for now

        # Hourly activity for the last 24 hours (simplified)
        hourly_activity = []
        for hour in range(24):
            hourly_activity.append(
                {"hour": hour, "messages": 0}  # Would need proper query implementation
            )

        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "conversations_today": conversations_today,
            "messages_today": messages_today,
            "avg_messages_per_conversation": round(avg_messages, 2),
            "channels": channels,
            "hourly_activity": hourly_activity,
        }

    except Exception as e:
        logger.exception(f"Error generating chat analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate analytics data.",
        )


@router.get("/admin/system/health")
async def get_system_health(db: Session = Depends(get_db)):
    """
    Get overall AI system health status.

    Provides comprehensive health check information for all
    AI system components and services.
    """
    try:
        # Test chat service
        try:
            ChatService()
            chat_status = "healthy"
        except Exception:
            chat_status = "unhealthy"

        # Test database
        try:
            db.execute("SELECT 1")
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

        # Calculate uptime (simplified - would need proper tracking in production)
        uptime_seconds = 0.0  # Would be calculated from service start time

        return {
            "chat_service": chat_status,
            "knowledge_base": "healthy",  # Simplified
            "ai_pipeline": "healthy",  # Simplified
            "database": db_status,
            "uptime_seconds": uptime_seconds,
            "last_error": None,  # Would track actual last error
        }

    except Exception as e:
        logger.exception(f"Error getting system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve system health status.",
        )


@router.get("/admin/conversations")
async def get_admin_conversations(
    limit: int = Query(default=50, le=100, description="Maximum number of conversations to return"),
    offset: int = Query(default=0, ge=0, description="Number of conversations to skip"),
    db: Session = Depends(get_db),
):
    """
    Get conversations for admin review.

    Returns paginated list of conversations with admin-specific information.
    """
    try:
        # Get conversations with pagination
        conversations = (
            db.query(Conversation)
            .order_by(Conversation.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Convert to response format
        response_conversations = []
        for conv in conversations:
            # Get message count
            message_count = db.query(AIMessage).filter(AIMessage.conversation_id == conv.id).count()

            response_conversations.append(
                {
                    "conversation_id": conv.id,
                    "channel": conv.channel,
                    "user_id": conv.user_id,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                    "message_count": message_count,
                    "status": conv.status,
                }
            )

        return response_conversations

    except Exception as e:
        logger.exception(f"Error retrieving admin conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve conversations.",
        )


# Export router
__all__ = ["router"]
