"""
AI Newsletter Endpoints - GPT-4 Powered Content Generation
Automated holiday newsletter generation with customer segmentation

IMPORTANT: Newsletters are sent via SMS (RingCentral), NOT email!
Email is only used for admin/transactional purposes (invoices, bookings, etc.)
"""

import logging
from datetime import datetime, timezone
from typing import Any

from api.deps import AdminUser, get_current_admin_user, get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from services.ai_newsletter_generator import (
    CustomerSegment,
    get_ai_newsletter_generator,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== Request/Response Models ====================


class NewsletterGenerateRequest(BaseModel):
    """Request to generate newsletters for upcoming holidays"""

    days_ahead: int = Field(
        default=60, ge=1, le=365, description="How many days ahead to generate newsletters for"
    )
    segments: list[CustomerSegment] | None = Field(
        default=None, description="Specific customer segments to generate for (default: all)"
    )


class NewsletterContentRequest(BaseModel):
    """Request to generate content for a specific holiday and segment"""

    holiday_key: str = Field(..., description="Holiday key (e.g., 'christmas', 'thanksgiving')")
    segment: CustomerSegment = Field(
        default=CustomerSegment.ALL, description="Customer segment to target"
    )


class NewsletterContentResponse(BaseModel):
    """Response with generated newsletter content"""

    id: str
    holiday_key: str
    holiday_name: str
    holiday_date: str
    segment: str
    subject_line: str
    content_html: str
    content_text: str
    preview_text: str
    send_date: str
    generated_at: datetime

    class Config:
        from_attributes = True


class NewsletterListResponse(BaseModel):
    """Response with list of generated newsletters"""

    newsletters: list[NewsletterContentResponse]
    total: int
    holidays_covered: list[str]


class NewsletterSendRequest(BaseModel):
    """Request to send newsletter to subscribers"""

    holiday_key: str
    segment: CustomerSegment
    send_immediately: bool = Field(default=False, description="Send now or schedule for later")
    scheduled_time: datetime | None = Field(
        default=None, description="When to send (if not immediate)"
    )


class NewsletterSendResponse(BaseModel):
    """Response after sending newsletter"""

    success: bool
    newsletter_id: str
    recipients_count: int
    send_status: str
    scheduled_time: datetime | None = None
    message: str


# ==================== Endpoints ====================


@router.get(
    "/newsletters/generate",
    response_model=NewsletterListResponse,
    summary="Generate AI-powered newsletters for upcoming holidays",
    description="Automatically generates newsletter content for all upcoming holidays using GPT-4",
)
async def generate_newsletters(
    days_ahead: int = Query(
        default=60, ge=1, le=365, description="How many days ahead to look"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin_user),
) -> NewsletterListResponse:
    """
    Generate AI-powered newsletters for upcoming holidays.

    This endpoint:
    1. Finds all holidays in the next X days
    2. Uses GPT-4 to generate personalized content for each holiday
    3. Creates content for all customer segments
    4. Returns ready-to-send newsletters

    **Business Value:**
    - Saves 3-4 hours of manual content creation per newsletter
    - AI generates professional, engaging content
    - Personalized for different customer types
    - Automatic scheduling based on marketing windows
    """
    try:
        logger.info(f"Admin {current_user.email} generating newsletters for next {days_ahead} days")

        # Get AI newsletter generator
        generator = get_ai_newsletter_generator()

        # Generate newsletters for all upcoming holidays
        newsletters = await generator.generate_holiday_newsletters(days=days_ahead)

        if not newsletters:
            logger.warning(f"No holidays found in next {days_ahead} days")
            return NewsletterListResponse(
                newsletters=[],
                total=0,
                holidays_covered=[],
            )

        # Convert to response format
        newsletter_responses = []
        holidays_covered = set()

        for newsletter in newsletters:
            content = newsletter.get("content", {})
            newsletter_responses.append(
                NewsletterContentResponse(
                    id=newsletter["id"],
                    holiday_key=newsletter["holiday_key"],
                    holiday_name=newsletter["holiday_name"],
                    holiday_date=newsletter["holiday_date"].isoformat(),
                    segment=newsletter["target_segment"].value,
                    subject_line=newsletter["subject"],
                    content_html=content.get("html_content", ""),
                    content_text=content.get("text_content", ""),
                    preview_text=content.get("preview_text", ""),
                    send_date=newsletter["send_date"].isoformat(),
                    generated_at=newsletter["created_at"],
                )
            )
            holidays_covered.add(newsletter["holiday_name"])

        logger.info(
            f"Generated {len(newsletter_responses)} newsletters for {len(holidays_covered)} holidays"
        )

        return NewsletterListResponse(
            newsletters=newsletter_responses,
            total=len(newsletter_responses),
            holidays_covered=sorted(list(holidays_covered)),
        )

    except Exception as e:
        logger.error(f"Error generating newsletters: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate newsletters: {str(e)}",
        )


@router.post(
    "/newsletters/generate-content",
    response_model=NewsletterContentResponse,
    summary="Generate content for specific holiday and segment",
    description="Generate AI-powered newsletter content for a specific holiday and customer segment",
)
async def generate_newsletter_content(
    request: NewsletterContentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin_user),
) -> NewsletterContentResponse:
    """
    Generate newsletter content for a specific holiday and customer segment.

    **Use Cases:**
    - Preview content before bulk generation
    - Regenerate content if you don't like the first version
    - Create custom content for specific segments
    - Test different marketing angles
    """
    try:
        logger.info(
            f"Admin {current_user.email} generating content for {request.holiday_key} - {request.segment.value}"
        )

        # Get AI newsletter generator
        generator = get_ai_newsletter_generator()

        # Generate content for specific holiday and segment
        content = await generator.generate_content(
            holiday_key=request.holiday_key,
            segment=request.segment,
        )

        if not content or not content.get("html_content"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Holiday '{request.holiday_key}' not found or not in marketing window",
            )

        # Get holiday info from service
        holiday_service = generator.holiday_service
        context = holiday_service.get_holiday_message_context(request.holiday_key)
        
        # Find the holiday date
        upcoming = holiday_service.get_upcoming_holidays(days=365)
        holiday_date = None
        holiday_name = request.holiday_key.replace("_", " ").title()
        
        for h_key, h_obj, h_date in upcoming:
            if h_key == request.holiday_key:
                holiday_date = h_date
                holiday_name = h_obj.name
                break
        
        if not holiday_date:
            # Use context if available
            holiday_date = datetime.now(timezone.utc).date()

        logger.info(f"Generated content for {request.holiday_key}")

        return NewsletterContentResponse(
            id=f"{request.holiday_key}_{request.segment.value}_{datetime.now(timezone.utc).timestamp()}",
            holiday_key=request.holiday_key,
            holiday_name=holiday_name,
            holiday_date=holiday_date.isoformat(),
            segment=request.segment.value,
            subject_line=context.get("holiday_specific_message", f"{holiday_name} Special"),
            content_html=content.get("html_content", ""),
            content_text=content.get("text_content", ""),
            preview_text=content.get("preview_text", ""),
            send_date=datetime.now(timezone.utc).isoformat(),
            generated_at=datetime.now(timezone.utc),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating newsletter content: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}",
        )


