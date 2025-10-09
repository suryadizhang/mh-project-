"""Social media integration Pydantic schemas."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from api.app.models.social import (
    MessageDirection,
    MessageKind,
    ReviewStatus,
    SocialPlatform,
    ThreadStatus,
)


class SocialWebhookPayload(BaseModel):
    """Base webhook payload schema."""
    object: str
    entry: list[dict[str, Any]]


class InstagramWebhookEntry(BaseModel):
    """Instagram webhook entry schema."""
    id: str
    time: int
    changes: Optional[list[dict[str, Any]]] = None
    messaging: Optional[list[dict[str, Any]]] = None


class FacebookWebhookEntry(BaseModel):
    """Facebook webhook entry schema."""
    id: str
    time: int
    changes: Optional[list[dict[str, Any]]] = None
    messaging: Optional[list[dict[str, Any]]] = None


class SocialAccountBase(BaseModel):
    """Base social account schema."""
    platform: SocialPlatform
    page_id: str = Field(..., description="Platform-specific page/business ID")
    page_name: str = Field(..., description="Display name of the business page")
    handle: Optional[str] = Field(None, description="@username or handle if applicable")
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None


class SocialAccountCreate(SocialAccountBase):
    """Schema for creating a social account."""
    token_ref: Optional[str] = Field(None, description="Encrypted reference to access tokens")
    metadata: Optional[dict[str, Any]] = None


class SocialAccountUpdate(BaseModel):
    """Schema for updating a social account."""
    page_name: Optional[str] = None
    handle: Optional[str] = None
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    token_ref: Optional[str] = None
    webhook_verified: Optional[bool] = None
    last_sync_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None


class SocialAccount(SocialAccountBase):
    """Complete social account schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    connected_by: UUID
    connected_at: datetime
    webhook_verified: bool = False
    last_sync_at: Optional[datetime] = None
    is_active: bool = True
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class SocialIdentityBase(BaseModel):
    """Base social identity schema."""
    platform: SocialPlatform
    handle: str = Field(..., description="Social handle without @ prefix")
    display_name: Optional[str] = None
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None


class SocialIdentityCreate(SocialIdentityBase):
    """Schema for creating a social identity."""
    customer_id: Optional[UUID] = None
    confidence_score: float = 1.0
    verification_status: str = "unverified"
    metadata: Optional[dict[str, Any]] = None


class SocialIdentity(SocialIdentityBase):
    """Complete social identity schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: Optional[UUID] = None
    confidence_score: float = 1.0
    verification_status: str = "unverified"
    first_seen_at: datetime
    last_active_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class SocialThreadBase(BaseModel):
    """Base social thread schema."""
    platform: SocialPlatform
    thread_ref: str = Field(..., description="Platform-specific thread/conversation ID")
    account_id: UUID
    status: ThreadStatus = ThreadStatus.OPEN
    priority: int = Field(3, ge=1, le=5, description="1=urgent, 5=low")


class SocialThreadCreate(SocialThreadBase):
    """Schema for creating a social thread."""
    customer_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    social_identity_id: Optional[UUID] = None
    subject: Optional[str] = None
    context_url: Optional[str] = None
    assigned_to: Optional[UUID] = None
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class SocialThreadUpdate(BaseModel):
    """Schema for updating a social thread."""
    customer_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    social_identity_id: Optional[UUID] = None
    status: Optional[ThreadStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    subject: Optional[str] = None
    context_url: Optional[str] = None
    assigned_to: Optional[UUID] = None
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class SocialThread(SocialThreadBase):
    """Complete social thread schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    social_identity_id: Optional[UUID] = None
    subject: Optional[str] = None
    context_url: Optional[str] = None
    message_count: int = 0
    unread_count: int = 0
    last_message_at: Optional[datetime] = None
    last_response_at: Optional[datetime] = None
    assigned_to: Optional[UUID] = None
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None


class SocialMessageBase(BaseModel):
    """Base social message schema."""
    thread_id: UUID
    direction: MessageDirection
    kind: MessageKind
    body: Optional[str] = None


class SocialMessageCreate(SocialMessageBase):
    """Schema for creating a social message."""
    message_ref: Optional[str] = None
    author_handle: Optional[str] = None
    author_name: Optional[str] = None
    media: Optional[dict[str, Any]] = None
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    intent_tags: Optional[list[str]] = None
    is_public: bool = False
    requires_approval: bool = False
    approved_by: Optional[UUID] = None
    ai_generated: bool = False
    parent_message_id: Optional[UUID] = None
    metadata: Optional[dict[str, Any]] = None


