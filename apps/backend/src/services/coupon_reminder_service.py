"""
Coupon Reminder Service - Milestone-Based SMS Reminders via RingCentral

Strategy: Event-focused reminders that feel helpful, not spammy
Duration: 6 months (180 days)
Final Reminder: 2 weeks before expiration (customers need planning time)

SSoT Compliance:
- All pricing values (party minimum, max discount) come from business_config_service
- NEVER hardcode business values in SMS templates
- See: 20-SINGLE_SOURCE_OF_TRUTH.instructions.md
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

# MIGRATED: Imports moved from OLD models to NEW db.models system
# TODO: Manual migration needed for: DiscountCoupon, CustomerReview
# from models import DiscountCoupon, CustomerReview
from services.ringcentral_sms import ringcentral_sms
from services.business_config_service import get_business_config
from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class CouponReminderService:
    """Service for managing milestone-based coupon reminders via SMS."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_welcome_sms(
        self,
        coupon_code: str,
        customer_phone: str,
        customer_name: str,
        discount_percentage: int,
        expiration_date: datetime,
    ) -> bool:
        """
        Day 0: Send welcome SMS immediately after coupon issuance.

        Purpose: Confirm coupon receipt and provide key details.
        """
        try:
            # SSoT: Fetch dynamic pricing values from database
            config = await get_business_config(self.db)
            max_discount = int(config.deposit_amount_cents / 100)
            min_order = int(config.party_minimum_cents / 100)

            expiry_formatted = expiration_date.strftime("%B %d, %Y")

            message = (
                f"Hi {customer_name}! 🎉\n\n"
                f"Thank you for your feedback! We've issued you a special coupon:\n\n"
                f"Code: {coupon_code}\n"
                f"Discount: {discount_percentage}% off (max ${max_discount})\n"
                f"Valid: 6 months (until {expiry_formatted})\n"
                f"Minimum: ${min_order} order\n\n"
                f"Use it for your next hibachi celebration!\n"
                f"Book now: {settings.BOOKING_URL}"
            )

            async with ringcentral_sms as sms_service:
                response = await sms_service.send_sms(to_number=customer_phone, message=message)

            if response.success:
                logger.info(f"Welcome SMS sent for coupon {coupon_code}")
                return True
            else:
                logger.error(
                    f"Failed to send welcome SMS for coupon {coupon_code}: {response.error}"
                )
                return False

        except Exception as e:
            logger.exception(f"Error sending welcome SMS for coupon {coupon_code}: {e}")
            return False

    async def send_helpful_ideas_sms(
        self,
        coupon_code: str,
        customer_phone: str,
        customer_name: str,
    ) -> bool:
        """
        Day 30: Send helpful event ideas (not pushy).

        Purpose: Keep coupon top-of-mind with helpful suggestions.
        """
        try:
            message = (
                f"Hi {customer_name}! 🍱\n\n"
                f"Planning your next celebration? Here are some popular hibachi occasions:\n\n"
                f"🎂 Birthday parties\n"
                f"🎉 Family gatherings\n"
                f"🏢 Corporate team events\n"
                f"🎊 Holiday celebrations\n\n"
                f"Remember: You have a {coupon_code} coupon ready to use!\n"
                f"Book: {settings.BOOKING_URL}"
            )

            async with ringcentral_sms as sms_service:
                response = await sms_service.send_sms(to_number=customer_phone, message=message)

            if response.success:
                logger.info(f"Helpful ideas SMS sent for coupon {coupon_code}")
                return True
            else:
                logger.error(f"Failed to send ideas SMS: {response.error}")
                return False

        except Exception as e:
            logger.exception(f"Error sending ideas SMS: {e}")
            return False

    async def send_midpoint_reminder_sms(
        self,
        coupon_code: str,
        customer_phone: str,
        customer_name: str,
        days_remaining: int,
    ) -> bool:
        """
        Day 90 (3 months): Mid-point check-in.

        Purpose: Gentle reminder that time is passing.
        """
        try:
            message = (
                f"Hi {customer_name}! 👋\n\n"
                f"Just a friendly reminder: Your coupon {coupon_code} has 3 months left!\n\n"
                f"💰 {days_remaining} days to save on your next hibachi event\n"
                f"🎉 Perfect timing for upcoming celebrations\n\n"
                f"Plan ahead: {settings.BOOKING_URL}"
            )

            async with ringcentral_sms as sms_service:
                response = await sms_service.send_sms(to_number=customer_phone, message=message)

            if response.success:
                logger.info(f"Mid-point reminder SMS sent for coupon {coupon_code}")
                return True
            else:
                logger.error(f"Failed to send mid-point SMS: {response.error}")
                return False

        except Exception as e:
            logger.exception(f"Error sending mid-point SMS: {e}")
            return False

    async def send_holiday_reminder_sms(
        self,
        coupon_code: str,
        customer_phone: str,
        customer_name: str,
        holiday_name: str,
        holiday_context: str,
    ) -> bool:
        """
        Holiday triggers: Context-aware reminders for upcoming holidays.

        Purpose: Suggest using coupon for relevant upcoming events.
        """
        try:
            message = (
                f"Hi {customer_name}! 🎊\n\n"
                f"{holiday_context}\n\n"
                f"Don't forget: You have coupon {coupon_code} ready to use!\n"
                f"💰 Save on your {holiday_name} celebration\n\n"
                f"Book your hibachi experience: {settings.BOOKING_URL}"
            )

            async with ringcentral_sms as sms_service:
                response = await sms_service.send_sms(to_number=customer_phone, message=message)

            if response.success:
                logger.info(f"Holiday reminder SMS sent for {holiday_name} - coupon {coupon_code}")
                return True
            else:
                logger.error(f"Failed to send holiday SMS: {response.error}")
                return False

        except Exception as e:
            logger.exception(f"Error sending holiday SMS: {e}")
            return False

    async def send_two_month_warning_sms(
        self,
        coupon_code: str,
        customer_phone: str,
        customer_name: str,
        expiration_date: datetime,
    ) -> bool:
        """
        Day 120 (2 months left): Gentle urgency.

        Purpose: Remind customer to start planning.
        """
        try:
            expiry_formatted = expiration_date.strftime("%B %d")

            message = (
                f"Hi {customer_name}! ⏰\n\n"
                f"Heads up: Your coupon {coupon_code} expires in 2 months ({expiry_formatted}).\n\n"
                f"💡 Start planning your next hibachi event!\n"
                f"📅 Book early for best availability\n\n"
                f"Reserve now: {settings.BOOKING_URL}"
            )

            async with ringcentral_sms as sms_service:
                response = await sms_service.send_sms(to_number=customer_phone, message=message)

            if response.success:
                logger.info(f"2-month warning SMS sent for coupon {coupon_code}")
                return True
            else:
                logger.error(f"Failed to send 2-month warning SMS: {response.error}")
                return False

        except Exception as e:
            logger.exception(f"Error sending 2-month warning SMS: {e}")
            return False

    async def send_one_month_warning_sms(
        self,
        coupon_code: str,
        customer_phone: str,
        customer_name: str,
        expiration_date: datetime,
    ) -> bool:
        """
        Day 150 (1 month left): Increased urgency.

        Purpose: Create action motivation.
        """
        try:
            # SSoT: Fetch dynamic pricing values from database
            config = await get_business_config(self.db)
            max_discount = int(config.deposit_amount_cents / 100)

            expiry_formatted = expiration_date.strftime("%B %d")

            message = (
                f"Hi {customer_name}! ⚠️\n\n"
                f"Your coupon {coupon_code} expires in 1 month ({expiry_formatted})!\n\n"
                f"🎯 Don't miss out on your discount\n"
                f"💰 Save up to ${max_discount} on your next event\n\n"
                f"Book before it expires: {settings.BOOKING_URL}"
            )

            async with ringcentral_sms as sms_service:
                response = await sms_service.send_sms(to_number=customer_phone, message=message)

            if response.success:
                logger.info(f"1-month warning SMS sent for coupon {coupon_code}")
                return True
            else:
                logger.error(f"Failed to send 1-month warning SMS: {response.error}")
                return False

        except Exception as e:
            logger.exception(f"Error sending 1-month warning SMS: {e}")
            return False

    async def send_final_reminder_sms(
        self,
        coupon_code: str,
        customer_phone: str,
        customer_name: str,
        expiration_date: datetime,
    ) -> bool:
        """
        Day 166 (2 weeks left): FINAL reminder - customers need planning time!

        Purpose: Last chance to book and plan event.
        User requirement: "people need to prepare time for the party"
        """
        try:
            # SSoT: Fetch dynamic pricing values from database
            config = await get_business_config(self.db)
            max_discount = int(config.deposit_amount_cents / 100)

            expiry_formatted = expiration_date.strftime("%B %d")

            message = (
                f"🚨 FINAL REMINDER {customer_name}!\n\n"
                f"Your coupon {coupon_code} expires in 2 WEEKS ({expiry_formatted}).\n\n"
                f"⏰ Last chance to use it!\n"
                f"💰 Save up to ${max_discount}\n"
                f"📅 Book NOW to secure your date\n\n"
                f"Don't let it expire: {settings.BOOKING_URL}\n\n"
                f"Need help? Call us: {settings.SUPPORT_PHONE}"
            )

            async with ringcentral_sms as sms_service:
                response = await sms_service.send_sms(to_number=customer_phone, message=message)

            if response.success:
                logger.info(
                    f"FINAL reminder SMS sent for coupon {coupon_code} (2 weeks before expiry)"
                )
                return True
            else:
                logger.error(f"Failed to send final reminder SMS: {response.error}")
                return False

        except Exception as e:
            logger.exception(f"Error sending final reminder SMS: {e}")
            return False

    async def get_coupons_for_reminder(
        self,
        reminder_type: str,
    ) -> list[dict[str, Any]]:
        """
        Get coupons that need a specific reminder sent.

        Reminder Types:
        - welcome: Just issued (Day 0)
        - helpful_ideas: Day 30
        - midpoint: Day 90 (3 months in)
        - two_month_warning: Day 120 (2 months left)
        - one_month_warning: Day 150 (1 month left)
        - final_warning: Day 166 (2 weeks left) - USER REQUIREMENT
        - thanksgiving: 2 weeks before Thanksgiving
        - christmas: Early December
        - newyear: Mid-January
        """
        try:
            now = datetime.now(timezone.utc)

            # Define time windows for each reminder type
            reminder_windows = {
                "welcome": (0, 1),  # Within 24 hours of creation
                "helpful_ideas": (29, 31),  # Around day 30
                "midpoint": (89, 91),  # Around day 90
                "two_month_warning": (119, 121),  # Around day 120
                "one_month_warning": (149, 151),  # Around day 150
                "final_warning": (165, 167),  # Around day 166 (2 weeks before expiry)
            }

            if reminder_type not in reminder_windows:
                logger.error(f"Invalid reminder type: {reminder_type}")
                return []

            min_days, max_days = reminder_windows[reminder_type]
            min_date = now - timedelta(days=max_days)
            max_date = now - timedelta(days=min_days)

            # Query active coupons in the target date range
            result = await self.db.execute(
                select(DiscountCoupon).where(
                    and_(
                        DiscountCoupon.status == "active",
                        DiscountCoupon.times_used == 0,
                        DiscountCoupon.created_at >= min_date,
                        DiscountCoupon.created_at <= max_date,
                        DiscountCoupon.valid_until > now,  # Not expired
                    )
                )
            )

            coupons = result.scalars().all()

            # Format coupon data for reminders
            coupon_data = []
            for coupon in coupons:
                # Check if this reminder was already sent
                metadata = coupon.extra_metadata or {}
                reminders_sent = metadata.get("reminders_sent", [])

                if reminder_type not in reminders_sent:
                    days_since_creation = (now - coupon.created_at).days
                    days_until_expiry = (coupon.valid_until - now).days

                    coupon_data.append(
                        {
                            "coupon_id": coupon.id,
                            "coupon_code": coupon.coupon_code,
                            "customer_id": coupon.customer_id,
                            "discount_percentage": coupon.discount_value,
                            "created_at": coupon.created_at,
                            "valid_until": coupon.valid_until,
                            "days_since_creation": days_since_creation,
                            "days_until_expiry": days_until_expiry,
                            "metadata": metadata,
                        }
                    )

            logger.info(f"Found {len(coupon_data)} coupons for {reminder_type} reminder")
            return coupon_data

        except Exception as e:
            logger.exception(f"Error getting coupons for reminder: {e}")
            return []

    async def mark_reminder_sent(
        self,
        coupon_id: UUID,
        reminder_type: str,
    ) -> bool:
        """
        Mark a reminder as sent in the coupon metadata.

        Prevents duplicate reminders.
        """
        try:
            result = await self.db.execute(
                select(DiscountCoupon).where(DiscountCoupon.id == coupon_id)
            )
            coupon = result.scalar_one_or_none()

            if not coupon:
                logger.error(f"Coupon {coupon_id} not found")
                return False

            # Update metadata
            metadata = coupon.extra_metadata or {}
            reminders_sent = metadata.get("reminders_sent", [])

            if reminder_type not in reminders_sent:
                reminders_sent.append(reminder_type)
                metadata["reminders_sent"] = reminders_sent
                metadata[f"{reminder_type}_sent_at"] = datetime.now(timezone.utc).isoformat()

                coupon.extra_metadata = metadata
                await self.db.commit()

                logger.info(
                    f"Marked {reminder_type} reminder as sent for coupon {coupon.coupon_code}"
                )

            return True

        except Exception as e:
            logger.exception(f"Error marking reminder as sent: {e}")
            await self.db.rollback()
            return False

    async def get_holiday_reminders(
        self,
        holiday_name: str,
    ) -> list[dict[str, Any]]:
        """
        Get active coupons that should receive holiday-specific reminders.

        Holidays:
        - thanksgiving: 2 weeks before Thanksgiving
        - christmas: Early December
        - newyear: Mid-January
        """
        try:
            now = datetime.now(timezone.utc)

            # Query all active coupons
            result = await self.db.execute(
                select(DiscountCoupon).where(
                    and_(
                        DiscountCoupon.status == "active",
                        DiscountCoupon.times_used == 0,
                        DiscountCoupon.valid_until > now,
                    )
                )
            )

            coupons = result.scalars().all()

            # Filter coupons that haven't received this holiday reminder
            coupon_data = []
            for coupon in coupons:
                metadata = coupon.extra_metadata or {}
                reminders_sent = metadata.get("reminders_sent", [])

                holiday_reminder_key = f"holiday_{holiday_name}"
                if holiday_reminder_key not in reminders_sent:
                    days_until_expiry = (coupon.valid_until - now).days

                    coupon_data.append(
                        {
                            "coupon_id": coupon.id,
                            "coupon_code": coupon.coupon_code,
                            "customer_id": coupon.customer_id,
                            "days_until_expiry": days_until_expiry,
                            "metadata": metadata,
                        }
                    )

            logger.info(f"Found {len(coupon_data)} coupons for {holiday_name} holiday reminder")
            return coupon_data

        except Exception as e:
            logger.exception(f"Error getting holiday reminders: {e}")
            return []


