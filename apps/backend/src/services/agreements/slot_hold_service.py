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
- Uses event_date + slot_time (separate columns) NOT slot_datetime

Usage:
    service = SlotHoldService(db)

    # Create hold when booking starts
    hold = await service.create_hold(
        station_id=station_id,
        event_date=date(2025, 1, 30),
        slot_time=time(18, 0),  # 6 PM
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
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Default hold duration
DEFAULT_HOLD_MINUTES = 480  # 8 hours (user confirmed preference)

# Smart expiration settings
EVENING_CUTOFF_HOUR = 22  # 10 PM
EVENING_HOLD_MINUTES = 960  # 16 hours (covers overnight until next business hours)
URGENT_EVENT_DAYS = 6  # Events within this many days get max 8h hold
MAX_HOLD_MINUTES = 480  # 8 hours maximum for urgent events


def calculate_smart_expiration(event_date: date, now: datetime | None = None) -> int:
    """
    Calculate smart hold duration based on booking time and event proximity.

    Logic:
    - If booking is made after 10 PM: 16 hours (covers overnight)
    - If event is within 6 days: max 8 hours
    - Default: 8 hours

    Args:
        event_date: Date of the event
        now: Current datetime (for testing), defaults to UTC now

    Returns:
        Hold duration in minutes
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # Calculate days until event
    today = now.date()
    days_until_event = (event_date - today).days

    # If event is very soon, cap at 8 hours regardless of time
    if days_until_event <= URGENT_EVENT_DAYS:
        return MAX_HOLD_MINUTES

    # If booking after 10 PM, give 16 hours to cover overnight
    if now.hour >= EVENING_CUTOFF_HOUR:
        return EVENING_HOLD_MINUTES

    # Default: 8 hours
    return DEFAULT_HOLD_MINUTES


class SlotHoldError(Exception):
    """Base exception for slot hold operations."""

    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class SlotUnavailableError(SlotHoldError):
    """Raised when slot is already held or booked."""

    def __init__(self, message: str = "This time slot is no longer available"):
        super().__init__(message, "SLOT_UNAVAILABLE")


class DatabaseError(SlotHoldError):
    """Raised when database operation fails."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, "DATABASE_ERROR")


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
        event_date: date,
        slot_time: time,
        customer_email: str,
        customer_name: str | None = None,
        guest_count: int = 10,
        customer_id: UUID | None = None,
        hold_minutes: int = DEFAULT_HOLD_MINUTES,
    ) -> dict[str, Any]:
        """
        Create a temporary hold on a time slot.

        Args:
            station_id: Station for the booking
            event_date: Date of the event
            slot_time: Time slot of the event
            customer_email: Customer's email for identification
            customer_name: Customer's name (optional)
            guest_count: Number of guests (default 10)
            customer_id: Customer ID if logged in (optional)
            hold_minutes: How long to hold the slot (default 2 hours)

        Returns:
            Hold dict with id, signing_token, expires_at

        Raises:
            SlotUnavailableError: If slot is already held or booked
            DatabaseError: If database operation fails
        """
        # Generate UUID for SMS signing link (must be valid UUID for database)
        signing_token = str(uuid4())

        # Use smart expiration if default value, otherwise use specified duration
        if hold_minutes == DEFAULT_HOLD_MINUTES:
            actual_hold_minutes = calculate_smart_expiration(event_date)
            logger.debug(
                f"Smart expiration: {actual_hold_minutes} minutes for event on {event_date}"
            )
        else:
            actual_hold_minutes = hold_minutes

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=actual_hold_minutes)

        try:
            # Check if slot is already held or booked
            if await self._is_slot_held_or_booked(station_id, event_date, slot_time):
                raise SlotUnavailableError("This time slot is no longer available")

            result = await self.db.execute(
                text(
                    """
                    INSERT INTO core.slot_holds (
                        station_id, event_date, slot_time, customer_email, customer_name,
                        guest_count, signing_token, status, expires_at
                    ) VALUES (
                        :station_id, :event_date, :slot_time, :customer_email, :customer_name,
                        :guest_count, :signing_token, 'pending', :expires_at
                    )
                    RETURNING id, signing_token, expires_at, created_at
                """
                ),
                {
                    "station_id": str(station_id),
                    "event_date": event_date,
                    "slot_time": slot_time,
                    "customer_email": customer_email,
                    "customer_name": customer_name,
                    "guest_count": guest_count,
                    "signing_token": signing_token,
                    "expires_at": expires_at,
                },
            )

            row = result.fetchone()
            await self.db.commit()

        except SlotUnavailableError:
            raise  # Re-raise our custom exception
        except DBAPIError as e:
            logger.error(f"Database error creating slot hold: {e}")
            await self.db.rollback()
            raise DatabaseError(f"Failed to create slot hold: {e}")
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error creating slot hold: {e}")
            await self.db.rollback()
            raise DatabaseError(f"Database operation failed: {e}")

        logger.info(
            f"Created slot hold: station={station_id}, "
            f"date={event_date}, time={slot_time}, expires={expires_at}"
        )

        return {
            "id": row.id,
            "signing_token": str(row.signing_token),  # Convert UUID to string
            "expires_at": row.expires_at,
            "created_at": row.created_at,
            "station_id": station_id,
            "event_date": event_date,
            "slot_time": slot_time,
        }

    async def _is_slot_held_or_booked(
        self, station_id: UUID, event_date: date, slot_time: time
    ) -> bool:
        """
        Check if a slot is already held or has a confirmed booking.

        Args:
            station_id: Station ID
            event_date: Event date
            slot_time: Slot time

        Returns:
            True if slot is unavailable
        """
        # Check for active holds
        result = await self.db.execute(
            text(
                """
                SELECT 1 FROM core.slot_holds
                WHERE station_id = :station_id
                AND event_date = :event_date
                AND slot_time = :slot_time
                AND status IN ('pending', 'signed')
                AND expires_at > NOW()
                LIMIT 1
            """
            ),
            {
                "station_id": str(station_id),
                "event_date": event_date,
                "slot_time": slot_time,
            },
        )

        if result.fetchone():
            return True

        # Check for confirmed bookings (bookings use 'date' and 'slot' columns)
        result = await self.db.execute(
            text(
                """
                SELECT 1 FROM core.bookings
                WHERE station_id = :station_id
                AND date = :event_date
                AND slot = :slot_time
                AND status NOT IN ('cancelled')
                AND deleted_at IS NULL
                LIMIT 1
            """
            ),
            {
                "station_id": str(station_id),
                "event_date": event_date,
                "slot_time": slot_time,
            },
        )

        return result.fetchone() is not None

    async def validate_hold(self, signing_token: str) -> dict[str, Any] | None:
        """
        Validate a slot hold by its signing token.

        Used when customer clicks SMS signing link.
        Returns hold info with validation_status to distinguish between:
        - VALID: Active hold that can be signed
        - EXPIRED: Hold has passed expires_at time
        - COMPLETED: Hold was converted to booking (deposit paid)
        - CANCELLED: Hold was manually cancelled
        - NOT_FOUND: Token doesn't exist

        Args:
            signing_token: Token from create_hold()

        Returns:
            Hold dict with validation_status field, or None if token doesn't exist
        """
        # Query hold WITHOUT time/status filters to get full status info
        result = await self.db.execute(
            text(
                """
                SELECT id, station_id, event_date, slot_time, customer_email,
                       customer_name, guest_count, status, expires_at, created_at,
                       agreement_signed_at, deposit_paid_at, converted_to_booking_id
                FROM core.slot_holds
                WHERE signing_token = :signing_token
            """
            ),
            {"signing_token": signing_token},
        )

        row = result.fetchone()
        if not row:
            return None  # Token doesn't exist at all

        # Determine validation status
        now = datetime.now(timezone.utc)
        expires_at = row.expires_at
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if row.status == "converted" or row.converted_to_booking_id:
            validation_status = "COMPLETED"
        elif row.status == "cancelled":
            validation_status = "CANCELLED"
        elif row.status == "expired" or (expires_at and now > expires_at):
            validation_status = "EXPIRED"
        elif row.status in ("pending", "signed"):
            validation_status = "VALID"
        else:
            validation_status = "UNKNOWN"

        return {
            "id": row.id,
            "station_id": row.station_id,
            "event_date": row.event_date,
            "slot_time": row.slot_time,
            "customer_email": row.customer_email,
            "customer_name": row.customer_name,
            "guest_count": row.guest_count,
            "status": row.status,
            "expires_at": row.expires_at,
            "created_at": row.created_at,
            "validation_status": validation_status,
            "agreement_signed_at": row.agreement_signed_at,
            "deposit_paid_at": row.deposit_paid_at,
            "booking_id": row.converted_to_booking_id,
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
                SELECT id, station_id, event_date, slot_time, customer_email,
                       customer_name, guest_count, signing_token, status,
                       expires_at, created_at, converted_to_booking_id
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
            "event_date": row.event_date,
            "slot_time": row.slot_time,
            "customer_email": row.customer_email,
            "customer_name": row.customer_name,
            "guest_count": row.guest_count,
            "signing_token": str(row.signing_token),  # Convert UUID to string
            "status": row.status,
            "expires_at": row.expires_at,
            "created_at": row.created_at,
            "booking_id": row.converted_to_booking_id,
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
                    converted_to_booking_id = :booking_id
                WHERE id = :hold_id
                AND status IN ('pending', 'signed')
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
        self, station_id: UUID, event_date: date, slot_time: time
    ) -> list[dict[str, Any]]:
        """
        Get all active holds for a specific slot.

        Used to check slot availability including holds.

        Args:
            station_id: Station ID
            event_date: Event date
            slot_time: Slot time

        Returns:
            List of active holds
        """
        result = await self.db.execute(
            text(
                """
                SELECT id, customer_email, customer_name, guest_count, expires_at, created_at
                FROM core.slot_holds
                WHERE station_id = :station_id
                AND event_date = :event_date
                AND slot_time = :slot_time
                AND status IN ('pending', 'signed')
                AND expires_at > NOW()
                ORDER BY created_at
            """
            ),
            {
                "station_id": str(station_id),
                "event_date": event_date,
                "slot_time": slot_time,
            },
        )

        return [
            {
                "id": row.id,
                "customer_email": row.customer_email,
                "customer_name": row.customer_name,
                "guest_count": row.guest_count,
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

        Simple implementation that updates signing_link_sent_at timestamp.
        TODO: Add full send tracking with send_count, channels, rate limiting
        once database schema is updated.

        Args:
            hold_id: The slot hold ID
            channel: Channel used ('sms' or 'email')

        Returns:
            Dict with send_count (always 1 for now), or None if failed
        """
        try:
            result = await self.db.execute(
                text(
                    """
                    UPDATE core.slot_holds
                    SET signing_link_sent_at = NOW()
                    WHERE id = :hold_id
                    RETURNING id, signing_link_sent_at
                """
                ),
                {"hold_id": str(hold_id)},
            )

            row = result.fetchone()
            await self.db.commit()

            if row:
                logger.info(f"Recorded signing link sent for hold {hold_id} " f"via {channel}")
                return {
                    "send_count": 1,
                    "first_sent_at": row.signing_link_sent_at,
                    "last_sent_at": row.signing_link_sent_at,
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

        Simple implementation using base slot_holds table.
        TODO: Add full tracking view once database schema is updated.

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
                    CASE
                        WHEN signing_link_sent_at IS NOT NULL THEN 'sent'
                        ELSE 'pending'
                    END as link_status
                FROM core.slot_holds
                WHERE id = :hold_id
            """
            ),
            {"hold_id": str(hold_id)},
        )

        row = result.fetchone()
        if row:
            return {
                "id": row.id,
                "signing_token": str(row.signing_token) if row.signing_token else None,
                "sent_at": row.signing_link_sent_at,
                "resent_at": None,  # Not tracked yet
                "send_count": 1 if row.signing_link_sent_at else 0,
                "channels": [],  # Not tracked yet
                "status": row.link_status,
                "rate_limited": False,  # Not implemented yet
                "seconds_since_last_send": None,  # Not tracked yet
            }

        return None


# Convenience function for dependency injection
def get_slot_hold_service(db: AsyncSession) -> SlotHoldService:
    """FastAPI dependency injection helper."""
    return SlotHoldService(db)
