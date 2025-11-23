"""
Background worker for sending automated review requests.
Runs daily to send review SMS 1 day after booking completion.
"""

import asyncio
from datetime import datetime, timedelta
import logging

from core.database import AsyncSessionLocal
from models import Booking, Customer, CustomerReview
from core.config import get_settings
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()

logger = logging.getLogger(__name__)


class ReviewRequestWorker:
    """Worker for sending automated review requests."""

    def __init__(self):
        self.base_url = settings.customer_app_url or "https://myhibachi.com"
        
        # Lazy-loaded services
        self._review_service = None
    
    @property
    def review_service(self):
        """Lazy load review service (Google APIs)"""
        if self._review_service is None:
            logger.info("Loading review service...")
            from services.review_service import ReviewService
            self._review_service = ReviewService()
        return self._review_service

    async def process_completed_bookings(self) -> int:
        """
        Find bookings completed 24 hours ago and send review requests.
        Returns number of review requests sent.
        """
        async with AsyncSessionLocal() as db:
            try:
                # Calculate time window (24 hours ago, with 1-hour tolerance)
                now = datetime.now()
                target_time_start = now - timedelta(hours=25)  # 25 hours ago
                target_time_end = now - timedelta(hours=23)  # 23 hours ago

                logger.info(
                    f"Checking for bookings completed between {target_time_start} and {target_time_end}"
                )

                # Find completed bookings without reviews
                query = (
                    select(Booking)
                    .where(
                        and_(
                            Booking.status == "completed",
                            Booking.date.between(target_time_start, target_time_end),
                        )
                    )
                    .outerjoin(CustomerReview, CustomerReview.booking_id == Booking.id)
                    .where(CustomerReview.id.is_(None))  # No review exists
                )

                result = await db.execute(query)
                bookings = result.scalars().all()

                logger.info(f"Found {len(bookings)} bookings eligible for review requests")

                sent_count = 0
                for booking in bookings:
                    success = await self._send_review_request(db, booking)
                    if success:
                        sent_count += 1

                logger.info(f"Sent {sent_count} review requests successfully")
                return sent_count

            except Exception as e:
                logger.error(f"Error processing completed bookings: {e}", exc_info=True)
                return 0

    async def _send_review_request(self, db: AsyncSession, booking: Booking) -> bool:
        """Send review request for a single booking."""
        try:
            # Get customer details
            customer_result = await db.execute(
                select(Customer).where(Customer.id == booking.customer_id)
            )
            customer = customer_result.scalar_one_or_none()

            if not customer:
                logger.warning(f"Customer not found for booking {booking.id}")
                return False

            # Decrypt customer data (assuming you have encryption)
            from utils.encryption import (
                decrypt_field,
                get_field_encryption,
            )

            field_encryption = get_field_encryption()

            try:
                customer_phone = decrypt_field(customer.phone_encrypted, field_encryption.key)
                customer_name = decrypt_field(customer.name_encrypted, field_encryption.key)
            except Exception as e:
                logger.exception(f"Error decrypting customer data: {e}")
                return False

            # Create review service (lazy loaded)
            from services.review_service import ReviewService
            review_service = ReviewService(db)

            # Create review record
            review = await review_service.create_review_request(
                booking_id=booking.id, customer_id=customer.id, station_id=booking.station_id
            )

            if not review:
                logger.warning(f"Failed to create review for booking {booking.id}")
                return False

            # Send SMS
            success = await review_service.send_review_sms(
                review_id=review.id,
                customer_phone=customer_phone,
                customer_name=customer_name.split()[0],  # First name only
                base_url=self.base_url,
            )

            if success:
                logger.info(f"Successfully sent review request for booking {booking.id}")
                return True
            else:
                logger.error(f"Failed to send SMS for booking {booking.id}")
                return False

        except Exception as e:
            logger.error(
                f"Error sending review request for booking {booking.id}: {e}", exc_info=True
            )
            return False

    async def send_review_reminders(self) -> int:
        """
        Send reminders for pending reviews (3 days after initial request).
        Returns number of reminders sent.
        """
        async with AsyncSessionLocal() as db:
            try:
                # Find pending reviews 3 days old
                reminder_time = datetime.now() - timedelta(days=3)

                query = select(CustomerReview).where(
                    and_(
                        CustomerReview.status == "pending",
                        CustomerReview.sms_sent_at.isnot(None),
                        CustomerReview.sms_sent_at <= reminder_time,
                    )
                )

                result = await db.execute(query)
                reviews = result.scalars().all()

                logger.info(f"Found {len(reviews)} reviews needing reminders")

                sent_count = 0
                for review in reviews:
                    success = await self._send_review_reminder(db, review)
                    if success:
                        sent_count += 1

                logger.info(f"Sent {sent_count} review reminders")
                return sent_count

            except Exception as e:
                logger.error(f"Error sending review reminders: {e}", exc_info=True)
                return 0

    async def _send_review_reminder(self, db: AsyncSession, review: CustomerReview) -> bool:
        """Send reminder SMS for pending review."""
        try:
            # Get customer details
            customer_result = await db.execute(
                select(Customer).where(Customer.id == review.customer_id)
            )
            customer = customer_result.scalar_one_or_none()

            if not customer:
                return False

            # Decrypt customer data
            from utils.encryption import (
                decrypt_field,
                get_field_encryption,
            )

            field_encryption = get_field_encryption()

            customer_phone = decrypt_field(customer.phone_encrypted, field_encryption.key)
            customer_name = decrypt_field(customer.name_encrypted, field_encryption.key)

            # Send reminder SMS
            from services.ringcentral_sms import ringcentral_sms

            message = (
                f"Hi {customer_name.split()[0]}! 👋\n\n"
                f"We'd still love to hear about your hibachi experience!\n\n"
                f"Share your feedback: {review.review_link}\n\n"
                f"Thank you! 🍱"
            )

            async with ringcentral_sms as sms_service:
                response = await sms_service.send_sms(to_number=customer_phone, message=message)

            if response.success:
                # Update metadata to track reminder sent
                if not review.metadata:
                    review.metadata = {}
                review.metadata["reminder_sent_at"] = datetime.now().isoformat()
                await db.commit()

                logger.info(f"Sent reminder for review {review.id}")
                return True

            return False

        except Exception as e:
            logger.exception(f"Error sending reminder for review {review.id}: {e}")
            return False

    async def cleanup_expired_coupons(self) -> int:
        """Mark expired coupons as expired. Returns number of coupons updated."""
        async with AsyncSessionLocal() as db:
            try:
                from models import DiscountCoupon
                
                # Find active coupons past expiration
                query = select(DiscountCoupon).where(
                    and_(
                        DiscountCoupon.status == "active",
                        DiscountCoupon.valid_until < datetime.now(),
                    )
                )

                result = await db.execute(query)
                expired_coupons = result.scalars().all()

                for coupon in expired_coupons:
                    coupon.status = "expired"

                await db.commit()

                logger.info(f"Marked {len(expired_coupons)} coupons as expired")
                return len(expired_coupons)

            except Exception as e:
                logger.exception(f"Error cleaning up expired coupons: {e}")
                await db.rollback()
                return 0


async def run_review_worker():
    """Main worker function - run this as a scheduled job."""
    logger.info("Starting review request worker")

    worker = ReviewRequestWorker()

    # Send new review requests
    sent_count = await worker.process_completed_bookings()
    logger.info(f"Review requests sent: {sent_count}")

    # Send reminders (optional - could be run separately)
    reminder_count = await worker.send_review_reminders()
    logger.info(f"Review reminders sent: {reminder_count}")

    # Cleanup expired coupons
    expired_count = await worker.cleanup_expired_coupons()
    logger.info(f"Expired coupons cleaned up: {expired_count}")

    logger.info("Review request worker completed")


# For running as standalone script
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    asyncio.run(run_review_worker())


__all__ = ["ReviewRequestWorker", "run_review_worker"]
