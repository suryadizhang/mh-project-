"""
AI Chat API endpoints for frontend integration.
Provides REST endpoints for chat functionality, conversation management, and knowledge base interaction.
Integrates role-based AI services for customer booking and admin management.
"""

from datetime import datetime, timezone
import logging
from uuid import uuid4

from api.ai.endpoints.database import get_db
from db.models.ai.conversations import UnifiedConversation as Conversation, UnifiedMessage as AIMessage
from api.ai.endpoints.services.admin_management_ai import admin_management_ai
from api.ai.endpoints.services.chat_service import ChatService
from api.ai.endpoints.services.customer_booking_ai import customer_booking_ai
from api.ai.endpoints.services.role_based_ai import UserRole
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


# Role-based AI routing functions
async def route_ai_message(message: str, user_role: UserRole, context: dict) -> dict:
    """Route message to appropriate AI service based on user role"""
    try:
        if user_role == UserRole.CUSTOMER:
            # Route to customer booking AI
            return await customer_booking_ai.process_customer_message(message, context)
        elif user_role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF]:
            # Route to admin management AI
            return await admin_management_ai.process_admin_message(message, context)
        else:
            # Fallback to general response
            return {
                "response": "Hello! I'm MyHibachi's AI assistant. How can I help you today?",
                "intent": "general",
                "confidence": 0.7,
            }
    except Exception as e:
        logger.exception(f"Error routing AI message: {e}")
        return {
            "response": "I'm sorry, I'm having trouble processing your request. Please try again.",
            "intent": "error",
            "confidence": 0.0,
        }


def generate_role_based_suggestions(user_role: UserRole, intent: str) -> list[str]:
    """Generate suggestions based on user role and detected intent"""
    if user_role == UserRole.CUSTOMER:
        if intent in ["create_booking", "booking_general"]:
            return [
                "Book a table for tonight",
                "Change my reservation",
                "View my bookings",
                "Cancel a booking",
            ]
        elif intent == "general_inquiry":
            return [
                "Show me the menu",
                "What are your hours?",
                "Make a reservation",
                "Where are you located?",
            ]
        else:
            return ["Make a reservation", "View menu", "Restaurant information", "Contact details"]
    elif user_role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF]:
        if intent == "user_management":
            return ["View all users", "Create new user", "Reset user password", "User analytics"]
        elif intent == "booking_management":
            return [
                "View all bookings",
                "Create admin booking",
                "Booking analytics",
                "Manage availability",
            ]
        elif intent == "staff_management":
            return ["View staff overview", "Manage schedules", "Staff performance", "Add new staff"]
        else:
            return [
                "User management",
                "Booking management",
                "Staff management",
                "Operations",
                "Analytics",
                "System settings",
            ]
    else:
        return ["How can I help you?", "Tell me what you need", "Ask me anything"]


# Pydantic models for request/response
class ChatMessageRequest(BaseModel):
    """Request model for sending a chat message."""

    message: str = Field(..., min_length=1, max_length=4000, description="The user's message")
    conversation_id: str | None = Field(
        None, description="Optional conversation ID to continue existing conversation"
    )
    channel: str = Field(default="web", description="Channel identifier (web, admin, mobile)")
    user_id: str | None = Field(None, description="Optional user identifier for personalization")
    user_role: str | None = Field(
        default="customer", description="User role (customer, admin, staff, super_admin)"
    )
    context: dict | None = Field(
        default_factory=dict, description="Additional context for the conversation"
    )


class ChatMessageResponse(BaseModel):
    """Response model for chat messages."""

    message_id: str = Field(..., description="Unique identifier for this message")
    conversation_id: str = Field(..., description="Conversation identifier")
    content: str = Field(..., description="AI response content")
    timestamp: datetime = Field(..., description="Message timestamp")
    channel: str = Field(..., description="Channel identifier")
    user_role: str = Field(..., description="User role that generated this response")
    intent: str | None = Field(None, description="Detected user intent")
    confidence: float | None = Field(None, description="AI confidence score (0-1)")
    suggestions: list[str] | None = Field(None, description="Suggested follow-up questions")
    actions: list[dict] | None = Field(None, description="Available actions based on response")


