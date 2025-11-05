"""
API endpoints for customer reviews and feedback.
"""

import logging
from uuid import UUID

from core.database import get_db
from services.review_service import ReviewService
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from services.unified_notification_service import (
    notify_complaint,
    notify_review,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])


# Pydantic models
class ReviewSubmissionRequest(BaseModel):
    """Request model for submitting a review."""

    rating: str = Field(..., description="Rating: great, good, okay, could_be_better")
    complaint_text: str | None = Field(None, description="Required for negative reviews")
    improvement_suggestions: str | None = Field(None, description="How we can improve")


class ExternalReviewTrackingRequest(BaseModel):
    """Request model for tracking external reviews."""

    platform: str = Field(..., description="Platform: yelp or google")


class CouponValidationRequest(BaseModel):
    """Request model for validating a coupon."""

    coupon_code: str = Field(..., description="Coupon code to validate")
    customer_id: UUID = Field(..., description="Customer ID")
    order_total_cents: int = Field(..., description="Order total in cents")


class CouponApplicationRequest(BaseModel):
    """Request model for applying a coupon."""

    coupon_code: str = Field(..., description="Coupon code to apply")
    booking_id: UUID = Field(..., description="Booking ID")


class ReviewResolutionRequest(BaseModel):
    """Request model for resolving a review."""

    resolved_by: UUID = Field(..., description="Admin user ID who resolved the issue")
    resolution_notes: str = Field(..., description="Notes about the resolution")


class AIInteractionRequest(BaseModel):
    """Request model for AI to issue coupon after interaction."""

    review_id: UUID = Field(..., description="Review ID")
    ai_interaction_notes: str = Field(..., description="Notes from AI interaction")
    discount_percentage: int = Field(10, description="Discount percentage (default 10%)")


class AIEscalationRequest(BaseModel):
    """Request model for AI to escalate to human."""

    review_id: UUID = Field(..., description="Review ID")
    ai_notes: str = Field(..., description="AI notes about why escalation needed")
    priority: str = Field("urgent", description="Escalation priority: low, medium, high, urgent")


# Public endpoints (customer-facing)
@router.get("/{review_id}")
async def get_review(review_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get review details for customer review page."""
    service = ReviewService(db)
    review = await service.get_review_by_id(review_id)

    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    # Return limited data for public access
    return {
        "id": str(review.id),
        "status": review.status,
        "rating": review.rating if review.status != "pending" else None,
        "submitted": review.status != "pending",
        "booking_date": review.booking.date.isoformat() if review.booking else None,
        "customer_name": f"{review.customer.first_name if hasattr(review.customer, 'first_name') else 'Valued Customer'}",
        "coupon_issued": review.coupon_issued,
        "coupon_code": review.coupon.coupon_code if review.coupon else None,
    }


@router.post("/{review_id}/submit")
async def submit_review(
    review_id: UUID,
    data: ReviewSubmissionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Submit a customer review."""
    import asyncio

    service = ReviewService(db)

    # Get client IP and user agent
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    result = await service.submit_review(
        review_id=review_id,
        rating=data.rating,
        complaint_text=data.complaint_text,
        improvement_suggestions=data.improvement_suggestions,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to submit review"),
        )

    # Send WhatsApp notification based on rating (non-blocking)
    # Get review details from result
    review_data = result.get("review", {})
    customer_name = review_data.get("customer_name", "Customer")
    customer_phone = review_data.get("customer_phone")
    rating_text = data.rating.replace("_", " ").title()

    # Determine if this is a complaint or positive review
    is_complaint = data.rating in ("could_be_better", "okay")

    if is_complaint and data.complaint_text:
        # Send complaint notification
        asyncio.create_task(
            notify_complaint(
                customer_name=customer_name,
                customer_phone=customer_phone,
                booking_id=str(review_data.get("booking_id", "Unknown")),
                complaint_text=data.complaint_text,
                priority="high" if data.rating == "could_be_better" else "medium",
            )
        )
        logger.info(f"📧 WhatsApp complaint notification queued for review {review_id}")
    else:
        # Send positive review notification
        asyncio.create_task(
            notify_review(
                customer_name=customer_name,
                rating=rating_text,
                review_text=f"{data.improvement_suggestions[:100] if data.improvement_suggestions else 'No additional feedback'}",
            )
        )
        logger.info(f"📧 WhatsApp review notification queued for review {review_id}")

    return result


@router.post("/{review_id}/track-external")
async def track_external_review(
    review_id: UUID, data: ExternalReviewTrackingRequest, db: AsyncSession = Depends(get_db)
):
    """Track when customer leaves external review (Yelp/Google)."""
    service = ReviewService(db)

    success = await service.track_external_review(review_id=review_id, platform=data.platform)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to track external review"
        )

    return {"success": True, "message": f"Tracked {data.platform} review"}


# Coupon endpoints
@router.post("/coupons/validate")
async def validate_coupon(data: CouponValidationRequest, db: AsyncSession = Depends(get_db)):
    """Validate a discount coupon."""
    service = ReviewService(db)

    result = await service.validate_coupon(
        coupon_code=data.coupon_code,
        customer_id=data.customer_id,
        order_total_cents=data.order_total_cents,
    )

    return result


@router.post("/coupons/apply")
async def apply_coupon(data: CouponApplicationRequest, db: AsyncSession = Depends(get_db)):
    """Apply a discount coupon to a booking."""
    service = ReviewService(db)

    success = await service.apply_coupon(coupon_code=data.coupon_code, booking_id=data.booking_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to apply coupon"
        )

    return {"success": True, "message": "Coupon applied successfully"}


