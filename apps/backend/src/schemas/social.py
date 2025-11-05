"""Social media integration Pydantic schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from models.legacy_social import (  # Phase 2C: Updated from api.app.models.social
    MessageDirection,
    MessageKind,
    ReviewStatus,
    SocialPlatform,
    ThreadStatus,
)
from pydantic import BaseModel, ConfigDict, Field


class SocialWebhookPayload(BaseModel):
    """Base webhook payload schema."""

    object: str
    entry: list[dict[str, Any]]


class InstagramWebhookEntry(BaseModel):
    """Instagram webhook entry schema."""

    id: str
    time: int
    changes: list[dict[str, Any]] | None = None
    messaging: list[dict[str, Any]] | None = None


class FacebookWebhookEntry(BaseModel):
    """Facebook webhook entry schema."""

    id: str
    time: int
    changes: list[dict[str, Any]] | None = None
    messaging: list[dict[str, Any]] | None = None


class SocialAccountBase(BaseModel):
    """Base social account schema."""

    platform: SocialPlatform
    page_id: str = Field(..., description="Platform-specific page/business ID")
    page_name: str = Field(..., description="Display name of the business page")
    handle: str | None = Field(None, description="@username or handle if applicable")
    profile_url: str | None = None
    avatar_url: str | None = None


class SocialAccountCreate(SocialAccountBase):
    """Schema for creating a social account."""

    token_ref: str | None = Field(None, description="Encrypted reference to access tokens")
    metadata: dict[str, Any] | None = None


class SocialAccountUpdate(BaseModel):
    """Schema for updating a social account."""

    page_name: str | None = None
    handle: str | None = None
    profile_url: str | None = None
    avatar_url: str | None = None
    token_ref: str | None = None
    webhook_verified: bool | None = None
    last_sync_at: datetime | None = None
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None


class SocialAccount(SocialAccountBase):
    """Complete social account schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    connected_by: UUID
    connected_at: datetime
    webhook_verified: bool = False
    last_sync_at: datetime | None = None
    is_active: bool = True
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class SocialIdentityBase(BaseModel):
    """Base social identity schema."""

    platform: SocialPlatform
    handle: str = Field(..., description="Social handle without @ prefix")
    display_name: str | None = None
    profile_url: str | None = None
    avatar_url: str | None = None


class SocialIdentityCreate(SocialIdentityBase):
    """Schema for creating a social identity."""

    customer_id: UUID | None = None
    confidence_score: float = 1.0
    verification_status: str = "unverified"
    metadata: dict[str, Any] | None = None


class SocialIdentity(SocialIdentityBase):
    """Complete social identity schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID | None = None
    confidence_score: float = 1.0
    verification_status: str = "unverified"
    first_seen_at: datetime
    last_active_at: datetime | None = None
    metadata: dict[str, Any] | None = None
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

    customer_id: UUID | None = None
    lead_id: UUID | None = None
    social_identity_id: UUID | None = None
    subject: str | None = None
    context_url: str | None = None
    assigned_to: UUID | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class SocialThreadUpdate(BaseModel):
    """Schema for updating a social thread."""

    customer_id: UUID | None = None
    lead_id: UUID | None = None
    social_identity_id: UUID | None = None
    status: ThreadStatus | None = None
    priority: int | None = Field(None, ge=1, le=5)
    subject: str | None = None
    context_url: str | None = None
    assigned_to: UUID | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class SocialThread(SocialThreadBase):
    """Complete social thread schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID | None = None
    lead_id: UUID | None = None
    social_identity_id: UUID | None = None
    subject: str | None = None
    context_url: str | None = None
    message_count: int = 0
    unread_count: int = 0
    last_message_at: datetime | None = None
    last_response_at: datetime | None = None
    assigned_to: UUID | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None


class SocialMessageBase(BaseModel):
    """Base social message schema."""

    thread_id: UUID
    direction: MessageDirection
    kind: MessageKind
    body: str | None = None


class SocialMessageCreate(SocialMessageBase):
    """Schema for creating a social message."""

    message_ref: str | None = None
    author_handle: str | None = None
    author_name: str | None = None
    media: dict[str, Any] | None = None
    sentiment_score: float | None = Field(None, ge=-1, le=1)
    intent_tags: list[str] | None = None
    is_public: bool = False
    requires_approval: bool = False
    approved_by: UUID | None = None
    ai_generated: bool = False
    parent_message_id: UUID | None = None
    metadata: dict[str, Any] | None = None


