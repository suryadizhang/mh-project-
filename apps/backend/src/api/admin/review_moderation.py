"""
Admin Review Moderation API
Endpoints for reviewing and moderating customer review submissions

Features:
- View pending reviews (FIFO queue)
- Approve/reject individual reviews
- Bulk approve/reject
- Audit log tracking
- Email notifications (optional)
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from datetime import datetime
from typing import Any

# Import database and models
from api.app.database import get_db
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from models.review import CustomerReviewBlogPost, ReviewApprovalLog
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Create router
router = APIRouter(prefix="/api/admin/review-moderation", tags=["admin-review-moderation"])


# ============================================================================
# Pydantic Models
# ============================================================================


class ApproveReviewRequest(BaseModel):
    """Request model for approving a review"""

    admin_id: int = Field(..., description="ID of admin approving the review")
    comment: str | None = Field(None, description="Optional comment from admin")
    notify_customer: bool = Field(True, description="Send email notification to customer")


class RejectReviewRequest(BaseModel):
    """Request model for rejecting a review"""

    admin_id: int = Field(..., description="ID of admin rejecting the review")
    reason: str = Field(..., description="Reason for rejection (required)")
    notify_customer: bool = Field(True, description="Send email notification to customer")


class BulkActionRequest(BaseModel):
    """Request model for bulk actions"""

    review_ids: list[int] = Field(..., description="List of review IDs to process")
    action: str = Field(..., description="Action: 'approve' or 'reject'")
    admin_id: int = Field(..., description="ID of admin performing action")
    reason: str | None = Field(None, description="Reason (required for reject)")
    notify_customers: bool = Field(True, description="Send email notifications")


class ReviewResponse(BaseModel):
    """Response model for review data"""

    id: int
    title: str
    content: str
    rating: int
    customer_name: str
    customer_email: str
    customer_phone: str | None
    images: list[dict[str, Any]]
    google_review_url: str | None
    yelp_review_url: str | None
    status: str
    created_at: datetime
    likes_count: int
    helpful_count: int

    class Config:
        from_attributes = True


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/pending-reviews")
async def get_pending_reviews(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field: created_at, rating"),
    order: str = Query("asc", description="Sort order: asc (FIFO) or desc"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get pending reviews in FIFO queue (oldest first by default)

    Features:
    - Pagination support
    - FIFO ordering (oldest pending first)
    - Media preview metadata included
    - Customer contact info
    """
    try:
        # Calculate offset
        offset = (page - 1) * limit

        # Build query for pending reviews
        query = select(CustomerReviewBlogPost).where(CustomerReviewBlogPost.status == "pending")

        # Apply sorting (FIFO = oldest first)
        if order == "desc":
            query = query.order_by(getattr(CustomerReviewBlogPost, sort_by).desc())
        else:
            query = query.order_by(getattr(CustomerReviewBlogPost, sort_by).asc())

        # Get total count
        count_query = (
            select(func.count())
            .select_from(CustomerReviewBlogPost)
            .where(CustomerReviewBlogPost.status == "pending")
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # Get paginated results
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        reviews = result.scalars().all()

        # Format response with media metadata
        reviews_data = []
        for review in reviews:
            reviews_data.append(
                {
                    "id": review.id,
                    "title": review.title,
                    "content": review.content,
                    "rating": review.rating,
                    "customer_name": review.customer_name,
                    "customer_email": review.customer_email,
                    "customer_phone": review.customer_phone,
                    "images": review.get_images(),  # JSON parsed
                    "google_review_url": review.google_review_url,
                    "yelp_review_url": review.yelp_review_url,
                    "status": review.status,
                    "created_at": review.created_at.isoformat(),
                    "likes_count": review.likes_count,
                    "helpful_count": review.helpful_count,
                    "has_external_reviews": bool(
                        review.google_review_url or review.yelp_review_url
                    ),
                    "media_count": len(review.get_images()),
                    "image_count": len(
                        [img for img in review.get_images() if img.get("resource_type") == "image"]
                    ),
                    "video_count": len(
                        [img for img in review.get_images() if img.get("resource_type") == "video"]
                    ),
                }
            )

        return {
            "success": True,
            "data": reviews_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit,
                "has_next": offset + limit < total,
                "has_prev": page > 1,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pending reviews: {e!s}")


@router.post("/approve-review/{review_id}")
async def approve_review(
    review_id: int, request: ApproveReviewRequest, db: AsyncSession = Depends(get_db)
):
    """
    Approve a review and make it public

    Features:
    - Sets status to 'approved'
    - Sets approved_at timestamp
    - Creates audit log entry
    - Optional email notification
    """
    try:
        # Get review
        query = select(CustomerReviewBlogPost).where(CustomerReviewBlogPost.id == review_id)
        result = await db.execute(query)
        review = result.scalar_one_or_none()

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        if review.status != "pending":
            raise HTTPException(status_code=400, detail=f"Review is already {review.status}")

        # Approve the review using helper method
        review.approve(request.admin_id)

        # Create audit log
        log = ReviewApprovalLog.create_log(
            review_id=review_id,
            action="approved",
            admin_id=request.admin_id,
            comment=request.comment or "Review approved",
        )
        db.add(log)

        # Commit changes
        await db.commit()
        await db.refresh(review)

        # TODO: Send email notification if requested
        if request.notify_customer:
            # Email service integration would go here
            pass

        return {
            "success": True,
            "message": "Review approved successfully",
            "data": {
                "review_id": review.id,
                "status": review.status,
                "approved_at": review.approved_at.isoformat() if review.approved_at else None,
                "approved_by": review.approved_by,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error approving review: {e!s}")


@router.post("/reject-review/{review_id}")
async def reject_review(
    review_id: int, request: RejectReviewRequest, db: AsyncSession = Depends(get_db)
):
    """
    Reject a review with reason

    Features:
    - Sets status to 'rejected'
    - Stores rejection reason
    - Creates audit log entry
    - Optional email notification with reason
    """
    try:
        # Get review
        query = select(CustomerReviewBlogPost).where(CustomerReviewBlogPost.id == review_id)
        result = await db.execute(query)
        review = result.scalar_one_or_none()

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        if review.status != "pending":
            raise HTTPException(status_code=400, detail=f"Review is already {review.status}")

        # Reject the review using helper method
        review.reject(request.admin_id, request.reason)

        # Create audit log
        log = ReviewApprovalLog.create_log(
            review_id=review_id,
            action="rejected",
            admin_id=request.admin_id,
            comment=f"Rejected: {request.reason}",
        )
        db.add(log)

        # Commit changes
        await db.commit()
        await db.refresh(review)

        # TODO: Send email notification if requested
        if request.notify_customer:
            # Email service integration would go here
            # Include rejection reason in email
            pass

        return {
            "success": True,
            "message": "Review rejected successfully",
            "data": {
                "review_id": review.id,
                "status": review.status,
                "rejection_reason": review.rejection_reason,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error rejecting review: {e!s}")


@router.post("/bulk-action")
async def bulk_action(request: BulkActionRequest, db: AsyncSession = Depends(get_db)):
    """
    Perform bulk approve or reject on multiple reviews

    Features:
    - Approve or reject multiple reviews at once
    - Creates audit log for each review
    - Returns success/failure counts
    - Optional email notifications
    """
    try:
        if request.action not in ["approve", "reject"]:
            raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")

        if request.action == "reject" and not request.reason:
            raise HTTPException(status_code=400, detail="Reason required for bulk reject")

        # Get all reviews
        query = select(CustomerReviewBlogPost).where(
            CustomerReviewBlogPost.id.in_(request.review_ids)
        )
        result = await db.execute(query)
        reviews = result.scalars().all()

        success_count = 0
        failed_count = 0
        errors = []

        for review in reviews:
            try:
                # Skip if not pending
                if review.status != "pending":
                    errors.append(f"Review {review.id} is already {review.status}")
                    failed_count += 1
                    continue

                # Perform action
                if request.action == "approve":
                    review.approve(request.admin_id)
                    action_text = "approved"
                else:
                    review.reject(request.admin_id, request.reason)
                    action_text = "rejected"

                # Create audit log
                log = ReviewApprovalLog.create_log(
                    review_id=review.id,
                    action=action_text,
                    admin_id=request.admin_id,
                    comment=request.reason if request.action == "reject" else f"Bulk {action_text}",
                )
                db.add(log)

                success_count += 1

            except Exception as e:
                errors.append(f"Review {review.id}: {e!s}")
                failed_count += 1

        # Commit all changes
        await db.commit()

        # TODO: Send email notifications if requested
        if request.notify_customers:
            # Email service integration would go here
            pass

        return {
            "success": True,
            "message": "Bulk action completed",
            "data": {
                "action": request.action,
                "total_requested": len(request.review_ids),
                "success_count": success_count,
                "failed_count": failed_count,
                "errors": errors if errors else None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error performing bulk action: {e!s}")


@router.get("/approval-log/{review_id}")
async def get_approval_log(review_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get approval audit log for a specific review

    Returns:
    - All approval actions taken on this review
    - Admin who performed each action
    - Timestamps and comments
    """
    try:
        # Get review to verify it exists
        query = select(CustomerReviewBlogPost).where(CustomerReviewBlogPost.id == review_id)
        result = await db.execute(query)
        review = result.scalar_one_or_none()

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        # Get audit log entries
        log_query = (
            select(ReviewApprovalLog)
            .where(ReviewApprovalLog.review_id == review_id)
            .order_by(ReviewApprovalLog.created_at.desc())
        )

        log_result = await db.execute(log_query)
        logs = log_result.scalars().all()

        # Format response
        log_data = []
        for log in logs:
            log_data.append(
                {
                    "id": log.id,
                    "review_id": log.review_id,
                    "action": log.action,
                    "admin_id": log.admin_id,
                    "comment": log.comment,
                    "created_at": log.created_at.isoformat(),
                }
            )

        return {
            "success": True,
            "data": {
                "review_id": review_id,
                "current_status": review.status,
                "logs": log_data,
                "total_actions": len(log_data),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching approval log: {e!s}")


@router.get("/stats")
async def get_moderation_stats(db: AsyncSession = Depends(get_db)):
    """
    Get moderation statistics

    Returns:
    - Count by status (pending, approved, rejected)
    - Average approval time
    - Recent activity
    """
    try:
        # Count by status
        pending_query = (
            select(func.count())
            .select_from(CustomerReviewBlogPost)
            .where(CustomerReviewBlogPost.status == "pending")
        )
        approved_query = (
            select(func.count())
            .select_from(CustomerReviewBlogPost)
            .where(CustomerReviewBlogPost.status == "approved")
        )
        rejected_query = (
            select(func.count())
            .select_from(CustomerReviewBlogPost)
            .where(CustomerReviewBlogPost.status == "rejected")
        )

        pending_result = await db.execute(pending_query)
        approved_result = await db.execute(approved_query)
        rejected_result = await db.execute(rejected_query)

        pending_count = pending_result.scalar()
        approved_count = approved_result.scalar()
        rejected_count = rejected_result.scalar()

        return {
            "success": True,
            "data": {
                "pending_count": pending_count,
                "approved_count": approved_count,
                "rejected_count": rejected_count,
                "total_reviews": pending_count + approved_count + rejected_count,
                "approval_rate": (
                    round(approved_count / (approved_count + rejected_count) * 100, 2)
                    if (approved_count + rejected_count) > 0
                    else 0
                ),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {e!s}")


@router.put("/hold-review/{review_id}")
async def hold_review(
    review_id: int,
    admin_id: int = Body(..., embed=True),
    reason: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    """
    Put a review on hold for further investigation

    Features:
    - Sets status to 'on_hold'
    - Stores reason for hold
    - Creates audit log entry
    """
    try:
        # Get review
        query = select(CustomerReviewBlogPost).where(CustomerReviewBlogPost.id == review_id)
        result = await db.execute(query)
        review = result.scalar_one_or_none()

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        # Update status
        review.status = "on_hold"
        review.rejection_reason = f"On hold: {reason}"

        # Create audit log
        log = ReviewApprovalLog.create_log(
            review_id=review_id,
            action="on_hold",
            admin_id=admin_id,
            comment=f"Put on hold: {reason}",
        )
        db.add(log)

        await db.commit()
        await db.refresh(review)

        return {
            "success": True,
            "message": "Review put on hold",
            "data": {"review_id": review.id, "status": review.status, "reason": reason},
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error holding review: {e!s}")
