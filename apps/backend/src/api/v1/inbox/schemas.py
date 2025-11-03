"""
Unified Inbox API Schemas
Pydantic models for request/response validation
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    validator,
)

from .models import MessageChannel, MessageDirection, MessageStatus, TCPAStatus


# Base schemas
class MessageChannelSchema(BaseModel):
    """Message channel information"""

    channel: MessageChannel
    identifier: str  # phone, email, handle
    display_name: str | None = None


class MessageContentSchema(BaseModel):
    """Message content structure"""

    content: str = Field(..., min_length=1, max_length=10000)
    content_type: str = Field(default="text/plain")
    subject: str | None = Field(None, max_length=255)


# Request schemas
class SendMessageRequest(BaseModel):
    """Request to send a message through unified inbox"""

    channel: MessageChannel
    direction: MessageDirection = MessageDirection.OUTBOUND

    # Recipient
    phone_number: str | None = Field(None, pattern=r"^\+?1?[0-9]{10,15}$")
    email_address: str | None = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    social_handle: str | None = None
    contact_id: UUID | None = None

    # Content
    content: str = Field(..., min_length=1, max_length=10000)
    content_type: str = Field(default="text/plain")
    subject: str | None = Field(None, max_length=255)

    # Threading
    thread_id: UUID | None = None
    parent_message_id: UUID | None = None

    # Metadata
    metadata: dict[str, Any] | None = None

    @validator("phone_number", "email_address", "social_handle")
    def validate_recipient(self, v, values):
        """Ensure at least one recipient identifier is provided"""
        identifiers = [
            values.get("phone_number"),
            values.get("email_address"),
            values.get("social_handle"),
            values.get("contact_id"),
        ]
        if not any(identifiers):
            raise ValueError("At least one recipient identifier must be provided")
        return v


class MessageFilterRequest(BaseModel):
    """Request to filter messages"""

    channel: MessageChannel | None = None
    direction: MessageDirection | None = None
    status: MessageStatus | None = None
    contact_id: UUID | None = None
    thread_id: UUID | None = None
    phone_number: str | None = None
    email_address: str | None = None

    # Date filtering
    created_after: datetime | None = None
    created_before: datetime | None = None

    # Pagination
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)


class ThreadCreateRequest(BaseModel):
    """Request to create a new thread"""

    channel: MessageChannel
    subject: str | None = Field(None, max_length=255)
    contact_id: UUID | None = None
    booking_id: UUID | None = None
    metadata: dict[str, Any] | None = None


class TCPAUpdateRequest(BaseModel):
    """Request to update TCPA status"""

    phone_number: str = Field(..., pattern=r"^\+?1?[0-9]{10,15}$")
    channel: MessageChannel
    status: TCPAStatus
    opt_in_method: str | None = Field(None, max_length=100)
    opt_in_source: str | None = Field(None, max_length=255)


# Response schemas
class MessageResponse(BaseModel):
    """Message response schema"""

    id: UUID
    channel: MessageChannel
    direction: MessageDirection
    status: MessageStatus

    # Contact info
    contact_id: UUID | None = None
    phone_number: str | None = None
    email_address: str | None = None
    social_handle: str | None = None

    # Content
    subject: str | None = None
    content: str
    content_type: str

    # Threading
    thread_id: UUID | None = None
    parent_message_id: UUID | None = None

    # Metadata
    external_id: str | None = None
    metadata: dict[str, Any] | None = None

    # Timestamps
    created_at: datetime
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    read_at: datetime | None = None

    class Config:
        from_attributes = True


class ThreadResponse(BaseModel):
    """Thread response schema"""

    id: UUID
    subject: str | None = None
    channel: MessageChannel

    # Associations
    contact_id: UUID | None = None
    booking_id: UUID | None = None

    # Status
    is_active: bool
    is_archived: bool
    tcpa_status: TCPAStatus
    tcpa_updated_at: datetime | None = None

    # Stats
    message_count: int = 0
    unread_count: int = 0

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None = None

    # Latest message preview
    latest_message: MessageResponse | None = None

    class Config:
        from_attributes = True


class ThreadWithMessagesResponse(ThreadResponse):
    """Thread with full message history"""

    messages: list[MessageResponse] = []


class TCPAStatusResponse(BaseModel):
    """TCPA status response"""

    id: UUID
    contact_id: UUID | None = None
    phone_number: str
    status: TCPAStatus
    channel: MessageChannel

    # Audit info
    opt_in_method: str | None = None
    opt_in_source: str | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageStatsResponse(BaseModel):
    """Message statistics response"""

    total_messages: int
    total_threads: int

    # By channel
    channel_stats: dict[str, int]

    # By status
    status_stats: dict[str, int]

    # By direction
    direction_stats: dict[str, int]

    # Recent activity
    messages_last_24h: int
    threads_last_24h: int


class WebSocketConnectionResponse(BaseModel):
    """WebSocket connection response"""

    id: UUID
    connection_id: str
    user_id: UUID | None = None
    is_active: bool
    connected_at: datetime
    last_ping_at: datetime | None = None

    class Config:
        from_attributes = True


# WebSocket message schemas
class WebSocketMessage(BaseModel):
    """WebSocket message structure"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "message",
                "data": {"content": "Hello"},
                "timestamp": "2024-10-25T10:30:00Z",
            }
        }
    )

    type: str  # message, status, notification, etc.
    data: dict[str, Any]
    timestamp: datetime = Field(description="Message timestamp")

    @classmethod
    def create(cls, type: str, data: dict[str, Any]) -> "WebSocketMessage":
        """Factory method to create WebSocketMessage with automatic timestamp."""
        return cls(type=type, data=data, timestamp=datetime.now())


class WebSocketMessageNotification(BaseModel):
    """WebSocket notification for new messages"""

    type: str = "new_message"
    message: MessageResponse
    thread: ThreadResponse


class WebSocketStatusUpdate(BaseModel):
    """WebSocket status update notification"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "status_update",
                "message_id": "550e8400-e29b-41d4-a716-446655440000",
                "old_status": "sent",
                "new_status": "delivered",
                "timestamp": "2024-10-25T10:30:00Z",
            }
        }
    )

    type: str = "status_update"
    message_id: UUID
    old_status: MessageStatus
    new_status: MessageStatus
    timestamp: datetime = Field(description="Update timestamp")

    @classmethod
    def create(
        cls, message_id: UUID, old_status: MessageStatus, new_status: MessageStatus
    ) -> "WebSocketStatusUpdate":
        """Factory method to create WebSocketStatusUpdate with automatic timestamp."""
        return cls(
            message_id=message_id,
            old_status=old_status,
            new_status=new_status,
            timestamp=datetime.now(),
        )


# Bulk operation schemas
class BulkMessageRequest(BaseModel):
    """Bulk message sending request"""

    messages: list[SendMessageRequest] = Field(..., min_items=1, max_items=100)
    batch_metadata: dict[str, Any] | None = None


class BulkMessageResponse(BaseModel):
    """Bulk message response"""

    batch_id: UUID
    total_messages: int
    successful: int
    failed: int
    results: list[dict[str, Any]]  # Individual results


# Auto-response schemas
class AutoResponseRule(BaseModel):
    """Auto-response rule configuration"""

    id: UUID
    name: str
    channel: MessageChannel

    # Trigger conditions
    keywords: list[str] = []
    exact_match: bool = False
    case_sensitive: bool = False

    # Response
    response_template: str
    response_delay_seconds: int = 0

    # Status
    is_active: bool = True

    # Timestamps
    created_at: datetime
    updated_at: datetime