# Holiday reminder configurations
HOLIDAY_MESSAGES = {
    # Winter Holidays
    "thanksgiving": {
        "name": "Thanksgiving",
        "context": "Thanksgiving is coming up! 🦃 Planning a family gathering or Friendsgiving?",
    },
    "christmas": {
        "name": "Christmas",
        "context": "The holiday season is here! 🎄 Perfect time for office parties and festive celebrations!",
    },
    "newyear": {
        "name": "New Year",
        "context": "Ring in the New Year! 🎊 Celebrate with friends and family!",
    },
    # Spring Holidays
    "easter": {
        "name": "Easter",
        "context": "Easter is coming! 🐰 Plan your family brunch or spring celebration!",
    },
    "mothers_day": {
        "name": "Mother's Day",
        "context": "Mother's Day is approaching! 💐 Treat Mom to an unforgettable hibachi experience!",
    },
    # Summer Holidays & Seasons
    "fathers_day": {
        "name": "Father's Day",
        "context": "Father's Day is coming! 👔 Give Dad a memorable dining experience!",
    },
    "graduation": {
        "name": "Graduation Season",
        "context": "Graduation season is here! 🎓 Celebrate achievements with family and friends!",
    },
    "july4th": {
        "name": "Independence Day",
        "context": "4th of July is approaching! 🇺🇸 Perfect for patriotic celebrations and BBQ parties!",
    },
    # Fall Holidays
    "halloween": {
        "name": "Halloween",
        "context": "Halloween is coming! 🎃 Plan a fun family gathering or costume party!",
    },
}