@router.post("/chat", response_model=ChatMessageResponse, status_code=status.HTTP_200_OK)
async def send_chat_message(
    request: ChatMessageRequest, db: Session = Depends(get_db)
) -> ChatMessageResponse:
    """
    Send a chat message and get AI response based on user role and capabilities.

    This endpoint accepts a user message and returns an AI-generated response.
    It handles conversation continuity, context management, and role-based AI routing.
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid4())
        message_id = str(uuid4())

        # Parse user role
        try:
            user_role = UserRole(request.user_role.lower())
        except (ValueError, AttributeError):
            user_role = UserRole.CUSTOMER

        # Prepare context for AI processing
        context = {
            "user_id": request.user_id,
            "user_role": user_role,
            "channel": request.channel,
            "conversation_id": conversation_id,
            **request.context,
        }

        # Route to appropriate AI service based on role and message
        ai_response = await route_ai_message(request.message, user_role, context)

        # Extract response components
        response_content = ai_response.get(
            "response", "I'm sorry, I couldn't process your request."
        )
        intent = ai_response.get("intent", "general")
        confidence = ai_response.get("confidence", 0.8)
        suggestions = generate_role_based_suggestions(user_role, intent)
        actions = ai_response.get("actions", [])

        # Log the interaction for monitoring
        logger.info(
            f"AI Chat - Role: {user_role.value}, Intent: {intent}, Channel: {request.channel}"
        )

        # Return structured response
        return ChatMessageResponse(
            message_id=message_id,
            conversation_id=conversation_id,
            content=response_content,
            timestamp=datetime.now(timezone.utc),
            channel=request.channel,
            user_role=user_role.value,
            intent=intent,
            confidence=confidence,
            suggestions=suggestions,
            actions=actions,
        )

    except Exception as e:
        logger.exception(f"Error processing chat message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process chat message. Please try again.",
        )


@router.get("/conversations")
async def get_conversations(
    limit: int = Query(default=50, le=100, description="Maximum number of conversations to return"),
    offset: int = Query(default=0, ge=0, description="Number of conversations to skip"),
    channel: str | None = Query(None, description="Filter by channel"),
    db: Session = Depends(get_db),
):
    """
    Get list of conversations with pagination.

    Returns a paginated list of conversations, optionally filtered by channel.
    """
    try:
        # Build query
        query = db.query(Conversation)

        if channel:
            query = query.filter(Conversation.channel == channel)

        # Apply pagination
        conversations = query.offset(offset).limit(limit).all()

        # Convert to response format
        response_conversations = []
        for conv in conversations:
            # Get message count for each conversation
            message_count = db.query(AIMessage).filter(AIMessage.conversation_id == conv.id).count()

            response_conversations.append(
                {
                    "conversation_id": conv.id,
                    "channel": conv.channel,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                    "message_count": message_count,
                    "status": conv.status,
                }
            )

        return response_conversations

    except Exception as e:
        logger.exception(f"Error retrieving conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve conversations.",
        )


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """
    Get details of a specific conversation.

    Returns detailed information about a conversation including metadata.
    """
    try:
        # Find conversation
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

        # Get message count
        message_count = db.query(Message).filter(Message.conversation_id == conversation_id).count()

        return {
            "conversation_id": conversation.id,
            "channel": conversation.channel,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "message_count": message_count,
            "status": conversation.status,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve conversation.",
        )


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(default=50, le=100, description="Maximum number of messages to return"),
    offset: int = Query(default=0, ge=0, description="Number of messages to skip"),
    db: Session = Depends(get_db),
):
    """
    Get messages from a specific conversation.

    Returns paginated list of messages for a conversation, ordered by timestamp.
    """
    try:
        # Verify conversation exists
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

        # Get messages with pagination
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Convert to response format
        response_messages = []
        for msg in messages:
            response_messages.append(
                {
                    "message_id": msg.id,
                    "conversation_id": msg.conversation_id,
                    "content": msg.text,
                    "sender": msg.role,
                    "timestamp": msg.created_at,
                    "channel": conversation.channel,
                }
            )

        return response_messages

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving messages for conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve conversation messages.",
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def chat_health_check():
    """
    Health check endpoint for chat service.

    Returns the status of the chat service components.
    """
    try:
        # Test chat service initialization
        ChatService()

        return {
            "status": "healthy",
            "service": "ai-chat-api",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
        }

    except Exception as e:
        logger.exception(f"Chat service health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Chat service is not available"
        )


# Export router
__all__ = ["router"]
