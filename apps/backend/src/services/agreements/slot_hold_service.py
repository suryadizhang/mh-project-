"""
Slot Hold Service
=================

Manages temporary slot holds during the signing process.
Prevents double-booking while customer is reviewing/signing agreement.

Flow:
1. Customer starts booking → create_hold() reserves the slot for 2 hours
2. Customer has 2 hours to sign agreement and pay deposit
3. If signed in time → convert_to_booking() releases hold
4. If timeout → expire_hold() makes slot available again

Important:
- Hold tokens are unique per slot hold for SMS signing links
- Expired holds are automatically cleaned up by cron job
- Multiple holds for same slot are prevented

Usage:
    service = SlotHoldService(db)

    # Create hold when booking starts
    hold = await service.create_hold(
        station_id=station_id,
        slot_datetime=slot_datetime,
        customer_email="customer@example.com",
        hold_minutes=120
    )

    # Verify hold is valid
    is_valid = await service.validate_hold(hold.signing_token)

    # Convert to booking when signed
    await service.release_hold(hold.id, reason='converted_to_booking')

    # Cleanup expired holds (call from cron)
    count = await service.cleanup_expired_holds()

See: database/migrations/008_legal_agreements_system.sql
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Default hold duration
DEFAULT_HOLD_MINUTES = 120  # 2 hours


class SlotHoldService:
    """
    Service for managing temporary slot holds during signing process.

    Prevents double-booking while customer reviews and signs agreement.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize slot hold service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_hold(
        self,
        station_id: UUID,
        slot_datetime: datetime,
        customer_email: str,
        customer_id: UUID | None = None,
        hold_minutes: int = DEFAULT_HOLD_MINUTES,
    ) -> dict[str, Any]:
        """
        Create a temporary hold on a time slot.

        Args:
            station_id: Station for the booking
            slot_datetime: Date/time of the slot
            customer_email: Customer's email for identification
            customer_id: Customer ID if logged in (optional)
            hold_minutes: How long to hold the slot (default 2 hours)

        Returns:
            Hold dict with id, signing_token, expires_at

        Raises:
            ValueError: If slot is already held or booked
        """
        # Generate secure token for SMS signing link
        signing_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=hold_minutes)

        # Check if slot is already held or booked
        if await self._is_slot_held_or_booked(station_id, slot_datetime):
            raise ValueError("This time slot is no longer available")

        result = await self.db.execute(
            text(
                """
                INSERT INTO core.slot_holds (
                    station_id, slot_datetime, customer_email, customer_id,
                    signing_token, status, expires_at
                ) VALUES (
                    :station_id, :slot_datetime, :customer_email, :customer_id,
                    :signing_token, 'pending', :expires_at
                )
                RETURNING id, signing_token, expires_at, created_at
            """
            ),
            {
                "station_id": str(station_id),
                "slot_datetime": slot_datetime,
                "customer_email": customer_email,
                "customer_id": str(customer_id) if customer_id else None,
                "signing_token": signing_token,
                "expires_at": expires_at,
            },
        )

        row = result.fetchone()
        await self.db.commit()

        logger.info(
            f"Created slot hold: station={station_id}, "
            f"slot={slot_datetime}, expires={expires_at}"
        )

        return {
            "id": row.id,
            "signing_token": row.signing_token,
            "expires_at": row.expires_at,
            "created_at": row.created_at,
            "station_id": station_id,
            "slot_datetime": slot_datetime,
        }

    async def _is_slot_held_or_booked(self, station_id: UUID, slot_datetime: datetime) -> bool:
        """
        Check if a slot is already held or has a confirmed booking.

        Args:
            station_id: Station ID
            slot_datetime: Slot date/time

        Returns:
            True if slot is unavailable
        """
        # Check for active holds
        result = await self.db.execute(
            text(
                """
                SELECT 1 FROM core.slot_holds
                WHERE station_id = :station_id
                AND slot_datetime = :slot_datetime
                AND status = 'pending'
                AND expires_at > NOW()
                LIMIT 1
            """
            ),
            {"station_id": str(station_id), "slot_datetime": slot_datetime},
        )

        if result.fetchone():
            return True

        # Check for confirmed bookings
        result = await self.db.execute(
            text(
                """
                SELECT 1 FROM core.bookings
                WHERE station_id = :station_id
                AND event_datetime = :slot_datetime
                AND status NOT IN ('cancelled', 'refunded')
                LIMIT 1
            """
            ),
            {"station_id": str(station_id), "slot_datetime": slot_datetime},
        )

        return result.fetchone() is not None

    async def validate_hold(self, signing_token: str) -> dict[str, Any] | None:
        """
        Validate a slot hold by its signing token.

        Used when customer clicks SMS signing link.

        Args:
            signing_token: Token from create_hold()

        Returns:
            Hold dict if valid and not expired, None otherwise
        """
        result = await self.db.execute(
            text(
                """
                SELECT id, station_id, slot_datetime, customer_email, customer_id,
                       status, expires_at, created_at
                FROM core.slot_holds
                WHERE signing_token = :signing_token
                AND status = 'pending'
                AND expires_at > NOW()
            """
            ),
            {"signing_token": signing_token},
        )

        row = result.fetchone()
        if not row:
            return None

        return {
            "id": row.id,
            "station_id": row.station_id,
            "slot_datetime": row.slot_datetime,
            "customer_email": row.customer_email,
            "customer_id": row.customer_id,
            "status": row.status,
            "expires_at": row.expires_at,
            "created_at": row.created_at,
        }

    async def get_hold_by_id(self, hold_id: UUID) -> dict[str, Any] | None:
        """
        Get a slot hold by ID.

        Args:
            hold_id: Hold ID

        Returns:
            Hold dict or None
        """
        result = await self.db.execute(
            text(
                """
                SELECT id, station_id, slot_datetime, customer_email, customer_id,
                       signing_token, status, expires_at, created_at, booking_id
                FROM core.slot_holds
                WHERE id = :hold_id
            """
            ),
            {"hold_id": str(hold_id)},
        )

        row = result.fetchone()
        if not row:
            return None

        return {
            "id": row.id,
            "station_id": row.station_id,
            "slot_datetime": row.slot_datetime,
            "customer_email": row.customer_email,
            "customer_id": row.customer_id,
            "signing_token": row.signing_token,
            "status": row.status,
            "expires_at": row.expires_at,
            "created_at": row.created_at,
            "booking_id": row.booking_id,
        }

    async def convert_to_booking(self, hold_id: UUID, booking_id: UUID) -> bool:
        """
        Convert a hold to a confirmed booking.

        Called after agreement is signed and deposit is paid.

        Args:
            hold_id: The slot hold ID
            booking_id: The newly created booking ID

        Returns:
            True if converted, False if hold not found or expired
        """
        result = await self.db.execute(
            text(
                """
                UPDATE core.slot_holds
                SET status = 'converted',
                    booking_id = :booking_id
                WHERE id = :hold_id
                AND status = 'pending'
                AND expires_at > NOW()
                RETURNING id
            """
            ),
            {"hold_id": str(hold_id), "booking_id": str(booking_id)},
        )

        row = result.fetchone()
        await self.db.commit()

        if row:
            logger.info(f"Converted slot hold {hold_id} to booking {booking_id}")
            return True

        logger.warning(f"Failed to convert slot hold {hold_id} - not found or expired")
        return False

    async def release_hold(self, hold_id: UUID, reason: str = "released") -> bool:
        """
        Release a slot hold without converting to booking.

        Args:
            hold_id: The slot hold ID
            reason: Why the hold was released ('released', 'cancelled', 'expired')

        Returns:
            True if released, False if not found
        """
        result = await self.db.execute(
            text(
                """
                UPDATE core.slot_holds
                SET status = :reason
                WHERE id = :hold_id
                AND status = 'pending'
                RETURNING id
            """
            ),
            {"hold_id": str(hold_id), "reason": reason},
        )

        row = result.fetchone()
        await self.db.commit()

        if row:
            logger.info(f"Released slot hold {hold_id}: {reason}")
            return True

        return False

    async def cleanup_expired_holds(self) -> int:
        """
        Mark all expired holds as 'expired'.

        Should be called periodically by a cron job.

        Returns:
            Number of holds marked as expired
        """
        result = await self.db.execute(
            text(
                """
                UPDATE core.slot_holds
                SET status = 'expired'
                WHERE status = 'pending'
                AND expires_at <= NOW()
                RETURNING id
            """
            )
        )

        rows = result.fetchall()
        await self.db.commit()

        count = len(rows)
        if count > 0:
            logger.info(f"Cleaned up {count} expired slot holds")

        return count

    async def get_active_holds_for_slot(
        self, station_id: UUID, slot_datetime: datetime
    ) -> list[dict[str, Any]]:
        """
        Get all active holds for a specific slot.

        Used to check slot availability including holds.

        Args:
            station_id: Station ID
            slot_datetime: Slot date/time

        Returns:
            List of active holds
        """
        result = await self.db.execute(
            text(
                """
                SELECT id, customer_email, expires_at, created_at
                FROM core.slot_holds
                WHERE station_id = :station_id
                AND slot_datetime = :slot_datetime
                AND status = 'pending'
                AND expires_at > NOW()
                ORDER BY created_at
            """
            ),
            {"station_id": str(station_id), "slot_datetime": slot_datetime},
        )

        return [
            {
                "id": row.id,
                "customer_email": row.customer_email,
                "expires_at": row.expires_at,
                "created_at": row.created_at,
            }
            for row in result.fetchall()
        ]

    async def extend_hold(self, hold_id: UUID, additional_minutes: int = 30) -> datetime | None:
        """
        Extend a hold's expiration time.

        Maximum extension is 30 minutes, and can only be done once.

        Args:
            hold_id: The slot hold ID
            additional_minutes: Minutes to add (max 30)

        Returns:
            New expiration time, or None if extension failed
        """
        # Cap at 30 minutes
        additional_minutes = min(additional_minutes, 30)

        result = await self.db.execute(
            text(
                """
                UPDATE core.slot_holds
                SET expires_at = expires_at + :interval
                WHERE id = :hold_id
                AND status = 'pending'
                AND expires_at > NOW()
                AND expires_at < created_at + INTERVAL '150 minutes'
                RETURNING expires_at
            """
            ),
            {
                "hold_id": str(hold_id),
                "interval": timedelta(minutes=additional_minutes),
            },
        )

        row = result.fetchone()
        await self.db.commit()

        if row:
            logger.info(f"Extended slot hold {hold_id} by {additional_minutes} minutes")
            return row.expires_at

        logger.warning(f"Failed to extend slot hold {hold_id}")
        return None

    async def record_signing_link_sent(self, hold_id: UUID, channel: str) -> dict[str, Any] | None:
        """
        Record that a signing link was sent for this hold.

        Uses the database function core.record_signing_link_sent() which:
        - Increments send count
        - Tracks first send and last resend times
        - Adds channel to the channels array
        - Rate limits to 5 sends total

        Args:
            hold_id: The slot hold ID
            channel: Channel used ('sms' or 'email')

        Returns:
            Dict with send_count, first_sent_at, last_sent_at, or None if failed

        Raises:
            ValueError: If rate limit exceeded (5 sends)
        """
        try:
            result = await self.db.execute(
                text(
                    """
                    SELECT * FROM core.record_signing_link_sent(
                        :hold_id::uuid,
                        :channel
                    )
                """
                ),
                {"hold_id": str(hold_id), "channel": channel},
            )

            row = result.fetchone()
            await self.db.commit()

            if row:
                logger.info(
                    f"Recorded signing link sent for hold {hold_id} "
                    f"via {channel} (count: {row.send_count})"
                )
                return {
                    "send_count": row.send_count,
                    "first_sent_at": row.first_sent_at,
                    "last_sent_at": row.last_sent_at,
                }

            return None

        except Exception as e:
            await self.db.rollback()
            error_msg = str(e)
            if "Rate limit exceeded" in error_msg:
                logger.warning(f"Rate limit exceeded for signing link on hold {hold_id}")
                raise ValueError("Signing link rate limit exceeded (max 5 sends)")
            logger.exception(f"Failed to record signing link sent: {e}")
            raise

    async def get_signing_link_status(self, hold_id: UUID) -> dict[str, Any] | None:
        """
        Get the signing link status for a hold.

        Uses the view core.slot_holds_with_link_status for computed fields.

        Args:
            hold_id: The slot hold ID

        Returns:
            Dict with link status info, or None if hold not found
        """
        result = await self.db.execute(
            text(
                """
                SELECT
                    id,
                    signing_token,
                    signing_link_sent_at,
                    signing_link_resent_at,
                    signing_link_send_count,
                    signing_link_channels,
                    link_status,
                    link_rate_limited,
                    seconds_since_last_send
                FROM core.slot_holds_with_link_status
                WHERE id = :hold_id
            """
            ),
            {"hold_id": str(hold_id)},
        )

        row = result.fetchone()
        if row:
            return {
                "id": row.id,
                "signing_token": row.signing_token,
                "sent_at": row.signing_link_sent_at,
                "resent_at": row.signing_link_resent_at,
                "send_count": row.signing_link_send_count,
                "channels": row.signing_link_channels or [],
                "status": row.link_status,
                "rate_limited": row.link_rate_limited,
                "seconds_since_last_send": row.seconds_since_last_send,
            }

        return None


# Convenience function for dependency injection
def get_slot_hold_service(db: AsyncSession) -> SlotHoldService:
    """FastAPI dependency injection helper."""
    return SlotHoldService(db)
