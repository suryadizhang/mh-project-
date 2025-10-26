"""Social media CQRS commands."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import Field, ConfigDict

from api.app.cqrs.base import Command
from api.app.models.social import MessageKind, SocialPlatform, ThreadStatus


class CreateLeadFromSocialCommand(Command):
    """Command to create a lead from social media interaction."""

    source: SocialPlatform
    thread_id: Optional[UUID] = None
    handle: str = Field(..., description="Social media handle of the lead")
    post_url: Optional[str] = None
    message_excerpt: Optional[str] = None
    inferred_interest: Optional[str] = None
    consent_dm: bool = False
    consent_sms: bool = False
    consent_email: bool = False
    metadata: Optional[dict[str, Any]] = None

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "source": "instagram",
                "thread_id": "550e8400-e29b-41d4-a716-446655440000",
                "handle": "@viviana.sac",
                "post_url": "https://instagram.com/p/abc123",
                "message_excerpt": "Price for 12 people in 95823?",
                "inferred_interest": "private_hibachi",
                "consent_dm": True,
                "metadata": {"utm": {"source": "instagram", "medium": "comment"}}
            }
        })


class SendSocialReplyCommand(Command):
    """Command to send a social media reply."""

    thread_id: UUID
    reply_kind: MessageKind
    body: str = Field(..., min_length=1, max_length=2000)
    safety: dict[str, Any] = Field(
        default={},
        description="Safety and approval metadata"
    )
    schedule_send_at: Optional[datetime] = None
    requires_approval: bool = True
    metadata: Optional[dict[str, Any]] = None

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "thread_id": "550e8400-e29b-41d4-a716-446655440000",
                "reply_kind": "dm",
                "body": "We'd love to host your party of 12! Deposit is $200. Want me to DM a booking link?",
                "safety": {
                    "approved_by_human": True,
                    "policy_score": 0.02,
                    "profanity_check": "clean"
                }
            }
        })


class LinkSocialIdentityToCustomerCommand(Command):
    """Command to link a social identity to a customer."""

    social_identity_id: UUID
    customer_id: UUID
    confidence_score: float = Field(1.0, ge=0.0, le=1.0)
    verification_method: str = Field("manual", description="How the link was verified")
    notes: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "social_identity_id": "550e8400-e29b-41d4-a716-446655440000",
                "customer_id": "660e8400-e29b-41d4-a716-446655440000",
                "confidence_score": 0.95,
                "verification_method": "phone_number_match",
                "notes": "Phone number matched in customer profile"
            }
        })


class AcknowledgeReviewCommand(Command):
    """Command to acknowledge a review."""

    review_id: UUID
    acknowledged_by: UUID
    notes: Optional[str] = None
    priority_level: int = Field(3, ge=1, le=5, description="1=urgent, 5=low")
    assigned_to: Optional[UUID] = None

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "review_id": "550e8400-e29b-41d4-a716-446655440000",
                "acknowledged_by": "770e8400-e29b-41d4-a716-446655440000",
                "notes": "Customer mentioned poor service on 2/15",
                "priority_level": 2,
                "assigned_to": "880e8400-e29b-41d4-a716-446655440000"
            }
        })


class EscalateReviewCommand(Command):
    """Command to escalate a review."""

    review_id: UUID
    escalated_by: UUID
    escalation_reason: str = Field(..., min_length=10, max_length=500)
    assigned_to: Optional[UUID] = None
    urgency_level: int = Field(3, ge=1, le=5, description="1=critical, 5=low")
    escalation_type: str = Field("general", description="Type of escalation")
    deadline: Optional[datetime] = None

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "review_id": "550e8400-e29b-41d4-a716-446655440000",
                "escalated_by": "770e8400-e29b-41d4-a716-446655440000",
                "escalation_reason": "Customer mentioned food poisoning - requires immediate management attention",
                "assigned_to": "990e8400-e29b-41d4-a716-446655440000",
                "urgency_level": 1,
                "escalation_type": "health_safety",
                "deadline": "2025-09-24T12:00:00Z"
            }
        })


class CloseReviewCommand(Command):
    """Command to close a review."""

    review_id: UUID
    closed_by: UUID
    resolution_notes: Optional[str] = None
    customer_satisfied: Optional[bool] = None
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "review_id": "550e8400-e29b-41d4-a716-446655440000",
                "closed_by": "770e8400-e29b-41d4-a716-446655440000",
                "resolution_notes": "Customer received full refund and apology. Issue resolved.",
                "customer_satisfied": True,
                "follow_up_required": False
            }
        })


class UpdateThreadStatusCommand(Command):
    """Command to update social thread status."""

    thread_id: UUID
    status: ThreadStatus
    updated_by: UUID
    reason: Optional[str] = None
    assigned_to: Optional[UUID] = None
    tags: Optional[list[str]] = None

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "thread_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "resolved",
                "updated_by": "770e8400-e29b-41d4-a716-446655440000",
                "reason": "Customer booking completed successfully",
                "tags": ["booking_completed", "positive_outcome"]
            }
        })


class CreateSocialAccountCommand(Command):
    """Command to create/connect a social media account."""

    platform: SocialPlatform
    page_id: str = Field(..., description="Platform-specific page/business ID")
    page_name: str = Field(..., description="Display name of the business page")
    handle: Optional[str] = None
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    connected_by: UUID
    token_ref: Optional[str] = Field(None, description="Encrypted reference to access tokens")
    metadata: Optional[dict[str, Any]] = None

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "platform": "instagram",
                "page_id": "17841400047205",
                "page_name": "My Hibachi Chef",
                "handle": "myhibachichef",
                "profile_url": "https://instagram.com/myhibachichef",
                "connected_by": "770e8400-e29b-41d4-a716-446655440000",
                "metadata": {
                    "capabilities": ["messaging", "comments", "mentions"],
                    "webhook_verified": True
                }
            }
        })


class ScheduleSocialFollowUpCommand(Command):
    """Command to schedule a social media follow-up."""

    thread_id: UUID
    follow_up_type: str = Field(..., description="Type of follow-up: dm, comment_reply, review_response")
    scheduled_for: datetime
    message_template: str
    conditions: Optional[dict[str, Any]] = Field(
        None,
        description="Conditions for sending (e.g., no customer response by X time)"
    )
    created_by: UUID

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "thread_id": "550e8400-e29b-41d4-a716-446655440000",
                "follow_up_type": "dm",
                "scheduled_for": "2025-09-25T10:00:00Z",
                "message_template": "Hi! Just following up on your hibachi inquiry. Are you still interested in booking for this weekend?",
                "conditions": {
                    "if_no_response_by": "2025-09-24T18:00:00Z",
                    "respect_quiet_hours": True
                },
                "created_by": "770e8400-e29b-41d4-a716-446655440000"
            }
        })


class BulkUpdateThreadsCommand(Command):
    """Command to bulk update multiple social threads."""

    thread_ids: list[UUID] = Field(..., min_items=1, max_items=100)
    updates: dict[str, Any] = Field(..., description="Fields to update")
    updated_by: UUID
    reason: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "thread_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "660e8400-e29b-41d4-a716-446655440000"
                ],
                "updates": {
                    "status": "resolved",
                    "tags": ["bulk_resolved", "campaign_complete"]
                },
                "updated_by": "770e8400-e29b-41d4-a716-446655440000",
                "reason": "Campaign promotion ended - closing all related threads"
            }
        })
