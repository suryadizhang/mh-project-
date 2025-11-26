"""
Coupon Reminder Scheduler - Automated SMS reminders via RingCentral

This scheduler runs daily to send milestone-based coupon reminders.

Schedule:
- Day 0: Welcome SMS (handled by coupon issuance)
- Day 30: Helpful ideas SMS
- Day 90: Mid-point reminder (3 months left)
- Day 120: 2-month warning
- Day 150: 1-month warning
- Day 166: FINAL reminder (2 weeks before expiry - customer needs planning time!)
- Holiday triggers: Thanksgiving, Christmas, New Year
"""

import asyncio
from datetime import datetime, timedelta, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from services.coupon_reminder_service import CouponReminderService, HOLIDAY_MESSAGES
from services.holiday_service import get_holiday_service, HolidayCategory

logger = logging.getLogger(__name__)


async def send_daily_reminders():
    """
    Main scheduler function - runs daily to send all applicable reminders.
    
    Should be called by:
    - Cron job (production)
    - Task scheduler (Windows)
    - Celery/RQ (queue system)
    """
    logger.info("=" * 60)
    logger.info(f"Starting daily coupon reminder job at {datetime.now(timezone.utc)}")
    logger.info("=" * 60)
    
    async for db in get_db():
        try:
            reminder_service = CouponReminderService(db)
            
            # Track statistics
            stats = {
                "helpful_ideas": 0,
                "midpoint": 0,
                "two_month_warning": 0,
                "one_month_warning": 0,
                "final_warning": 0,
                "holiday_reminders": 0,
                "errors": 0,
            }
            
            # ===== HELPFUL IDEAS (Day 30) =====
            logger.info("\n--- Checking Day 30 Helpful Ideas reminders ---")
            helpful_ideas_coupons = await reminder_service.get_coupons_for_reminder("helpful_ideas")
            
            for coupon_data in helpful_ideas_coupons:
                # TODO: Get customer details from database
                # For now, assume we have customer data in coupon metadata
                customer_phone = coupon_data["metadata"].get("customer_phone")
                customer_name = coupon_data["metadata"].get("customer_name", "there")
                
                if customer_phone:
                    success = await reminder_service.send_helpful_ideas_sms(
                        coupon_code=coupon_data["coupon_code"],
                        customer_phone=customer_phone,
                        customer_name=customer_name,
                    )
                    
                    if success:
                        await reminder_service.mark_reminder_sent(
                            coupon_data["coupon_id"],
                            "helpful_ideas"
                        )
                        stats["helpful_ideas"] += 1
                    else:
                        stats["errors"] += 1
                
                # Rate limiting: wait between messages
                await asyncio.sleep(2)
            
            # ===== MID-POINT REMINDER (Day 90) =====
            logger.info("\n--- Checking Day 90 Mid-point reminders ---")
            midpoint_coupons = await reminder_service.get_coupons_for_reminder("midpoint")
            
            for coupon_data in midpoint_coupons:
                customer_phone = coupon_data["metadata"].get("customer_phone")
                customer_name = coupon_data["metadata"].get("customer_name", "there")
                
                if customer_phone:
                    success = await reminder_service.send_midpoint_reminder_sms(
                        coupon_code=coupon_data["coupon_code"],
                        customer_phone=customer_phone,
                        customer_name=customer_name,
                        days_remaining=coupon_data["days_until_expiry"],
                    )
                    
                    if success:
                        await reminder_service.mark_reminder_sent(
                            coupon_data["coupon_id"],
                            "midpoint"
                        )
                        stats["midpoint"] += 1
                    else:
                        stats["errors"] += 1
                
                await asyncio.sleep(2)
            
            # ===== 2-MONTH WARNING (Day 120) =====
            logger.info("\n--- Checking Day 120 Two-month warning reminders ---")
            two_month_coupons = await reminder_service.get_coupons_for_reminder("two_month_warning")
            
            for coupon_data in two_month_coupons:
                customer_phone = coupon_data["metadata"].get("customer_phone")
                customer_name = coupon_data["metadata"].get("customer_name", "there")
                
                if customer_phone:
                    success = await reminder_service.send_two_month_warning_sms(
                        coupon_code=coupon_data["coupon_code"],
                        customer_phone=customer_phone,
                        customer_name=customer_name,
                        expiration_date=coupon_data["valid_until"],
                    )
                    
                    if success:
                        await reminder_service.mark_reminder_sent(
                            coupon_data["coupon_id"],
                            "two_month_warning"
                        )
                        stats["two_month_warning"] += 1
                    else:
                        stats["errors"] += 1
                
                await asyncio.sleep(2)
            
            # ===== 1-MONTH WARNING (Day 150) =====
            logger.info("\n--- Checking Day 150 One-month warning reminders ---")
            one_month_coupons = await reminder_service.get_coupons_for_reminder("one_month_warning")
            
            for coupon_data in one_month_coupons:
                customer_phone = coupon_data["metadata"].get("customer_phone")
                customer_name = coupon_data["metadata"].get("customer_name", "there")
                
                if customer_phone:
                    success = await reminder_service.send_one_month_warning_sms(
                        coupon_code=coupon_data["coupon_code"],
                        customer_phone=customer_phone,
                        customer_name=customer_name,
                        expiration_date=coupon_data["valid_until"],
                    )
                    
                    if success:
                        await reminder_service.mark_reminder_sent(
                            coupon_data["coupon_id"],
                            "one_month_warning"
                        )
                        stats["one_month_warning"] += 1
                    else:
                        stats["errors"] += 1
                
                await asyncio.sleep(2)
            
            # ===== FINAL WARNING (Day 166 - 2 WEEKS BEFORE EXPIRY) =====
            logger.info("\n--- Checking Day 166 FINAL reminder (2 weeks before expiry) ---")
            final_warning_coupons = await reminder_service.get_coupons_for_reminder("final_warning")
            
            for coupon_data in final_warning_coupons:
                customer_phone = coupon_data["metadata"].get("customer_phone")
                customer_name = coupon_data["metadata"].get("customer_name", "there")
                
                if customer_phone:
                    success = await reminder_service.send_final_reminder_sms(
                        coupon_code=coupon_data["coupon_code"],
                        customer_phone=customer_phone,
                        customer_name=customer_name,
                        expiration_date=coupon_data["valid_until"],
                    )
                    
                    if success:
                        await reminder_service.mark_reminder_sent(
                            coupon_data["coupon_id"],
                            "final_warning"
                        )
                        stats["final_warning"] += 1
                    else:
                        stats["errors"] += 1
                
                await asyncio.sleep(2)
            
            # ===== HOLIDAY REMINDERS (Using Centralized Holiday Service) =====
            logger.info("\n--- Checking holiday-specific reminders ---")
            today = datetime.now(timezone.utc).date()
            
            # Use centralized holiday service for accurate, dynamic holiday detection
            holiday_service = get_holiday_service()
            
            # Get current holiday/season (if any)
            current_holiday = holiday_service.get_current_holiday(today)
            
            if current_holiday:
                holiday_key, holiday_obj, holiday_date = current_holiday
                logger.info(f"Currently in marketing window for: {holiday_obj.name} (Date: {holiday_date})")
                
                # Map our holiday keys to HOLIDAY_MESSAGES keys
                holiday_message_map = {
                    "thanksgiving": "thanksgiving",
                    "christmas": "christmas",
                    "new_years": "newyear",
                    "new_years_eve": "newyear",
                    "mothers_day": "mothers_day",
                    "fathers_day": "fathers_day",
                    "graduation_season": "graduation",
                    "independence_day": "july4th",
                }
                
                # Get message template key
                message_key = holiday_message_map.get(holiday_key)
                
                if message_key and message_key in HOLIDAY_MESSAGES:
                    # Get coupons eligible for this holiday reminder
                    holiday_coupons = await reminder_service.get_holiday_reminders(message_key)
                    logger.info(f"Found {len(holiday_coupons)} coupons eligible for {holiday_obj.name} reminder")
                    
                    for coupon_data in holiday_coupons:
                        customer_phone = coupon_data["metadata"].get("customer_phone")
                        customer_name = coupon_data["metadata"].get("customer_name", "there")
                        
                        if customer_phone:
                            holiday_info = HOLIDAY_MESSAGES[message_key]
                            
                            # Get rich holiday context for personalization
                            context = holiday_service.get_holiday_message_context(holiday_key, today)
                            days_until = context.get("days_until", 0)
                            
                            success = await reminder_service.send_holiday_reminder_sms(
                                coupon_code=coupon_data["coupon_code"],
                                customer_phone=customer_phone,
                                customer_name=customer_name,
                                holiday_name=holiday_info["name"],
                                holiday_context=f"{holiday_info['context']} ({days_until} days until {holiday_obj.name}!)",
                            )
                            
                            if success:
                                await reminder_service.mark_reminder_sent(
                                    coupon_data["coupon_id"],
                                    f"holiday_{holiday_key}"
                                )
                                stats["holiday_reminders"] += 1
                            else:
                                stats["errors"] += 1
                        
                        await asyncio.sleep(2)
                else:
                    logger.info(f"No SMS template configured for {holiday_obj.name} yet")
            else:
                logger.info("No active holiday marketing windows today")
            
            # ===== SUMMARY =====
            logger.info("\n" + "=" * 60)
            logger.info("Daily reminder job completed")
            logger.info(f"Helpful Ideas (Day 30): {stats['helpful_ideas']} sent")
            logger.info(f"Mid-point (Day 90): {stats['midpoint']} sent")
            logger.info(f"2-Month Warning (Day 120): {stats['two_month_warning']} sent")
            logger.info(f"1-Month Warning (Day 150): {stats['one_month_warning']} sent")
            logger.info(f"FINAL Warning (Day 166): {stats['final_warning']} sent")
            logger.info(f"Holiday Reminders: {stats['holiday_reminders']} sent")
            logger.info(f"Errors: {stats['errors']}")
            logger.info(f"Total SMS sent: {sum(stats.values()) - stats['errors']}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.exception(f"Error in daily reminder job: {e}")
        finally:
            await db.close()


if __name__ == "__main__":
    # For testing: run the scheduler once
    asyncio.run(send_daily_reminders())
