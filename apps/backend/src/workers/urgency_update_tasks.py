"""
Urgency Update Worker Tasks
===========================

Daily background jobs for updating booking urgency status.
Runs at midnight (venue timezone) to recalculate days_until_event for all active bookings.

CRITICAL: Uses venue timezone for accurate day calculations.
A booking at 6pm Pacific should show "1 day away" at 11:59pm Pacific,
NOT at 11:59pm UTC.

Schedule:
    - Daily at 00:05 (5 minutes after midnight) - venue timezone
    - Calculates days_until_event for all active bookings
    - Updates is_urgent and booking_window fields
    - Triggers chef assignment alerts for newly urgent bookings

Related Files:
    - services/urgent_booking_service.py - Calculation logic
    - workers/chef_assignment_alert_tasks.py - Alert system (FAILPROOF)
    - database/migrations/021_urgent_booking_system.sql - Schema

SSoT Variables Used:
    - booking.urgent_window_days (default: 7)
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.database import get_async_db, get_sync_db
from services.business_config_service import get_business_config_sync
from services.urgent_booking_service import (
    BookingWindow,
    calculate_days_until_event,
    determine_booking_window,
    is_booking_urgent,
)
from workers.celery_config import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def daily_urgency_update(self) -> Dict[str, Any]:
    """
    Daily task to recalculate urgency for all active bookings.

    Runs at midnight venue timezone (configured in celery beat schedule).
    Updates days_until_event, is_urgent, and booking_window for each booking.

    Returns:
        Dict with counts of updated, urgent, and error bookings
    """
    db: Session = next(get_sync_db())
    config = get_business_config_sync()

    stats = {
        "total_processed": 0,
        "updated": 0,
        "newly_urgent": 0,
        "errors": 0,
        "started_at": datetime.utcnow().isoformat(),
    }

    try:
        # Get all active bookings (CONFIRMED, PENDING, DEPOSIT_PAID)
        # that have event_date >= today
        result = db.execute(
            text(
                """
                SELECT
                    id::text,
                    event_date,
                    event_time,
                    venue_timezone,
                    is_urgent,
                    days_until_event,
                    booking_window,
                    chef_id
                FROM core.bookings
                WHERE status IN ('confirmed', 'pending', 'deposit_paid')
                AND event_date >= CURRENT_DATE
                AND is_deleted = false
                ORDER BY event_date ASC
            """
            )
        )
        bookings = result.fetchall()

        logger.info(
            f"🔄 Daily urgency update starting for {len(bookings)} active bookings"
        )

        newly_urgent_bookings = []

        for booking in bookings:
            stats["total_processed"] += 1

            try:
                booking_id = booking[0]
                event_date = booking[1]
                event_time = booking[2]
                venue_timezone = booking[3] or "America/Los_Angeles"
                was_urgent = booking[4] or False
                old_days = booking[5]
                old_window = booking[6]
                has_chef = booking[7] is not None

                # Calculate new urgency values using venue timezone
                new_days = calculate_days_until_event(
                    event_date=event_date,
                    event_time=event_time,
                    venue_timezone=venue_timezone,
                )

                new_window = determine_booking_window(new_days, config)
                new_is_urgent = is_booking_urgent(new_days, config)

                # Check if anything changed
                if (
                    new_days != old_days
                    or new_window.value != old_window
                    or new_is_urgent != was_urgent
                ):
                    # Update the booking
                    db.execute(
                        text(
                            """
                            UPDATE core.bookings
                            SET
                                days_until_event = :days,
                                booking_window = :window,
                                is_urgent = :urgent,
                                updated_at = NOW()
                            WHERE id = :booking_id::uuid
                        """
                        ),
                        {
                            "days": new_days,
                            "window": new_window.value,
                            "urgent": new_is_urgent,
                            "booking_id": booking_id,
                        },
                    )
                    stats["updated"] += 1

                    # Track newly urgent bookings without chef
                    if new_is_urgent and not was_urgent:
                        stats["newly_urgent"] += 1
                        if not has_chef:
                            newly_urgent_bookings.append(
                                {
                                    "booking_id": booking_id,
                                    "event_date": str(event_date),
                                    "days_until": new_days,
                                }
                            )
                            logger.warning(
                                f"⚠️ Booking {booking_id} became URGENT "
                                f"({new_days} days until event, NO CHEF ASSIGNED)"
                            )

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"❌ Error updating urgency for booking {booking_id}: {e}")

        db.commit()

        stats["completed_at"] = datetime.utcnow().isoformat()

        logger.info(
            f"✅ Daily urgency update complete: "
            f"{stats['updated']}/{stats['total_processed']} updated, "
            f"{stats['newly_urgent']} newly urgent, "
            f"{stats['errors']} errors"
        )

        # Trigger chef assignment alerts for newly urgent bookings without chef
        if newly_urgent_bookings:
            logger.warning(
                f"🚨 {len(newly_urgent_bookings)} bookings became urgent without chef assigned!"
            )
            for booking_info in newly_urgent_bookings:
                # Trigger the FAILPROOF alert system
                trigger_chef_assignment_alert.delay(
                    booking_id=booking_info["booking_id"],
                    trigger_reason="urgency_threshold_crossed",
                    days_until_event=booking_info["days_until"],
                )

        return stats

    except Exception as e:
        logger.error(f"❌ Daily urgency update failed: {e}")
        db.rollback()
        stats["error"] = str(e)
        raise self.retry(exc=e, countdown=300)

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=5, default_retry_delay=60)
def trigger_chef_assignment_alert(
    self,
    booking_id: str,
    trigger_reason: str = "manual",
    days_until_event: int = None,
) -> Dict[str, Any]:
    """
    Trigger a chef assignment alert for a booking.

    This is the entry point for the FAILPROOF alert system.
    Delegates to chef_assignment_alert_tasks.py for the actual alerting.

    Args:
        booking_id: UUID of the booking
        trigger_reason: Why the alert was triggered
            - "urgency_threshold_crossed": Booking became urgent
            - "booking_created_urgent": New booking that's already urgent
            - "reminder": Scheduled reminder alert
            - "manual": Manual trigger by admin
        days_until_event: Days until event (for logging)

    Returns:
        Dict with alert status
    """
    from workers.chef_assignment_alert_tasks import process_chef_assignment_alert

    logger.info(
        f"🔔 Chef assignment alert triggered for booking {booking_id}: "
        f"reason={trigger_reason}, days_until={days_until_event}"
    )

    try:
        # Delegate to the FAILPROOF alert processor
        result = process_chef_assignment_alert.delay(
            booking_id=booking_id,
            trigger_reason=trigger_reason,
        )

        return {
            "status": "triggered",
            "booking_id": booking_id,
            "task_id": str(result.id),
            "trigger_reason": trigger_reason,
        }

    except Exception as e:
        logger.error(f"❌ Failed to trigger chef assignment alert: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def update_single_booking_urgency(self, booking_id: str) -> Dict[str, Any]:
    """
    Update urgency for a single booking (called on booking creation/update).

    Args:
        booking_id: UUID of the booking

    Returns:
        Dict with the booking's new urgency status
    """
    db: Session = next(get_sync_db())
    config = get_business_config_sync()

    try:
        # Get the booking
        result = db.execute(
            text(
                """
                SELECT
                    event_date,
                    event_time,
                    venue_timezone,
                    is_urgent,
                    chef_id
                FROM core.bookings
                WHERE id = :booking_id::uuid
                AND is_deleted = false
            """
            ),
            {"booking_id": booking_id},
        )
        booking = result.fetchone()

        if not booking:
            logger.error(f"Booking {booking_id} not found")
            return {"status": "error", "message": "Booking not found"}

        event_date = booking[0]
        event_time = booking[1]
        venue_timezone = booking[2] or "America/Los_Angeles"
        was_urgent = booking[3] or False
        has_chef = booking[4] is not None

        # Calculate urgency
        days_until = calculate_days_until_event(
            event_date=event_date,
            event_time=event_time,
            venue_timezone=venue_timezone,
        )

        window = determine_booking_window(days_until, config)
        is_urgent = is_booking_urgent(days_until, config)

        # Update the booking
        db.execute(
            text(
                """
                UPDATE core.bookings
                SET
                    days_until_event = :days,
                    booking_window = :window,
                    is_urgent = :urgent,
                    updated_at = NOW()
                WHERE id = :booking_id::uuid
            """
            ),
            {
                "days": days_until,
                "window": window.value,
                "urgent": is_urgent,
                "booking_id": booking_id,
            },
        )
        db.commit()

        logger.info(
            f"📊 Booking {booking_id} urgency updated: "
            f"days_until={days_until}, window={window.value}, is_urgent={is_urgent}"
        )

        # Trigger alert if urgent and no chef
        if is_urgent and not has_chef:
            trigger_reason = (
                "booking_created_urgent" if not was_urgent else "urgency_recalculated"
            )
            trigger_chef_assignment_alert.delay(
                booking_id=booking_id,
                trigger_reason=trigger_reason,
                days_until_event=days_until,
            )

        return {
            "status": "success",
            "booking_id": booking_id,
            "days_until_event": days_until,
            "booking_window": window.value,
            "is_urgent": is_urgent,
            "alert_triggered": is_urgent and not has_chef,
        }

    except Exception as e:
        logger.error(f"❌ Failed to update booking urgency: {e}")
        db.rollback()
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()
