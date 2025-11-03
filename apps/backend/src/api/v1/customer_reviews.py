"""
Customer Review Blog API - Production Grade
Supports: Images, Videos (like Facebook/Instagram/Twitter)
Features: Async/await, Cloudinary video upload, Admin moderation
"""

import os
import sys
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import JSONResponse
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from api.app.database import get_db
from models.review import CustomerReviewBlogPost, ReviewApprovalLog
from services.image_service import get_image_service

router = APIRouter(prefix="/api/customer-reviews", tags=["customer-reviews"])


@router.post("/submit-review")
async def submit_customer_review(
    title: str = Form(..., min_length=5, max_length=255),
    content: str = Form(..., min_length=50, max_length=5000),
    rating: int = Form(..., ge=1, le=5),
    customer_id: int = Form(...),  # TODO: Get from JWT token when auth is ready
    customer_name: str = Form(..., min_length=2, max_length=255),
    customer_email: str = Form(...),
    customer_phone: str | None = Form(None),
    show_initials_only: bool = Form(False),  # Privacy option
    booking_id: int | None = Form(None),
    reviewed_on_google: bool = Form(False),
    reviewed_on_yelp: bool = Form(False),
    google_review_link: str | None = Form(None),
    yelp_review_link: str | None = Form(None),
    media_files: list[UploadFile] = File(default=[]),  # Images + Videos
    db: AsyncSession = Depends(get_db),
):
    """
    Submit customer review with images/videos (Facebook/Instagram/Twitter style)

    Features:
    - Upload images (JPG, PNG, WEBP) up to 10MB each
    - Upload videos (MP4, MOV, WEBM) up to 100MB each
    - Max 10 media files total
    - Cloudinary auto-optimization
    - Admin approval workflow
    - Audit logging

    Returns:
        Success message with review ID and media count
    """

    try:
        # Validate media count
        if len(media_files) > 10:
            raise HTTPException(
                status_code=400, detail="Maximum 10 media files (images + videos) allowed"
            )

        # Filter out empty file uploads
        valid_media = [f for f in media_files if f.filename]

        # Generate slug
        slug_base = title.lower().replace(" ", "-")[:50]
        slug = f"{uuid.uuid4().hex[:8]}-{slug_base}"

        # Create review post (pending approval)
        review = CustomerReviewBlogPost(
            customer_id=customer_id,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            show_initials_only=show_initials_only,
            booking_id=booking_id,
            title=title,
            content=content,
            rating=rating,
            status="pending",
            reviewed_on_google=reviewed_on_google,
            reviewed_on_yelp=reviewed_on_yelp,
            google_review_link=google_review_link,
            yelp_review_link=yelp_review_link,
            slug=slug,
        )

        db.add(review)
        await db.commit()
        await db.refresh(review)

        # Upload media files (images + videos)
        uploaded_media = []
        if valid_media:
            image_service = get_image_service()
            uploaded_media = await image_service.upload_review_images(
                valid_media, review_id=review.id
            )

        # Save media URLs to review
        review.set_images(uploaded_media)  # Note: "images" field stores all media (images + videos)
        await db.commit()

        # Create approval log entry
        log = ReviewApprovalLog.create_log(
            review_id=review.id,
            action="pending_review",
            comment=f"New review submitted by customer with {len(uploaded_media)} media files",
        )
        db.add(log)
        await db.commit()

        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Review submitted successfully! It will appear after admin approval.",
                "review_id": review.id,
                "status": "pending",
                "media_uploaded": len(uploaded_media),
                "media_types": {
                    "images": sum(1 for m in uploaded_media if m.get("resource_type") == "image"),
                    "videos": sum(1 for m in uploaded_media if m.get("resource_type") == "video"),
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit review: {e!s}")


@router.get("/my-reviews")
async def get_my_reviews(
    customer_id: int = Query(...), db: AsyncSession = Depends(get_db)  # TODO: Get from JWT token
):
    """
    Get customer's own reviews (all statuses)

    Returns:
        List of customer's reviews with status, media, and rejection reason
    """

    result = await db.execute(
        select(CustomerReviewBlogPost)
        .filter(CustomerReviewBlogPost.customer_id == customer_id)
        .order_by(desc(CustomerReviewBlogPost.created_at))
    )
    reviews = result.scalars().all()

    return {
        "success": True,
        "reviews": [
            {
                "id": r.id,
                "title": r.title,
                "content": r.content,
                "rating": r.rating,
                "media": r.get_images(),  # Contains both images and videos
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "rejection_reason": r.rejection_reason if r.status == "rejected" else None,
                "reviewed_on_google": r.reviewed_on_google,
                "reviewed_on_yelp": r.reviewed_on_yelp,
            }
            for r in reviews
        ],
        "total": len(reviews),
    }


@router.get("/approved-reviews")
async def get_approved_reviews(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get approved customer reviews (public endpoint)

    Features:
    - Pagination
    - Newest first (Facebook newsfeed style)
    - Only approved reviews
    - Includes images + videos
    - Engagement metrics

    Returns:
        Paginated list of approved reviews with media
    """

    offset = (page - 1) * per_page

    # Query approved reviews with count
    count_query = (
        select(func.count())
        .select_from(CustomerReviewBlogPost)
        .filter(CustomerReviewBlogPost.status == "approved")
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Query reviews
    query = (
        select(CustomerReviewBlogPost)
        .filter(CustomerReviewBlogPost.status == "approved")
        .order_by(desc(CustomerReviewBlogPost.approved_at))
        .offset(offset)
        .limit(per_page)
    )

    result = await db.execute(query)
    reviews = result.scalars().all()

    return {
        "success": True,
        "reviews": [
            {
                "id": r.id,
                "title": r.title,
                "content": r.content,
                "rating": r.rating,
                "media": r.get_images(),  # Images + videos
                "customer_name": r.get_display_name(),  # Respects privacy: shows initials OR full name
                # Email and phone are HIDDEN for privacy (GDPR/CCPA compliance)
                # customer_email: HIDDEN
                # customer_phone: HIDDEN
                "created_at": r.created_at.isoformat(),
                "approved_at": r.approved_at.isoformat() if r.approved_at else None,
                "likes_count": r.likes_count,
                "helpful_count": r.helpful_count,
                "reviewed_on_google": r.reviewed_on_google,
                "reviewed_on_yelp": r.reviewed_on_yelp,
            }
            for r in reviews
        ],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page if total > 0 else 0,
            "has_next": offset + per_page < total,
            "has_prev": page > 1,
        },
    }


@router.get("/reviews/{review_id}")
async def get_review_by_id(review_id: int, db: AsyncSession = Depends(get_db)):
    """Get single review by ID (only if approved)"""

    result = await db.execute(
        select(CustomerReviewBlogPost).filter(
            CustomerReviewBlogPost.id == review_id, CustomerReviewBlogPost.status == "approved"
        )
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found or not approved")

    return {
        "success": True,
        "review": {
            "id": review.id,
            "title": review.title,
            "content": review.content,
            "rating": review.rating,
            "media": review.get_images(),
            "customer_name": review.get_display_name(),  # Respects privacy: shows initials OR full name
            # Email and phone are HIDDEN for privacy
            "created_at": review.created_at.isoformat(),
            "approved_at": review.approved_at.isoformat() if review.approved_at else None,
            "likes_count": review.likes_count,
            "helpful_count": review.helpful_count,
            "reviewed_on_google": review.reviewed_on_google,
            "reviewed_on_yelp": review.reviewed_on_yelp,
            "google_review_link": review.google_review_link,
            "yelp_review_link": review.yelp_review_link,
        },
    }


# Engagement endpoints
@router.post("/reviews/{review_id}/like")
async def like_review(review_id: int, db: AsyncSession = Depends(get_db)):
    """
    Like a review (atomic increment)

    Features:
    - No authentication required (public)
    - Atomic increment (no race conditions)
    - Only for approved reviews
    """

    result = await db.execute(
        select(CustomerReviewBlogPost).filter(
            CustomerReviewBlogPost.id == review_id, CustomerReviewBlogPost.status == "approved"
        )
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.increment_likes()
    await db.commit()
    await db.refresh(review)

    return {"success": True, "likes_count": review.likes_count}


@router.post("/reviews/{review_id}/helpful")
async def mark_helpful(review_id: int, db: AsyncSession = Depends(get_db)):
    """Mark review as helpful (atomic increment)"""

    result = await db.execute(
        select(CustomerReviewBlogPost).filter(
            CustomerReviewBlogPost.id == review_id, CustomerReviewBlogPost.status == "approved"
        )
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.increment_helpful()
    await db.commit()
    await db.refresh(review)

    return {"success": True, "helpful_count": review.helpful_count}


@router.get("/stats")
async def get_review_stats(db: AsyncSession = Depends(get_db)):
    """Get review statistics"""

    # Total reviews
    total_result = await db.execute(select(func.count()).select_from(CustomerReviewBlogPost))
    total_reviews = total_result.scalar() or 0

    # Approved reviews
    approved_result = await db.execute(
        select(func.count())
        .select_from(CustomerReviewBlogPost)
        .filter(CustomerReviewBlogPost.status == "approved")
    )
    approved_reviews = approved_result.scalar() or 0

    # Pending reviews
    pending_result = await db.execute(
        select(func.count())
        .select_from(CustomerReviewBlogPost)
        .filter(CustomerReviewBlogPost.status == "pending")
    )
    pending_reviews = pending_result.scalar() or 0

    # Average rating
    avg_result = await db.execute(
        select(func.avg(CustomerReviewBlogPost.rating)).filter(
            CustomerReviewBlogPost.status == "approved"
        )
    )
    avg_rating = avg_result.scalar() or 0

    return {
        "success": True,
        "stats": {
            "total_reviews": total_reviews,
            "approved_reviews": approved_reviews,
            "pending_reviews": pending_reviews,
            "average_rating": round(float(avg_rating), 2) if avg_rating else 0,
        },
    }