@router.post(
    "/newsletters/send",
    response_model=NewsletterSendResponse,
    summary="Send newsletter to subscribers",
    description="Send generated newsletter to specific customer segment",
)
async def send_newsletter(
    request: NewsletterSendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin_user),
) -> NewsletterSendResponse:
    """
    Send newsletter to subscribers.

    **Steps:**
    1. Generate content if not already generated
    2. Get subscriber list for segment
    3. Send via email/SMS based on preferences
    4. Track opens, clicks, conversions

    **Note:** This is a placeholder. Full email sending integration requires:
    - SendGrid/Mailchimp integration
    - Subscriber database
    - Email template rendering
    - Tracking pixels for analytics
    """
    try:
        logger.info(
            f"Admin {current_user.email} sending newsletter: {request.holiday_key} to {request.segment.value}"
        )

        # TODO: Implement actual email sending
        # For now, return mock response
        return NewsletterSendResponse(
            success=True,
            newsletter_id=f"nl_{request.holiday_key}_{request.segment.value}_{datetime.now(timezone.utc).timestamp()}",
            recipients_count=0,  # TODO: Get actual subscriber count
            send_status="scheduled" if request.scheduled_time else "sent",
            scheduled_time=request.scheduled_time,
            message="Newsletter sending is not yet implemented. Please integrate SendGrid/Mailchimp.",
        )

    except Exception as e:
        logger.error(f"Error sending newsletter: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send newsletter: {str(e)}",
        )


@router.get(
    "/newsletters/preview/{holiday_key}",
    summary="Preview newsletter content",
    description="Get preview of newsletter content without sending",
)
async def preview_newsletter(
    holiday_key: str,
    segment: CustomerSegment = Query(default=CustomerSegment.ALL),
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """
    Preview newsletter content in HTML format.

    Returns the HTML version for rendering in admin dashboard.
    """
    try:
        generator = get_ai_newsletter_generator()
        content = await generator.generate_content(
            holiday_key=holiday_key,
            segment=segment,
        )

        if not content or not content.get("html_content"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Holiday '{holiday_key}' not found",
            )

        # Get subject line from context
        context = generator.holiday_service.get_holiday_message_context(holiday_key)

        return {
            "subject": context.get("holiday_specific_message", f"{holiday_key.replace('_', ' ').title()} Special"),
            "html": content.get("html_content", ""),
            "text": content.get("text_content", ""),
            "preview_text": content.get("preview_text", ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing newsletter: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview newsletter: {str(e)}",
        )