@router.get("/customers/{customer_id}/coupons")
async def get_customer_coupons(
    customer_id: UUID,
    station_id: UUID | None = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """Get customer's available coupons."""
    service = ReviewService(db)

    coupons = await service.get_customer_coupons(
        customer_id=customer_id, station_id=station_id, active_only=active_only
    )

    return {
        "coupons": [
            {
                "id": str(coupon.id),
                "code": coupon.coupon_code,
                "discount_display": coupon.discount_display,
                "description": coupon.description,
                "minimum_order": coupon.minimum_order_cents / 100,
                "valid_until": coupon.valid_until.isoformat(),
                "is_valid": coupon.is_valid,
                "times_used": coupon.times_used,
                "max_uses": coupon.max_uses,
            }
            for coupon in coupons
        ]
    }


@router.get("/customers/{customer_id}/reviews")
async def get_customer_reviews(
    customer_id: UUID, station_id: UUID | None = None, db: AsyncSession = Depends(get_db)
):
    """Get customer's review history."""
    service = ReviewService(db)

    reviews = await service.get_customer_reviews(customer_id=customer_id, station_id=station_id)

    return {
        "reviews": [
            {
                "id": str(review.id),
                "booking_id": str(review.booking_id),
                "rating": review.rating,
                "status": review.status,
                "submitted_at": review.submitted_at.isoformat() if review.submitted_at else None,
                "coupon_issued": review.coupon_issued,
                "left_external_review": review.left_yelp_review or review.left_google_review,
            }
            for review in reviews
        ]
    }


# Admin endpoints
@router.get("/admin/escalated")
async def get_escalated_reviews(
    station_id: UUID, status: str = "escalated", db: AsyncSession = Depends(get_db)
):
    """Get escalated reviews for admin dashboard."""
    service = ReviewService(db)

    reviews = await service.get_escalated_reviews(station_id=station_id, status=status)

    return {
        "reviews": [
            {
                "id": str(review.id),
                "booking_id": str(review.booking_id),
                "customer_id": str(review.customer_id),
                "customer_name": f"{review.customer.first_name if hasattr(review.customer, 'first_name') else ''} {review.customer.last_name if hasattr(review.customer, 'last_name') else ''}".strip(),
                "rating": review.rating,
                "complaint_text": review.complaint_text,
                "improvement_suggestions": review.improvement_suggestions,
                "submitted_at": review.submitted_at.isoformat() if review.submitted_at else None,
                "escalated_at": (
                    review.admin_notified_at.isoformat() if review.admin_notified_at else None
                ),
                "coupon_issued": review.coupon_issued,
                "escalations": [
                    {
                        "id": str(esc.id),
                        "type": esc.escalation_type,
                        "priority": esc.priority,
                        "status": esc.status,
                        "reason": esc.escalation_reason,
                        "created_at": esc.created_at.isoformat(),
                    }
                    for esc in review.escalations
                ],
            }
            for review in reviews
        ]
    }


@router.post("/{review_id}/resolve")
async def resolve_review(
    review_id: UUID, data: ReviewResolutionRequest, db: AsyncSession = Depends(get_db)
):
    """Resolve an escalated review (admin only)."""
    service = ReviewService(db)

    success = await service.resolve_review(
        review_id=review_id, resolved_by=data.resolved_by, resolution_notes=data.resolution_notes
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to resolve review"
        )

    return {"success": True, "message": "Review resolved successfully"}


# AI Service endpoints
@router.post("/ai/issue-coupon")
async def ai_issue_coupon(data: AIInteractionRequest, db: AsyncSession = Depends(get_db)):
    """
    AI service calls this to issue coupon after interacting with customer.
    Only for 'could_be_better' reviews after AI determines coupon is warranted.
    """
    service = ReviewService(db)

    coupon = await service.issue_coupon_after_ai_interaction(
        review_id=data.review_id,
        ai_interaction_notes=data.ai_interaction_notes,
        discount_percentage=data.discount_percentage,
    )

    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to issue coupon"
        )

    return {
        "success": True,
        "coupon": {
            "id": str(coupon.id),
            "code": coupon.coupon_code,
            "discount_display": coupon.discount_display,
            "valid_until": coupon.valid_until.isoformat(),
        },
    }


@router.post("/ai/escalate-to-human")
async def ai_escalate_to_human(data: AIEscalationRequest, db: AsyncSession = Depends(get_db)):
    """
    AI service calls this when it cannot resolve the complaint.
    Escalates to human admin with urgency.
    """
    service = ReviewService(db)

    success = await service.escalate_to_human(
        review_id=data.review_id, ai_notes=data.ai_notes, priority=data.priority
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to escalate to human"
        )

    return {"success": True, "message": "Escalated to human admin", "priority": data.priority}


@router.get("/admin/analytics")
async def get_review_analytics(station_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get review analytics for admin dashboard."""
    # This would query the feedback.review_analytics view
    query = """
        SELECT
            rating,
            status,
            review_count,
            yelp_reviews,
            google_reviews,
            coupons_issued,
            escalated_count,
            avg_response_hours,
            review_date
        FROM feedback.review_analytics
        WHERE station_id = :station_id
        ORDER BY review_date DESC
        LIMIT 30
    """

    result = await db.execute(query, {"station_id": str(station_id)})
    rows = result.fetchall()

    return {
        "analytics": [
            {
                "rating": row.rating,
                "status": row.status,
                "count": row.review_count,
                "yelp_reviews": row.yelp_reviews,
                "google_reviews": row.google_reviews,
                "coupons_issued": row.coupons_issued,
                "escalated": row.escalated_count,
                "avg_response_hours": (
                    float(row.avg_response_hours) if row.avg_response_hours else None
                ),
                "date": row.review_date.isoformat(),
            }
            for row in rows
        ]
    }


__all__ = ["router"]
