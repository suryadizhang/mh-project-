"""
API endpoints for customer reviews and feedback.
"""

import logging
from typing import Optional
from uuid import UUID, uuid4

from core.database import get_db
from services.review_service import ReviewService
from services.media import R2StorageService, MediaProcessingService
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
)
from pydantic import BaseModel, Field
from services.unified_notification_service import (
    notify_complaint,
    notify_review,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from db.models.feedback_marketing import (
    CustomerReview,
    ReviewMedia,
    MediaType,
    MediaProcessingStatus,
)

logger = logging.getLogger(__name__)

# Media constraints
MAX_MEDIA_FILES = 5
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB

router = APIRouter(tags=["reviews"])  # No prefix - added in main.py


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


class ReviewCreateRequest(BaseModel):
    """Request model for creating a new review."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: str | None = Field(None, description="Review comment/feedback")
    customer_email: str = Field(..., description="Customer email address")
    booking_id: UUID | None = Field(None, description="Associated booking ID (if any)")


class PublicReviewResponse(BaseModel):
    """Response model for public review submission."""

    success: bool
    review_id: str
    message: str
    media_count: int = 0
    media_processing: bool = False


async def process_media_background(
    db_session_factory,
    review_id: UUID,
    media_records: list[dict],
):
    """
    Background task to process uploaded media files.

    This runs AFTER the HTTP response is sent, so users don't wait.
    """
    from core.database import AsyncSessionLocal

    r2_service = R2StorageService()
    media_service = MediaProcessingService()

    logger.info(
        f"🎬 Starting background media processing for review {review_id}, {len(media_records)} files"
    )

    async with AsyncSessionLocal() as db:
        for media_record in media_records:
            media_id = media_record["id"]
            file_bytes = media_record["file_bytes"]
            filename = media_record["filename"]
            content_type = media_record["content_type"]
            media_type = media_record["media_type"]

            try:
                # Update status to processing
                await db.execute(
                    update(ReviewMedia)
                    .where(ReviewMedia.id == media_id)
                    .values(processing_status=MediaProcessingStatus.PROCESSING)
                )
                await db.commit()

                # Process media
                if media_type == MediaType.IMAGE:
                    processed = media_service.process_image(file_bytes, filename, content_type)
                else:
                    processed = media_service.process_video(file_bytes, filename, content_type)

                # Upload to R2
                # Original
                original_url = await r2_service.upload_review_media(
                    review_id=review_id,
                    file_data=file_bytes,
                    filename=f"original_{filename}",
                    content_type=content_type,
                    subfolder="original",
                )

                # Optimized
                optimized_url = await r2_service.upload_review_media(
                    review_id=review_id,
                    file_data=processed["optimized"],
                    filename=f"optimized_{processed['optimized_filename']}",
                    content_type=processed["content_type"],
                    subfolder="optimized",
                )

                # Thumbnail
                thumbnail_url = await r2_service.upload_review_media(
                    review_id=review_id,
                    file_data=processed["thumbnail"],
                    filename=f"thumb_{processed['thumbnail_filename']}",
                    content_type="image/jpeg",  # Thumbnails are always JPEG
                    subfolder="thumbnails",
                )

                # Update record with URLs and dimensions
                update_values = {
                    "original_url": original_url,
                    "optimized_url": optimized_url,
                    "thumbnail_url": thumbnail_url,
                    "processing_status": MediaProcessingStatus.COMPLETED,
                    "processed_at": "NOW()",
                }

                if "width" in processed:
                    update_values["width"] = processed["width"]
                    update_values["height"] = processed["height"]

                await db.execute(
                    update(ReviewMedia).where(ReviewMedia.id == media_id).values(**update_values)
                )
                await db.commit()

                logger.info(f"✅ Processed media {media_id} for review {review_id}")

            except Exception as e:
                logger.error(f"❌ Failed to process media {media_id}: {e}")
                await db.execute(
                    update(ReviewMedia)
                    .where(ReviewMedia.id == media_id)
                    .values(
                        processing_status=MediaProcessingStatus.FAILED,
                        processing_error=str(e)[:500],
                    )
                )
                await db.commit()

    logger.info(f"🎬 Completed background media processing for review {review_id}")


@router.post("/submit-public", response_model=PublicReviewResponse)
async def submit_public_review(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    rating: int = Form(..., ge=1, le=5, description="Rating from 1-5"),
    review_text: Optional[str] = Form(None, description="Review text/feedback"),
    customer_email: str = Form(..., description="Customer email"),
    customer_name: Optional[str] = Form(None, description="Customer name"),
    booking_id: Optional[str] = Form(None, description="Associated booking ID"),
    files: list[UploadFile] = File(default=[], description="Media files (images/videos, max 5)"),
):
    """
    Public endpoint for customers to submit reviews with optional media uploads.

    Accepts multipart/form-data with:
    - rating: 1-5 stars (required)
    - review_text: Text feedback (optional)
    - customer_email: Email address (required)
    - customer_name: Customer name (optional)
    - booking_id: Associated booking UUID (optional)
    - files: Up to 5 image/video files (optional)

    Media files are processed asynchronously in the background.
    Response is returned immediately after review creation.
    """
    import asyncio

    # Validate file count
    if len(files) > MAX_MEDIA_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_MEDIA_FILES} files allowed",
        )

    # Validate files before processing
    media_to_process = []
    for file in files:
        if not file.filename:
            continue

        content_type = file.content_type or ""

        # Determine media type
        if content_type in ALLOWED_IMAGE_TYPES:
            media_type = MediaType.IMAGE
            max_size = MAX_IMAGE_SIZE
        elif content_type in ALLOWED_VIDEO_TYPES:
            media_type = MediaType.VIDEO
            max_size = MAX_VIDEO_SIZE
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {content_type}. Allowed: images (jpeg, png, webp, heic) and videos (mp4, mov, avi, webm)",
            )

        # Read file content
        file_bytes = await file.read()
        file_size = len(file_bytes)

        if file_size > max_size:
            size_mb = max_size / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file.filename} exceeds maximum size of {size_mb}MB",
            )

        media_to_process.append(
            {
                "file_bytes": file_bytes,
                "filename": file.filename,
                "content_type": content_type,
                "file_size": file_size,
                "media_type": media_type,
            }
        )

    # Parse booking_id if provided
    parsed_booking_id = None
    if booking_id:
        try:
            parsed_booking_id = UUID(booking_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking_id format"
            )

    # Get client info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        # Create review using service
        service = ReviewService(db)

        # Map rating to text format used by existing service
        rating_map = {5: "great", 4: "good", 3: "okay", 2: "could_be_better", 1: "could_be_better"}
        rating_text = rating_map.get(rating, "okay")

        # Create review record directly since we need more control
        review = CustomerReview(
            id=uuid4(),
            customer_email=customer_email,
            customer_name=customer_name,
            booking_id=parsed_booking_id,
            rating=rating_text,
            review_text=review_text,
            improvement_suggestions=review_text,  # Use same text for suggestions
            status="submitted",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(review)
        await db.flush()  # Get the review ID

        # Create media records (pending processing)
        media_records_for_background = []
        for idx, media in enumerate(media_to_process):
            media_record = ReviewMedia(
                id=uuid4(),
                review_id=review.id,
                media_type=media["media_type"],
                original_filename=media["filename"],
                file_size_bytes=media["file_size"],
                content_type=media["content_type"],
                processing_status=MediaProcessingStatus.PENDING,
                display_order=idx,
            )
            db.add(media_record)

            # Prepare for background processing
            media_records_for_background.append(
                {
                    "id": media_record.id,
                    "file_bytes": media["file_bytes"],
                    "filename": media["filename"],
                    "content_type": media["content_type"],
                    "media_type": media["media_type"],
                }
            )

        await db.commit()

        # Queue background task for media processing
        if media_records_for_background:
            background_tasks.add_task(
                process_media_background,
                None,  # Will use AsyncSessionLocal inside
                review.id,
                media_records_for_background,
            )

        # Send notification for the review
        is_complaint = rating <= 2
        if is_complaint and review_text:
            asyncio.create_task(
                notify_complaint(
                    customer_name=customer_name or customer_email,
                    customer_phone=None,
                    booking_id=str(parsed_booking_id) if parsed_booking_id else "Unknown",
                    complaint_text=review_text,
                    priority="high" if rating == 1 else "medium",
                )
            )
        else:
            asyncio.create_task(
                notify_review(
                    customer_name=customer_name or customer_email,
                    rating=str(rating),
                    review_text=review_text[:100] if review_text else "No feedback provided",
                )
            )

        logger.info(
            f"✅ Created review {review.id} with {len(media_records_for_background)} media files"
        )

        return PublicReviewResponse(
            success=True,
            review_id=str(review.id),
            message="Review submitted successfully"
            + (". Media files are being processed." if media_records_for_background else ""),
            media_count=len(media_records_for_background),
            media_processing=len(media_records_for_background) > 0,
        )

    except Exception as e:
        logger.error(f"❌ Failed to create review: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit review. Please try again.",
        )


# Public endpoints (customer-facing)
@router.get("/")
async def list_reviews(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List reviews (paginated)."""
    # TODO: Implement actual review listing logic
    # For now, return placeholder response
    return {
        "reviews": [],
        "total": 0,
        "skip": skip,
        "limit": limit,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new customer review."""
    # TODO: Implement actual review creation logic
    # For now, return placeholder response
    return {
        "id": "review-placeholder",
        "rating": data.rating,
        "comment": data.comment,
        "customer_email": data.customer_email,
        "status": "pending",
        "created_at": "2024-10-19T10:30:00Z",
    }


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
        "booking_date": (review.booking.date.isoformat() if review.booking else None),
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
                priority=("high" if data.rating == "could_be_better" else "medium"),
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
    review_id: UUID,
    data: ExternalReviewTrackingRequest,
    db: AsyncSession = Depends(get_db),
):
    """Track when customer leaves external review (Yelp/Google)."""
    service = ReviewService(db)

    success = await service.track_external_review(review_id=review_id, platform=data.platform)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to track external review",
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to apply coupon",
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
    customer_id: UUID,
    station_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
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
                "submitted_at": (review.submitted_at.isoformat() if review.submitted_at else None),
                "coupon_issued": review.coupon_issued,
                "left_external_review": review.left_yelp_review or review.left_google_review,
            }
            for review in reviews
        ]
    }


# Admin endpoints
@router.get("/admin/escalated")
async def get_escalated_reviews(
    station_id: UUID,
    status: str = "escalated",
    db: AsyncSession = Depends(get_db),
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
                "submitted_at": (review.submitted_at.isoformat() if review.submitted_at else None),
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
    review_id: UUID,
    data: ReviewResolutionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Resolve an escalated review (admin only)."""
    service = ReviewService(db)

    success = await service.resolve_review(
        review_id=review_id,
        resolved_by=data.resolved_by,
        resolution_notes=data.resolution_notes,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to resolve review",
        )

    return {"success": True, "message": "Review resolved successfully"}


# AI Service endpoints
@router.post("/ai/issue-coupon")
async def ai_issue_coupon(data: AIInteractionRequest, db: AsyncSession = Depends(get_db)):
    """
    AI service calls this to issue coupon after interacting with customer.

    ⚠️ CRITICAL: Only for EXISTING CUSTOMERS with completed bookings (complaint compensation).
    NOT for promotional discounts (admin-only).

    Requirements:
    - Must have booking_id (existing customer)
    - Must be 'could_be_better' review (complaint)
    - After AI determines compensation is warranted
    - Max 10% or $100 cap (whichever is less)
    """
    service = ReviewService(db)

    coupon = await service.issue_coupon_after_ai_interaction(
        review_id=data.review_id,
        ai_interaction_notes=data.ai_interaction_notes,
        discount_percentage=data.discount_percentage,
    )

    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to issue coupon",
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
        review_id=data.review_id,
        ai_notes=data.ai_notes,
        priority=data.priority,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to escalate to human",
        )

    return {
        "success": True,
        "message": "Escalated to human admin",
        "priority": data.priority,
    }


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
