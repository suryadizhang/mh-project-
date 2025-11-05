"""
Review service for managing customer reviews and feedback.
"""

from datetime import datetime, timedelta
import logging
from typing import Any
from uuid import UUID

from api.app.models.feedback import (
    CustomerReview,
    DiscountCoupon,
    ReviewEscalation,
)
from api.app.services.ringcentral_sms import ringcentral_sms
from core.config import get_settings
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

settings = get_settings()

logger = logging.getLogger(__name__)


class ReviewService:
    """Service for managing customer reviews and feedback."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_review_request(
        self, booking_id: UUID, customer_id: UUID, station_id: UUID
    ) -> CustomerReview | None:
        """Create a review request for a completed booking."""
        try:
            # Check if review already exists
            existing = await self.db.execute(
                select(CustomerReview).where(CustomerReview.booking_id == booking_id)
            )
            if existing.scalar_one_or_none():
                logger.info(f"Review already exists for booking {booking_id}")
                return None

            # Create review record
            review = CustomerReview(
                booking_id=booking_id,
                customer_id=customer_id,
                station_id=station_id,
                status="pending",
            )

            self.db.add(review)
            await self.db.commit()
            await self.db.refresh(review)

            logger.info(f"Created review request {review.id} for booking {booking_id}")
            return review

        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Error creating review request: {e}")
            return None

    async def send_review_sms(
        self, review_id: UUID, customer_phone: str, customer_name: str, base_url: str
    ) -> bool:
        """Send SMS review request to customer."""
        try:
            review = await self.db.get(CustomerReview, review_id)
            if not review:
                logger.error(f"Review {review_id} not found")
                return False

            # Generate review link
            review_link = f"{base_url}/review/{review.id}"

            # Compose SMS message
            message = (
                f"Hi {customer_name}! 🍱\n\n"
                f"Thank you for choosing My Hibachi Chef! "
                f"How was your hibachi experience?\n\n"
                f"Share your feedback: {review_link}\n\n"
                f"Your opinion helps us serve you better!"
            )

            # Send SMS via RingCentral
            async with ringcentral_sms as sms_service:
                response = await sms_service.send_sms(to_number=customer_phone, message=message)

            if response.success:
                # Update review record
                review.sms_sent_at = datetime.now()
                review.sms_message_id = response.message_id
                review.review_link = review_link

                await self.db.commit()
                logger.info(f"Review SMS sent for review {review_id}")
                return True
            else:
                logger.error(f"Failed to send review SMS: {response.error}")
                return False

        except Exception as e:
            logger.exception(f"Error sending review SMS: {e}")
            return False

    async def submit_review(
        self,
        review_id: UUID,
        rating: str,
        complaint_text: str | None = None,
        improvement_suggestions: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        """Submit customer review."""
        try:
            review = await self.db.get(
                CustomerReview, review_id, options=[selectinload(CustomerReview.customer)]
            )

            if not review:
                return {"success": False, "error": "Review not found"}

            if review.status != "pending":
                return {"success": False, "error": "Review already submitted"}

            # Validate rating
            valid_ratings = ["great", "good", "okay", "could_be_better"]
            if rating not in valid_ratings:
                return {"success": False, "error": "Invalid rating"}

            # Update review
            review.rating = rating
            review.status = "submitted"
            review.submitted_at = datetime.now()
            review.ip_address = ip_address
            review.user_agent = user_agent

            # Handle negative reviews
            if rating in ["okay", "could_be_better"]:
                if not complaint_text:
                    return {
                        "success": False,
                        "error": "Complaint text required for negative reviews",
                    }

                review.complaint_text = complaint_text
                review.improvement_suggestions = improvement_suggestions

                # "Okay" - Escalate to AI but no coupon (still acceptable)
                if rating == "okay":
                    review.status = "submitted"  # Keep as submitted, AI will handle
                    review.ai_escalated_at = datetime.now()

                    # Create escalation for AI to review
                    escalation = ReviewEscalation(
                        review_id=review.id,
                        escalation_type="ai_agent",
                        priority="low",
                        escalation_reason=f"Customer feedback (okay rating): {complaint_text[:200]}",
                        status="open",
                    )
                    self.db.add(escalation)
                    # AI will interact and decide if coupon needed

                # "Could be better" - Immediate escalation, AI handles coupon
                elif rating == "could_be_better":
                    review.status = "escalated"
                    review.ai_escalated_at = datetime.now()
                    review.admin_notified_at = datetime.now()

                    # Escalate to AI for immediate attention
                    escalation = ReviewEscalation(
                        review_id=review.id,
                        escalation_type="ai_agent",
                        priority="high",
                        escalation_reason=f"Serious complaint: {complaint_text[:200]}",
                        status="open",
                    )
                    self.db.add(escalation)

                    # Note: AI will issue coupon after interaction
                    # Coupon issued by AI service, not automatically here

            await self.db.commit()

            # Prepare response
            result = {
                "success": True,
                "rating": rating,
                "is_positive": rating in ["great", "good"],
                "needs_ai_interaction": rating in ["okay", "could_be_better"],
            }

            if rating in ["great", "good"]:
                result["redirect"] = "external_reviews"
                result["yelp_url"] = settings.yelp_review_url
                result["google_url"] = settings.google_review_url
            elif rating == "okay":
                result["redirect"] = "ai_followup"
                result["message"] = "Our team will review your feedback and reach out if needed."
            elif rating == "could_be_better":
                result["redirect"] = "ai_interaction"
                result["message"] = "We'd like to understand more and make this right."

            logger.info(f"Review {review_id} submitted with rating {rating}")
            return result

        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Error submitting review: {e}")
            return {"success": False, "error": str(e)}

    async def track_external_review(
        self, review_id: UUID, platform: str  # 'yelp' or 'google'
    ) -> bool:
        """Track when customer leaves external review."""
        try:
            review = await self.db.get(CustomerReview, review_id)
            if not review:
                return False

            if platform == "yelp":
                review.left_yelp_review = True
            elif platform == "google":
                review.left_google_review = True
            else:
                return False

            review.external_review_date = datetime.now()
            await self.db.commit()

            logger.info(f"Tracked {platform} review for review {review_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Error tracking external review: {e}")
            return False

    async def issue_coupon_after_ai_interaction(
        self, review_id: UUID, ai_interaction_notes: str, discount_percentage: int = 10
    ) -> DiscountCoupon | None:
        """
        Issue coupon after AI has interacted with customer.
        Called by AI service after conversation determines coupon is warranted.
        """
        try:
            review = await self.db.get(CustomerReview, review_id)
            if not review:
                logger.error(f"Review {review_id} not found")
                return None

            # Issue coupon
            coupon = await self._issue_coupon(
                customer_id=review.customer_id,
                station_id=review.station_id,
                review_id=review.id,
                reason="ai_resolved_complaint",
                discount_percentage=discount_percentage,
            )

            if coupon:
                review.coupon_issued = True
                review.coupon_id = coupon.id

                # Add metadata about AI interaction
                if not review.metadata:
                    review.metadata = {}
                review.metadata["ai_interaction_notes"] = ai_interaction_notes
                review.metadata["coupon_issued_at"] = datetime.now().isoformat()

                await self.db.commit()
                logger.info(f"AI issued coupon {coupon.coupon_code} for review {review_id}")
                return coupon

            return None

        except Exception as e:
            logger.exception(f"Error issuing coupon after AI interaction: {e}")
            await self.db.rollback()
            return None

    async def escalate_to_human(
        self, review_id: UUID, ai_notes: str, priority: str = "urgent"
    ) -> bool:
        """
        Escalate unresolved complaint to human admin.
        Called when AI cannot resolve the issue.
        """
        try:
            review = await self.db.get(CustomerReview, review_id)
            if not review:
                return False

            # Create human escalation
            escalation = ReviewEscalation(
                review_id=review.id,
                escalation_type="admin_notification",
                priority=priority,
                escalation_reason=f"AI unable to resolve: {ai_notes[:200]}",
                status="open",
            )

            self.db.add(escalation)
            review.status = "escalated"
            review.admin_notified_at = datetime.now()

            # Add to metadata
            if not review.metadata:
                review.metadata = {}
            review.metadata["escalated_to_human"] = True
            review.metadata["escalation_reason"] = ai_notes
            review.metadata["escalated_at"] = datetime.now().isoformat()

            await self.db.commit()

            # TODO: Send urgent notification to admin dashboard
            # TODO: Send email/SMS to admin team

            logger.info(f"Escalated review {review_id} to human admin with priority {priority}")
            return True

        except Exception as e:
            logger.exception(f"Error escalating to human: {e}")
            await self.db.rollback()
            return False

    async def _issue_coupon(
        self,
        customer_id: UUID,
        station_id: UUID,
        review_id: UUID,
        reason: str,
        discount_percentage: int = 10,
        validity_days: int = 90,
    ) -> DiscountCoupon | None:
        """Issue discount coupon for customer."""
        try:
            # Generate unique coupon code
            coupon_code = DiscountCoupon.generate_coupon_code()

            # Create coupon
            coupon = DiscountCoupon(
                station_id=station_id,
                customer_id=customer_id,
                review_id=review_id,
                coupon_code=coupon_code,
                discount_type="percentage",
                discount_value=discount_percentage,
                description=f"Thank you for your feedback! {discount_percentage}% off your next booking.",
                minimum_order_cents=5000,  # $50 minimum
                max_uses=1,
                issue_reason=reason,
                valid_from=datetime.now(),
                valid_until=datetime.now() + timedelta(days=validity_days),
                status="active",
            )

            self.db.add(coupon)
            await self.db.flush()

            logger.info(f"Issued coupon {coupon_code} for customer {customer_id}")
            return coupon

        except Exception as e:
            logger.exception(f"Error issuing coupon: {e}")
            return None

    async def get_review_by_id(self, review_id: UUID) -> CustomerReview | None:
        """Get review by ID with related data."""
        result = await self.db.execute(
            select(CustomerReview)
            .where(CustomerReview.id == review_id)
            .options(
                selectinload(CustomerReview.customer),
                selectinload(CustomerReview.booking),
                selectinload(CustomerReview.coupon),
            )
        )
        return result.scalar_one_or_none()

    async def get_customer_reviews(
        self, customer_id: UUID, station_id: UUID | None = None
    ) -> list[CustomerReview]:
        """Get all reviews for a customer."""
        query = select(CustomerReview).where(CustomerReview.customer_id == customer_id)

        if station_id:
            query = query.where(CustomerReview.station_id == station_id)

        query = query.order_by(CustomerReview.created_at.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_pending_review_requests(
        self, station_id: UUID, hours_old: int = 24
    ) -> list[CustomerReview]:
        """Get pending review requests older than specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours_old)

        result = await self.db.execute(
            select(CustomerReview)
            .where(
                and_(
                    CustomerReview.station_id == station_id,
                    CustomerReview.status == "pending",
                    CustomerReview.created_at <= cutoff_time,
                )
            )
            .options(selectinload(CustomerReview.customer), selectinload(CustomerReview.booking))
        )
        return result.scalars().all()

    async def get_escalated_reviews(
        self, station_id: UUID, status: str = "escalated"
    ) -> list[CustomerReview]:
        """Get escalated reviews for admin."""
        result = await self.db.execute(
            select(CustomerReview)
            .where(and_(CustomerReview.station_id == station_id, CustomerReview.status == status))
            .options(
                selectinload(CustomerReview.customer),
                selectinload(CustomerReview.booking),
                selectinload(CustomerReview.escalations),
            )
            .order_by(CustomerReview.created_at.desc())
        )
        return result.scalars().all()

    async def resolve_review(
        self, review_id: UUID, resolved_by: UUID, resolution_notes: str
    ) -> bool:
        """Resolve an escalated review."""
        try:
            review = await self.db.get(CustomerReview, review_id)
            if not review:
                return False

            review.status = "resolved"
            review.resolved_at = datetime.now()
            review.resolved_by = resolved_by
            review.resolution_notes = resolution_notes

            # Close all open escalations
            for escalation in review.escalations:
                if escalation.is_open:
                    escalation.status = "resolved"
                    escalation.resolved_at = datetime.now()

            await self.db.commit()
            logger.info(f"Resolved review {review_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Error resolving review: {e}")
            return False

    async def get_customer_coupons(
        self, customer_id: UUID, station_id: UUID | None = None, active_only: bool = True
    ) -> list[DiscountCoupon]:
        """Get customer's discount coupons."""
        query = select(DiscountCoupon).where(DiscountCoupon.customer_id == customer_id)

        if station_id:
            query = query.where(DiscountCoupon.station_id == station_id)

        if active_only:
            query = query.where(
                and_(
                    DiscountCoupon.status == "active", DiscountCoupon.valid_until >= datetime.now()
                )
            )

        query = query.order_by(DiscountCoupon.created_at.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    async def validate_coupon(
        self, coupon_code: str, customer_id: UUID, order_total_cents: int
    ) -> dict[str, Any]:
        """Validate if coupon can be used."""
        result = await self.db.execute(
            select(DiscountCoupon).where(DiscountCoupon.coupon_code == coupon_code)
        )
        coupon = result.scalar_one_or_none()

        if not coupon:
            return {"valid": False, "error": "Coupon not found"}

        if coupon.customer_id != customer_id:
            return {"valid": False, "error": "Coupon not valid for this customer"}

        if not coupon.is_valid:
            return {"valid": False, "error": "Coupon is not valid or expired"}

        if order_total_cents < coupon.minimum_order_cents:
            min_order = coupon.minimum_order_cents / 100
            return {"valid": False, "error": f"Minimum order ${min_order:.2f} required"}

        # Calculate discount
        if coupon.discount_type == "percentage":
            discount_cents = int(order_total_cents * coupon.discount_value / 100)
        else:  # fixed_amount
            discount_cents = coupon.discount_value

        return {
            "valid": True,
            "coupon": {
                "id": str(coupon.id),
                "code": coupon.coupon_code,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "discount_display": coupon.discount_display,
                "discount_cents": discount_cents,
                "description": coupon.description,
                "valid_until": coupon.valid_until.isoformat(),
            },
        }

    async def apply_coupon(self, coupon_code: str, booking_id: UUID) -> bool:
        """Apply coupon to booking."""
        try:
            result = await self.db.execute(
                select(DiscountCoupon).where(DiscountCoupon.coupon_code == coupon_code)
            )
            coupon = result.scalar_one_or_none()

            if not coupon or not coupon.is_valid:
                return False

            coupon.mark_used(str(booking_id))
            await self.db.commit()

            logger.info(f"Applied coupon {coupon_code} to booking {booking_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Error applying coupon: {e}")
            return False


__all__ = ["ReviewService"]
