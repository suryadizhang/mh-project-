"""Social media CQRS queries."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from cqrs.base import Query  # Phase 2C: Updated from api.app.cqrs.base
from models.enums import MessageKind, ReviewStatus, SocialPlatform, ThreadStatus
from pydantic import ConfigDict, Field


class GetSocialInboxQuery(Query):
    """Query to get social media inbox messages."""

    platforms: list[SocialPlatform] | None = None
    statuses: list[ThreadStatus] | None = None
    assigned_to: UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    search: str | None = Field(None, max_length=100)
    has_unread: bool | None = None
    priority_min: int | None = Field(None, ge=1, le=5)
    tags: list[str] | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)
    sort_by: str = Field("updated_at", description="Field to sort by")
    sort_order: Literal["asc", "desc"] = "desc"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "platforms": ["instagram", "facebook"],
                "statuses": ["new", "pending"],
                "assigned_to": "770e8400-e29b-41d4-a716-446655440000",
                "date_from": "2025-09-20T00:00:00Z",
                "search": "hibachi party",
                "has_unread": True,
                "tags": ["lead_potential"],
                "page": 1,
                "page_size": 25,
                "sort_by": "updated_at",
                "sort_order": "desc",
            }
        }
    )


class GetReviewsBoardQuery(Query):
    """Query to get reviews dashboard."""

    platforms: list[SocialPlatform] | None = None
    statuses: list[ReviewStatus] | None = None
    rating_min: int | None = Field(None, ge=1, le=5)
    rating_max: int | None = Field(None, ge=1, le=5)
    date_from: datetime | None = None
    date_to: datetime | None = None
    search: str | None = Field(None, max_length=100)
    priority_min: int | None = Field(None, ge=1, le=5)
    assigned_to: UUID | None = None
    escalated_only: bool = False
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: Literal["asc", "desc"] = "desc"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "platforms": ["google", "yelp"],
                "statuses": ["new", "acknowledged"],
                "rating_min": 1,
                "rating_max": 3,
                "date_from": "2025-09-01T00:00:00Z",
                "search": "bad service",
                "priority_min": 2,
                "escalated_only": False,
                "page": 1,
                "page_size": 25,
            }
        }
    )


class GetThreadDetailQuery(Query):
    """Query to get detailed social media thread."""

    thread_id: UUID
    include_messages: bool = True
    include_customer_profile: bool = True
    include_related_threads: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "thread_id": "550e8400-e29b-41d4-a716-446655440000",
                "include_messages": True,
                "include_customer_profile": True,
                "include_related_threads": True,
            }
        }
    )


class GetSocialAnalyticsQuery(Query):
    """Query to get social media analytics."""

    platforms: list[SocialPlatform] | None = None
    date_from: datetime
    date_to: datetime
    granularity: Literal["hour", "day", "week", "month"] = "day"
    metrics: list[str] | None = Field(
        default=None,
        description="Specific metrics to include: messages, threads, leads, reviews, response_time",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "platforms": ["instagram", "facebook"],
                "date_from": "2025-09-01T00:00:00Z",
                "date_to": "2025-09-23T23:59:59Z",
                "granularity": "day",
                "metrics": ["messages", "threads", "leads", "response_time"],
            }
        }
    )


class GetSocialAccountsQuery(Query):
    """Query to get connected social media accounts."""

    platforms: list[SocialPlatform] | None = None
    is_active: bool | None = None
    include_stats: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "platforms": ["instagram", "google"],
                "is_active": True,
                "include_stats": True,
            }
        }
    )


class GetCustomerSocialProfileQuery(Query):
    """Query to get customer's social media profile."""

    customer_id: UUID | None = None
    social_handle: str | None = None
    platform: SocialPlatform | None = None
    include_threads: bool = True
    include_reviews: bool = True
    threads_limit: int = Field(10, ge=1, le=50)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer_id": "660e8400-e29b-41d4-a716-446655440000",
                "social_handle": "@viviana.sac",
                "platform": "instagram",
                "include_threads": True,
                "include_reviews": True,
                "threads_limit": 20,
            }
        }
    )


class SearchSocialContentQuery(Query):
    """Query to search across social media content."""

    search_term: str = Field(..., min_length=2, max_length=100)
    platforms: list[SocialPlatform] | None = None
    content_types: list[Literal["message", "comment", "review", "mention"]] | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    customer_id: UUID | None = None
    thread_id: UUID | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "search_term": "party of 12",
                "platforms": ["instagram", "facebook"],
                "content_types": ["message", "comment"],
                "date_from": "2025-09-01T00:00:00Z",
                "page": 1,
                "page_size": 25,
            }
        }
    )


class GetUnreadCountsQuery(Query):
    """Query to get unread message counts by platform."""

    platforms: list[SocialPlatform] | None = None
    assigned_to: UUID | None = None
    group_by: Literal["platform", "status", "priority"] = "platform"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "platforms": ["instagram", "facebook", "google"],
                "assigned_to": "770e8400-e29b-41d4-a716-446655440000",
                "group_by": "platform",
            }
        }
    )


class GetSocialLeadsQuery(Query):
    """Query to get social media leads."""

    platforms: list[SocialPlatform] | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    consent_dm: bool | None = None
    consent_sms: bool | None = None
    consent_email: bool | None = None
    interest_category: str | None = None
    converted_only: bool = False
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: Literal["asc", "desc"] = "desc"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "platforms": ["instagram"],
                "date_from": "2025-09-01T00:00:00Z",
                "consent_dm": True,
                "interest_category": "private_hibachi",
                "converted_only": False,
                "page": 1,
                "page_size": 25,
            }
        }
    )


class GetRecentActivityQuery(Query):
    """Query to get recent social media activity."""

    platforms: list[SocialPlatform] | None = None
    activity_types: list[Literal["message", "comment", "review", "mention", "reply"]] | None = None
    hours_back: int = Field(24, ge=1, le=168, description="Hours to look back")
    limit: int = Field(50, ge=1, le=200)
    include_internal: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "platforms": ["instagram", "facebook"],
                "activity_types": ["message", "comment", "review"],
                "hours_back": 48,
                "limit": 100,
                "include_internal": False,
            }
        }
    )


class GetThreadMessagesQuery(Query):
    """Query to get messages in a social thread."""

    thread_id: UUID
    message_types: list[MessageKind] | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_order: Literal["asc", "desc"] = "asc"
    include_sender_profile: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "thread_id": "550e8400-e29b-41d4-a716-446655440000",
                "message_types": ["dm", "comment"],
                "page": 1,
                "page_size": 50,
                "sort_order": "asc",
                "include_sender_profile": True,
            }
        }
    )


class GetSocialMetricsQuery(Query):
    """Query to get social media metrics and KPIs."""

    date_from: datetime
    date_to: datetime
    platforms: list[SocialPlatform] | None = None
    metric_types: (
        list[
            Literal[
                "response_time",
                "resolution_time",
                "customer_satisfaction",
                "lead_conversion",
                "review_sentiment",
                "engagement_rate",
            ]
        ]
        | None
    ) = None
    granularity: Literal["day", "week", "month"] = "day"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date_from": "2025-09-01T00:00:00Z",
                "date_to": "2025-09-23T23:59:59Z",
                "platforms": ["instagram", "facebook"],
                "metric_types": ["response_time", "lead_conversion", "review_sentiment"],
                "granularity": "week",
            }
        }
    )
