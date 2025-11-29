"""Social media admin API endpoints."""

from datetime import datetime, timezone
import logging
from typing import Any
from uuid import UUID

from cqrs.base import CommandBus, QueryBus
from cqrs.social.social_commands import (
    AcknowledgeReviewCommand,
    CreateLeadFromSocialCommand,
    EscalateReviewCommand,
    SendSocialReplyCommand,
    UpdateThreadStatusCommand,
)
from cqrs.social.social_queries import (
    GetReviewsBoardQuery,
    GetSocialAnalyticsQuery,
    GetSocialInboxQuery,
    GetSocialLeadsQuery,
    GetThreadDetailQuery,
    GetUnreadCountsQuery,
)
from core.dependencies import (
    get_command_bus,
    get_current_admin_user,
    get_query_bus,
)

# MIGRATED: Enum imports moved from models.enums to NEW db.models system
from db.models.core import ReviewStatus, ThreadStatus
from db.models.crm import SocialPlatform
from schemas.social import (
    AcknowledgeReviewRequest,
    CreateLeadRequest,
    EscalateReviewRequest,
    ReviewsBoardResponse,
    SocialInboxResponse,
    SocialReplyRequest,
    ThreadDetailResponse,
    UpdateThreadStatusRequest,
)
from services.social_ai_generator import (
    SocialAIResponseGenerator,
    SocialResponseContext,
)
from services.social_ai_tools import SocialMediaToolKit
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query as QueryParam
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/social", tags=["Social Media Admin"])


@router.get("/inbox", response_model=SocialInboxResponse)
async def get_social_inbox(
    platforms: list[SocialPlatform] | None = QueryParam(None),
    statuses: list[ThreadStatus] | None = QueryParam(None),
    assigned_to: UUID | None = QueryParam(None),
    search: str | None = QueryParam(None),
    has_unread: bool | None = QueryParam(None),
    date_from: datetime | None = QueryParam(None),
    date_to: datetime | None = QueryParam(None),
    page: int = QueryParam(1, ge=1),
    page_size: int = QueryParam(25, ge=1, le=100),
    sort_by: str = QueryParam("updated_at"),
    sort_order: str = QueryParam("desc"),
    query_bus: QueryBus = Depends(get_query_bus),
    current_user=Depends(get_current_admin_user),
):
    """Get social media inbox messages with filtering."""
    try:
        query = GetSocialInboxQuery(
            platforms=platforms,
            statuses=statuses,
            assigned_to=assigned_to,
            search=search,
            has_unread=has_unread,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        result = await query_bus.execute(query)
        return SocialInboxResponse(**result)

    except Exception as e:
        logger.exception(f"Error getting social inbox: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve social inbox")


@router.get("/reviews", response_model=ReviewsBoardResponse)
async def get_reviews_board(
    platforms: list[SocialPlatform] | None = QueryParam(None),
    statuses: list[ReviewStatus] | None = QueryParam(None),
    rating_min: int | None = QueryParam(None, ge=1, le=5),
    rating_max: int | None = QueryParam(None, ge=1, le=5),
    date_from: datetime | None = QueryParam(None),
    date_to: datetime | None = QueryParam(None),
    search: str | None = QueryParam(None),
    escalated_only: bool = QueryParam(False),
    page: int = QueryParam(1, ge=1),
    page_size: int = QueryParam(25, ge=1, le=100),
    query_bus: QueryBus = Depends(get_query_bus),
    current_user=Depends(get_current_admin_user),
):
    """Get reviews dashboard with filtering."""
    try:
        query = GetReviewsBoardQuery(
            platforms=platforms,
            statuses=statuses,
            rating_min=rating_min,
            rating_max=rating_max,
            date_from=date_from,
            date_to=date_to,
            search=search,
            escalated_only=escalated_only,
            page=page,
            page_size=page_size,
        )

        result = await query_bus.execute(query)
        return ReviewsBoardResponse(**result)

    except Exception as e:
        logger.exception(f"Error getting reviews board: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reviews board")


@router.get("/thread/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread_detail(
    thread_id: UUID,
    include_customer_profile: bool = QueryParam(True),
    include_related_threads: bool = QueryParam(False),
    query_bus: QueryBus = Depends(get_query_bus),
    current_user=Depends(get_current_admin_user),
):
    """Get detailed thread information."""
    try:
        query = GetThreadDetailQuery(
            thread_id=thread_id,
            include_messages=True,
            include_customer_profile=include_customer_profile,
            include_related_threads=include_related_threads,
        )

        result = await query_bus.execute(query)
        return ThreadDetailResponse(**result)

    except Exception as e:
        logger.exception(f"Error getting thread detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve thread details")


@router.post("/thread/{thread_id}/reply")
async def send_social_reply(
    thread_id: UUID,
    request: SocialReplyRequest,
    command_bus: CommandBus = Depends(get_command_bus),
    current_user=Depends(get_current_admin_user),
):
    """Send a reply to a social media thread."""
    try:
        command = SendSocialReplyCommand(
            thread_id=thread_id,
            reply_kind=request.reply_kind,
            body=request.body,
            safety=request.safety or {},
            schedule_send_at=request.schedule_send_at,
            requires_approval=request.requires_approval,
            metadata={
                "sent_by_admin": current_user.id,
                "admin_name": current_user.name,
                "client_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        result = await command_bus.execute(command)

        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": (
                    "Reply sent successfully" if result["sent"] else "Reply queued for approval"
                ),
                "data": result,
            },
        )

    except Exception as e:
        logger.exception(f"Error sending social reply: {e}")
        raise HTTPException(status_code=500, detail="Failed to send social reply")