class SocialMessage(SocialMessageBase):
    """Complete social message schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    message_ref: Optional[str] = None
    author_handle: Optional[str] = None
    author_name: Optional[str] = None
    media: Optional[dict[str, Any]] = None
    sentiment_score: Optional[float] = None
    intent_tags: Optional[list[str]] = None
    is_public: bool = False
    requires_approval: bool = False
    approved_by: Optional[UUID] = None
    ai_generated: bool = False
    parent_message_id: Optional[UUID] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_details: Optional[str] = None


class ReviewBase(BaseModel):
    """Base review schema."""
    platform: SocialPlatform
    account_id: UUID
    review_ref: str = Field(..., description="Platform-specific review ID")


class ReviewCreate(ReviewBase):
    """Schema for creating a review."""
    thread_id: Optional[UUID] = None
    author_handle: Optional[str] = None
    author_name: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = None
    body: Optional[str] = None
    review_url: Optional[str] = None
    status: ReviewStatus = ReviewStatus.NEW
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    keywords: Optional[list[str]] = None
    customer_id: Optional[UUID] = None
    booking_ref: Optional[str] = None
    assigned_to: Optional[UUID] = None
    escalation_reason: Optional[str] = None
    response_due_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class ReviewUpdate(BaseModel):
    """Schema for updating a review."""
    status: Optional[ReviewStatus] = None
    assigned_to: Optional[UUID] = None
    escalation_reason: Optional[str] = None
    response_due_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class Review(ReviewBase):
    """Complete review schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    thread_id: Optional[UUID] = None
    author_handle: Optional[str] = None
    author_name: Optional[str] = None
    rating: Optional[int] = None
    title: Optional[str] = None
    body: Optional[str] = None
    review_url: Optional[str] = None
    status: ReviewStatus = ReviewStatus.NEW
    sentiment_score: Optional[float] = None
    keywords: Optional[list[str]] = None
    customer_id: Optional[UUID] = None
    booking_ref: Optional[str] = None
    assigned_to: Optional[UUID] = None
    escalation_reason: Optional[str] = None
    response_due_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


# Command Schemas for CQRS

class CreateLeadFromSocialCommand(BaseModel):
    """Command to create a lead from social interaction."""
    source: SocialPlatform
    thread_id: Optional[str] = None
    handle: str
    post_url: Optional[str] = None
    message_excerpt: Optional[str] = None
    inferred_interest: Optional[str] = None
    consent_dm: bool = False
    metadata: Optional[dict[str, Any]] = None


class SendSocialReplyCommand(BaseModel):
    """Command to send a social media reply."""
    thread_id: UUID
    reply_kind: MessageKind
    body: str
    safety: dict[str, Any] = Field(default_factory=dict, description="Safety and approval metadata")
    metadata: Optional[dict[str, Any]] = None


class LinkSocialIdentityToCustomerCommand(BaseModel):
    """Command to link a social identity to a customer."""
    social_identity_id: UUID
    customer_id: UUID
    confidence_score: float = 1.0
    verification_method: str = "manual"


class AcknowledgeReviewCommand(BaseModel):
    """Command to acknowledge a review."""
    review_id: UUID
    acknowledged_by: UUID
    notes: Optional[str] = None


class EscalateReviewCommand(BaseModel):
    """Command to escalate a review."""
    review_id: UUID
    escalated_by: UUID
    escalation_reason: str
    assigned_to: Optional[UUID] = None
    urgency_level: int = Field(3, ge=1, le=5)


class CloseReviewCommand(BaseModel):
    """Command to close a review."""
    review_id: UUID
    closed_by: UUID
    resolution_notes: Optional[str] = None


# Query Schemas

class SocialInboxQuery(BaseModel):
    """Query parameters for social inbox."""
    platforms: Optional[list[SocialPlatform]] = None
    status: Optional[list[ThreadStatus]] = None
    assigned_to: Optional[UUID] = None
    priority: Optional[int] = None
    tags: Optional[list[str]] = None
    customer_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    page: int = 1
    limit: int = 20
    sort_by: str = "last_message_at"
    sort_order: str = "desc"


class ReviewsBoardQuery(BaseModel):
    """Query parameters for reviews board."""
    platforms: Optional[list[SocialPlatform]] = None
    status: Optional[list[ReviewStatus]] = None
    rating_min: Optional[int] = Field(None, ge=1, le=5)
    rating_max: Optional[int] = Field(None, ge=1, le=5)
    assigned_to: Optional[UUID] = None
    keywords: Optional[list[str]] = None
    overdue_only: bool = False
    page: int = 1
    limit: int = 20
    sort_by: str = "created_at"
    sort_order: str = "asc"


class ThreadDetailQuery(BaseModel):
    """Query for thread details."""
    thread_id: UUID
    include_messages: bool = True
    message_limit: int = 50


# Response Schemas

class SocialInboxResponse(BaseModel):
    """Response for social inbox queries."""
    threads: list[SocialThread]
    total: int
    page: int
    limit: int
    has_next: bool


class ReviewsBoardResponse(BaseModel):
    """Response for reviews board queries."""
    reviews: list[Review]
    total: int
    page: int
    limit: int
    has_next: bool


class ThreadDetailResponse(BaseModel):
    """Response for thread detail queries."""
    thread: SocialThread
    messages: Optional[list[SocialMessage]] = None
    social_identity: Optional[SocialIdentity] = None
    customer: Optional[dict[str, Any]] = None
    lead: Optional[dict[str, Any]] = None
