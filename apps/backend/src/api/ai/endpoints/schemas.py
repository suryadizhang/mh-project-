"""
Pydantic models for API requests and responses
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class ChannelType(str, Enum):
    """Channel types for multi-channel support"""

    WEBSITE = "website"
    SMS = "sms"
    VOICE = "voice"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    EMAIL = "email"


class MessageRole(str, Enum):
    """Message roles in conversation"""

    USER = "user"
    AI = "ai"
    GPT = "gpt"
    HUMAN = "human"
    SYSTEM = "system"


# Chat Ingest Request/Response Models
class ChatIngestRequest(BaseModel):
    """Request model for /chat/ingest endpoint"""

    channel: ChannelType
    user_id: str = Field(..., description="External user identifier (phone, FB ID, etc.)")
    thread_id: str = Field(..., description="Channel-specific thread identifier")
    text: str = Field(..., min_length=1, max_length=2000)
    metadata: dict[str, Any] | None = Field(
        default_factory=dict, description="Channel-specific metadata"
    )


class ChatIngestResponse(BaseModel):
    """Response model for /chat/ingest endpoint"""

    message_id: UUID
    conversation_id: UUID
    reply: str
    confidence: float
    source: str  # "our-ai", "gpt-nano", "gpt-4-1-mini", "human"
    processing_time_ms: int
    escalated: bool = False


# Chat Reply Request/Response Models
class ChatReplyRequest(BaseModel):
    """Internal request model for /chat/reply endpoint"""

    conversation_id: UUID
    message: str
    context: list[dict[str, Any]] | None = Field(default_factory=list)


class ChatReplyResponse(BaseModel):
    """Response model for /chat/reply endpoint"""

    reply: str
    confidence: float
    source: str
    kb_sources: list[dict[str, Any]] = Field(default_factory=list)
    tokens_used: int | None = None
    cost_usd: float | None = None


# Escalation Models
class EscalationRequest(BaseModel):
    """Request model for /chat/escalate endpoint"""

    conversation_id: UUID
    reason: str
    priority: int | None = Field(default=1, ge=1, le=5)


class EscalationResponse(BaseModel):
    """Response model for /chat/escalate endpoint"""

    success: bool
    message: str
    escalated_at: datetime


# WebSocket Models
class WebSocketMessage(BaseModel):
    """WebSocket message format"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "message",
                "content": "Hello, how can I help?",
                "role": "assistant",
                "timestamp": "2024-10-25T10:30:00Z",
            }
        }
    )

    type: str  # "message", "typing", "takeover", "system"
    conversation_id: UUID | None = None
    content: str
    role: MessageRole | None = None
    timestamp: datetime = Field(description="Message timestamp")
    metadata: dict[str, Any] | None = None

    @classmethod
    def create(
        cls,
        type: str,
        content: str,
        conversation_id: UUID | None = None,
        role: MessageRole | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "WebSocketMessage":
        """Factory method to create WebSocketMessage with automatic timestamp."""
        return cls(
            type=type,
            content=content,
            conversation_id=conversation_id,
            role=role,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata,
        )


# Knowledge Base Models
class KBChunkCreate(BaseModel):
    """Request model for creating KB chunks"""

    title: str = Field(..., max_length=500)
    text: str = Field(..., max_length=5000)
    tags: list[str] = Field(default_factory=list)
    category: str | None = None
    source_type: str | None = "manual"


class KBChunkResponse(BaseModel):
    """Response model for KB chunks"""

    id: UUID
    title: str
    text: str
    tags: list[str]
    category: str | None
    usage_count: int
    success_rate: float
    created_at: datetime


class KBSearchRequest(BaseModel):
    """Request model for KB search"""

    query: str = Field(..., min_length=1, max_length=500)
    limit: int | None = Field(default=5, ge=1, le=20)
    category: str | None = None
    min_score: float | None = Field(default=0.5, ge=0.0, le=1.0)


class KBSearchResponse(BaseModel):
    """Response model for KB search"""

    chunks: list[dict[str, Any]]
    total_results: int
    query_time_ms: int


# Analytics Models
class ConversationAnalytics(BaseModel):
    """Conversation analytics response"""

    conversation_id: UUID
    total_messages: int
    ai_messages: int
    human_messages: int
    avg_confidence: float | None
    resolution_status: str | None
    first_response_time_seconds: int | None
    resolution_time_seconds: int | None
    total_cost_usd: float


# Training Data Models
class TrainingDataCreate(BaseModel):
    """Request model for creating training data"""

    question: str = Field(..., max_length=1000)
    answer: str = Field(..., max_length=2000)
    tags: list[str] = Field(default_factory=list)
    intent: str | None = None
    source_type: str = "manual"
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)


# Legacy compatibility models (for existing frontend)
class ChatRequest(BaseModel):
    """Legacy chat request model"""

    message: str
    page: str
    consent_to_save: bool | None = False
    city: str | None = None


class ChatResponse(BaseModel):
    """Legacy chat response model"""

    answer: str
    confidence: float
    route: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    can_escalate: bool = True
    log_id: str | None = None


class FeedbackRequest(BaseModel):
    """Legacy feedback request model"""

    log_id: str
    feedback: str
    suggestion: str | None = None