@router.post("/thread/{thread_id}/ai-response")
async def generate_ai_response(
    thread_id: UUID,
    query_bus: QueryBus = Depends(get_query_bus),
    command_bus: CommandBus = Depends(get_command_bus),
    current_user=Depends(get_current_admin_user),
):
    """Generate AI response for a social media thread."""
    try:
        # Get thread details for context
        thread_query = GetThreadDetailQuery(
            thread_id=thread_id, include_messages=True, include_customer_profile=True
        )

        thread_detail = await query_bus.execute(thread_query)

        # Build context for AI
        context = SocialResponseContext(
            thread_id=thread_id,
            platform=SocialPlatform(thread_detail["platform"]),
            customer_handle=thread_detail.get("customer_profile", {})
            .get("social_identity", {})
            .get("handle", "unknown"),
            customer_name=thread_detail.get("customer_profile", {}).get("name"),
            conversation_history=thread_detail.get("messages", []),
            customer_profile=thread_detail.get("customer_profile"),
            business_context={"admin_requested": True},
            response_tone="professional",
            urgency_level=thread_detail.get("priority", 3),
            requires_approval=True,
        )

        # Generate AI response
        ai_generator = SocialAIResponseGenerator(command_bus, query_bus)
        response_data = await ai_generator.generate_response(context)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "AI response generated successfully",
                "data": response_data,
            },
        )

    except Exception as e:
        logger.exception(f"Error generating AI response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI response")


@router.patch("/thread/{thread_id}/status")
async def update_thread_status(
    thread_id: UUID,
    request: UpdateThreadStatusRequest,
    command_bus: CommandBus = Depends(get_command_bus),
    current_user=Depends(get_current_admin_user),
):
    """Update social media thread status."""
    try:
        command = UpdateThreadStatusCommand(
            thread_id=thread_id,
            status=request.status,
            updated_by=current_user.id,
            reason=request.reason,
            assigned_to=request.assigned_to,
            tags=request.tags,
        )

        result = await command_bus.execute(command)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Thread status updated to {result['new_status']}",
                "data": result,
            },
        )

    except Exception as e:
        logger.exception(f"Error updating thread status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update thread status")


@router.post("/lead")
async def create_lead_from_social(
    request: CreateLeadRequest,
    command_bus: CommandBus = Depends(get_command_bus),
    current_user=Depends(get_current_admin_user),
):
    """Create a lead from social media interaction."""
    try:
        command = CreateLeadFromSocialCommand(
            source=request.source,
            thread_id=request.thread_id,
            handle=request.handle,
            post_url=request.post_url,
            message_excerpt=request.message_excerpt,
            inferred_interest=request.inferred_interest,
            consent_dm=request.consent_dm,
            consent_sms=request.consent_sms,
            consent_email=request.consent_email,
            metadata={"created_by_admin": current_user.id, "admin_name": current_user.name},
        )

        result = await command_bus.execute(command)

        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": (
                    "Lead created successfully" if result["created"] else "Lead already exists"
                ),
                "data": result,
            },
        )

    except Exception as e:
        logger.exception(f"Error creating lead from social: {e}")
        raise HTTPException(status_code=500, detail="Failed to create lead")


@router.patch("/review/{review_id}/acknowledge")
async def acknowledge_review(
    review_id: UUID,
    request: AcknowledgeReviewRequest,
    command_bus: CommandBus = Depends(get_command_bus),
    current_user=Depends(get_current_admin_user),
):
    """Acknowledge a review."""
    try:
        command = AcknowledgeReviewCommand(
            review_id=review_id,
            acknowledged_by=current_user.id,
            notes=request.notes,
            priority_level=request.priority_level,
            assigned_to=request.assigned_to,
        )

        result = await command_bus.execute(command)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Review acknowledged successfully",
                "data": result,
            },
        )

    except Exception as e:
        logger.exception(f"Error acknowledging review: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge review")