class SocialMessage(SocialMessageBase):
    """Complete social message schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    message_ref: str | None = None
    author_handle: str | None = None
    author_name: str | None = None
    media: dict[str, Any] | None = None
    sentiment_score: float | None = None
    intent_tags: list[str] | None = None
    is_public: bool = False
    requires_approval: bool = False
    approved_by: UUID | None = None
    ai_generated: bool = False
    parent_message_id: UUID | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime
    sent_at: datetime | None = None
    failed_at: datetime | None = None
    error_details: str | None = None


class ReviewBase(BaseModel):
    """Base review schema."""

    platform: SocialPlatform
    account_id: UUID
    review_ref: str = Field(..., description="Platform-specific review ID")


class ReviewCreate(ReviewBase):
    """Schema for creating a review."""

    thread_id: UUID | None = None
    author_handle: str | None = None
    author_name: str | None = None
    rating: int | None = Field(None, ge=1, le=5)
    title: str | None = None
    body: str | None = None
    review_url: str | None = None
    status: ReviewStatus = ReviewStatus.NEW
    sentiment_score: float | None = Field(None, ge=-1, le=1)
    keywords: list[str] | None = None
    customer_id: UUID | None = None
    booking_ref: str | None = None
    assigned_to: UUID | None = None
    escalation_reason: str | None = None
    response_due_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class ReviewUpdate(BaseModel):
    """Schema for updating a review."""

    status: ReviewStatus | None = None
    assigned_to: UUID | None = None
    escalation_reason: str | None = None
    response_due_at: datetime | None = None
    responded_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class Review(ReviewBase):
    """Complete review schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    thread_id: UUID | None = None
    author_handle: str | None = None
    author_name: str | None = None
    rating: int | None = None
    title: str | None = None
    body: str | None = None
    review_url: str | None = None
    status: ReviewStatus = ReviewStatus.NEW
    sentiment_score: float | None = None
    keywords: list[str] | None = None
    customer_id: UUID | None = None
    booking_ref: str | None = None
    assigned_to: UUID | None = None
    escalation_reason: str | None = None
    response_due_at: datetime | None = None
    responded_at: datetime | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


# Command Schemas for CQRS


class CreateLeadFromSocialCommand(BaseModel):
    """Command to create a lead from social interaction."""

    source: SocialPlatform
    thread_id: str | None = None
    handle: str
    post_url: str | None = None
    message_excerpt: str | None = None
    inferred_interest: str | None = None
    consent_dm: bool = False
    metadata: dict[str, Any] | None = None


class SendSocialReplyCommand(BaseModel):
    """Command to send a social media reply."""

    thread_id: UUID
    reply_kind: MessageKind
    body: str
    safety: dict[str, Any] = Field(default_factory=dict, description="Safety and approval metadata")
    metadata: dict[str, Any] | None = None


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
    notes: str | None = None


class EscalateReviewCommand(BaseModel):
    """Command to escalate a review."""

    review_id: UUID
    escalated_by: UUID
    escalation_reason: str
    assigned_to: UUID | None = None
    urgency_level: int = Field(3, ge=1, le=5)


class CloseReviewCommand(BaseModel):
    """Command to close a review."""

    review_id: UUID
    closed_by: UUID
    resolution_notes: str | None = None


# Query Schemas


class SocialInboxQuery(BaseModel):
    """Query parameters for social inbox."""

    platforms: list[SocialPlatform] | None = None
    status: list[ThreadStatus] | None = None
    assigned_to: UUID | None = None
    priority: int | None = None
    tags: list[str] | None = None
    customer_id: UUID | None = None
    lead_id: UUID | None = None
    page: int = 1
    limit: int = 20
    sort_by: str = "last_message_at"
    sort_order: str = "desc"


class ReviewsBoardQuery(BaseModel):
    """Query parameters for reviews board."""

    platforms: list[SocialPlatform] | None = None
    status: list[ReviewStatus] | None = None
    rating_min: int | None = Field(None, ge=1, le=5)
    rating_max: int | None = Field(None, ge=1, le=5)
    assigned_to: UUID | None = None
    keywords: list[str] | None = None
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
    messages: list[SocialMessage] | None = None
    social_identity: SocialIdentity | None = None
    customer: dict[str, Any] | None = None
    lead: dict[str, Any] | None = None