@router.patch("/review/{review_id}/escalate")
async def escalate_review(
    review_id: UUID,
    request: EscalateReviewRequest,
    command_bus: CommandBus = Depends(get_command_bus),
    current_user=Depends(get_current_admin_user),
):
    """Escalate a review."""
    try:
        command = EscalateReviewCommand(
            review_id=review_id,
            escalated_by=current_user.id,
            escalation_reason=request.escalation_reason,
            assigned_to=request.assigned_to,
            urgency_level=request.urgency_level,
            escalation_type=request.escalation_type,
            deadline=request.deadline,
        )

        result = await command_bus.execute(command)

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Review escalated successfully", "data": result},
        )

    except Exception as e:
        logger.exception(f"Error escalating review: {e}")
        raise HTTPException(status_code=500, detail="Failed to escalate review")


@router.get("/analytics")
async def get_social_analytics(
    platforms: list[SocialPlatform] | None = QueryParam(None),
    date_from: datetime = QueryParam(...),
    date_to: datetime = QueryParam(...),
    granularity: str = QueryParam("day"),
    metrics: list[str] | None = QueryParam(None),
    query_bus: QueryBus = Depends(get_query_bus),
    current_user=Depends(get_current_admin_user),
):
    """Get social media analytics."""
    try:
        query = GetSocialAnalyticsQuery(
            platforms=platforms,
            date_from=date_from,
            date_to=date_to,
            granularity=granularity,
            metrics=metrics,
        )

        result = await query_bus.execute(query)

        return JSONResponse(status_code=200, content={"success": True, "data": result})

    except Exception as e:
        logger.exception(f"Error getting social analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve social analytics")


@router.get("/unread-counts")
async def get_unread_counts(
    platforms: list[SocialPlatform] | None = QueryParam(None),
    assigned_to: UUID | None = QueryParam(None),
    group_by: str = QueryParam("platform"),
    query_bus: QueryBus = Depends(get_query_bus),
    current_user=Depends(get_current_admin_user),
):
    """Get unread message counts."""
    try:
        query = GetUnreadCountsQuery(
            platforms=platforms, assigned_to=assigned_to, group_by=group_by
        )

        result = await query_bus.execute(query)

        return JSONResponse(status_code=200, content={"success": True, "data": result})

    except Exception as e:
        logger.exception(f"Error getting unread counts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve unread counts")


@router.get("/leads")
async def get_social_leads(
    platforms: list[SocialPlatform] | None = QueryParam(None),
    date_from: datetime | None = QueryParam(None),
    date_to: datetime | None = QueryParam(None),
    converted_only: bool = QueryParam(False),
    page: int = QueryParam(1, ge=1),
    page_size: int = QueryParam(25, ge=1, le=100),
    query_bus: QueryBus = Depends(get_query_bus),
    current_user=Depends(get_current_admin_user),
):
    """Get social media leads."""
    try:
        query = GetSocialLeadsQuery(
            platforms=platforms,
            date_from=date_from,
            date_to=date_to,
            converted_only=converted_only,
            page=page,
            page_size=page_size,
        )

        result = await query_bus.execute(query)

        return JSONResponse(status_code=200, content={"success": True, "data": result})

    except Exception as e:
        logger.exception(f"Error getting social leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve social leads")


@router.post("/tools/{tool_name}")
async def execute_social_tool(
    tool_name: str,
    request: dict[str, Any],
    command_bus: CommandBus = Depends(get_command_bus),
    query_bus: QueryBus = Depends(get_query_bus),
    current_user=Depends(get_current_admin_user),
):
    """Execute social media AI tools."""
    try:
        toolkit = SocialMediaToolKit(command_bus, query_bus)
        result = await toolkit.execute_tool(tool_name, **request)

        return JSONResponse(
            status_code=200,
            content={
                "success": result.success,
                "message": result.message,
                "data": result.data,
                "requires_approval": result.requires_approval,
                "metadata": result.metadata,
            },
        )

    except Exception as e:
        logger.exception(f"Error executing social tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute tool: {tool_name}")


@router.get("/health")
async def social_health_check():
    """Health check for social media integration."""
    try:
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "features": [
                    "social_inbox",
                    "reviews_board",
                    "ai_responses",
                    "lead_creation",
                    "analytics",
                ],
            },
        )

    except Exception as e:
        logger.exception(f"Social health check failed: {e}")
        raise HTTPException(status_code=500, detail="Social media integration unhealthy")
