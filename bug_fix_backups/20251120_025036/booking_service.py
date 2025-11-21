"""
Booking Service Layer
Encapsulates booking business logic and orchestrates repository operations
"""

from datetime import UTC, date, datetime, timedelta
import logging
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

if TYPE_CHECKING:
    from services.lead_service import LeadService

from core.cache import CacheService, cached, invalidate_cache
from core.exceptions import (
    BusinessLogicException,
    ConflictException,
    ErrorCode,
    NotFoundException,
)
from models.booking import Booking, BookingStatus
from models.customer import Customer
from repositories.booking_repository import BookingRepository
from schemas.booking import BookingCreate
from services.audit_service import AuditService
from services.terms_acknowledgment_service import send_terms_for_phone_booking
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


class BookingService:
    """
    Service layer for booking operations with dependency injection.

    Responsibilities:
    - Business rule enforcement
    - Cross-cutting concerns (caching, logging)
    - Transaction coordination
    - Integration with external services (LeadService)
    """

    def __init__(
        self,
        repository: BookingRepository,
        cache: CacheService | None = None,
        lead_service: Optional[
            "LeadService"
        ] = None,  # Forward reference to avoid circular import
        audit_service: AuditService | None = None,
    ):
        """
        Initialize booking service with injected dependencies.

        Args:
            repository: Booking repository instance
            cache: Optional cache service for performance
            lead_service: Optional lead service for failed booking capture
            audit_service: Optional audit service for tracking changes
        """
        self.repository = repository
        self.cache = cache
        self.lead_service = lead_service
        self.audit_service = audit_service

    # Query Operations (with caching)

    @cached(ttl=300, key_prefix="booking:stats")
    async def get_dashboard_stats(
        self,
        user_id: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """
        Get dashboard statistics (cached for 5 minutes)

        Args:
            user_id: Optional user ID to filter by
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dictionary with booking statistics
        """
        logger.info(f"Calculating dashboard stats for user {user_id}")

        # Default to last 30 days
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        bookings = self.repository.find_by_date_range(
            start_date=start_date, end_date=end_date, include_cancelled=False
        )

        # Calculate statistics
        total_bookings = len(bookings)
        total_revenue = sum(b.total_amount or 0 for b in bookings)
        confirmed_bookings = len(
            [b for b in bookings if b.status == BookingStatus.CONFIRMED]
        )
        pending_bookings = len(
            [b for b in bookings if b.status == BookingStatus.PENDING]
        )

        # Average party size
        avg_party_size = (
            sum(b.party_size for b in bookings) / total_bookings
            if total_bookings > 0
            else 0
        )

        return {
            "total_bookings": total_bookings,
            "total_revenue": float(total_revenue),
            "confirmed_bookings": confirmed_bookings,
            "pending_bookings": pending_bookings,
            "average_party_size": round(avg_party_size, 1),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    @cached(ttl=60, key_prefix="booking:availability")
    async def get_available_slots(
        self, event_date: date, duration_hours: int = 2
    ) -> list[dict[str, Any]]:
        """
        Get available time slots for a date (cached for 1 minute)

        Args:
            event_date: Date to check availability
            duration_hours: Duration of event in hours

        Returns:
            List of available time slots
        """
        logger.info(f"Checking availability for {event_date}")

        # Business hours: 11 AM to 10 PM
        business_start = 11
        business_end = 22

        # Get existing bookings for the date
        existing_bookings = self.repository.find_by_date_range(
            start_date=event_date, end_date=event_date, include_cancelled=False
        )

        # Build available slots
        available_slots = []
        for hour in range(business_start, business_end - duration_hours + 1):
            slot_start = f"{hour:02d}:00"
            slot_end = f"{(hour + duration_hours):02d}:00"

            # Check if slot conflicts with existing bookings
            is_available = True
            for booking in existing_bookings:
                if self._slots_overlap(
                    slot_start, slot_end, booking.event_time, duration_hours
                ):
                    is_available = False
                    break

            if is_available:
                available_slots.append(
                    {
                        "start_time": slot_start,
                        "end_time": slot_end,
                        "available": True,
                    }
                )

        return available_slots

    async def get_booking_by_id(self, booking_id: UUID) -> Booking:
        """
        Get booking by ID

        Args:
            booking_id: Booking UUID

        Returns:
            Booking model

        Raises:
            NotFoundException: If booking not found
        """
        booking = self.repository.get_by_id(booking_id)

        if not booking:
            raise NotFoundException(
                resource="Booking", identifier=str(booking_id)
            )

        return booking

    async def get_customer_bookings(
        self, customer_id: UUID, include_past: bool = False
    ) -> list[Booking]:
        """
        Get all bookings for a customer

        Args:
            customer_id: Customer UUID
            include_past: Include past bookings

        Returns:
            List of bookings
        """
        bookings = self.repository.find_by_customer_id(
            customer_id=customer_id, include_cancelled=False
        )

        if not include_past:
            today = date.today()
            bookings = [b for b in bookings if b.event_date >= today]

        return bookings

    # Command Operations (invalidate cache)

    @invalidate_cache("booking:*")
    async def create_booking(self, booking_data: BookingCreate) -> Booking:
        """
        Create a new booking with validated input

        Args:
            booking_data: Validated booking creation schema (Pydantic model)
                - All inputs validated against schema constraints
                - No **kwargs injection possible
                - Time format validated (HH:MM 24-hour)
                - Party size validated (1-50 guests)
                - Date validated (must be in future)
                - Text fields sanitized (XSS prevention)

        Returns:
            Created booking

        Raises:
            BusinessLogicException: If business rules are violated
            ConflictException: If time slot is not available

        Security:
            ✅ No **kwargs injection
            ✅ All fields explicitly validated by Pydantic
            ✅ Time format enforced (HH:MM 24-hour)
            ✅ Party size constrained (1-50)
            ✅ Date cannot be in past
            ✅ Text fields sanitized
        """
        logger.info(
            f"Creating booking for customer {booking_data.customer_id} "
            f"on {booking_data.event_date} at {booking_data.event_time}"
        )

        # Date validation already done by Pydantic (event_date >= today)
        # Time format already validated by Pydantic (HH:MM 24-hour)
        # Party size already validated by Pydantic (1-50)

        # Convert event_date + event_time to booking_datetime for availability check
        try:
            event_time_obj = datetime.strptime(
                booking_data.event_time, "%H:%M"
            ).time()
            event_datetime = datetime.combine(
                booking_data.event_date, event_time_obj, tzinfo=UTC
            )
        except ValueError as e:
            raise BusinessLogicException(
                message=f"Invalid time format '{booking_data.event_time}': expected HH:MM (24-hour format)",
                error_code=ErrorCode.BAD_REQUEST,
            ) from e

        # Check availability
        is_available = self.repository.check_availability(
            booking_datetime=event_datetime,
            party_size=booking_data.party_size,
            exclude_booking_id=None,
        )

        if not is_available:
            # Capture failed booking as lead for follow-up
            if self.lead_service:
                try:
                    await self.lead_service.capture_failed_booking(
                        contact_info={
                            "email": booking_data.contact_email,
                            "phone": booking_data.contact_phone,
                        },
                        booking_data={
                            "event_date": booking_data.event_date,
                            "party_size": booking_data.party_size,
                            "event_time": booking_data.event_time,
                            "special_requests": booking_data.special_requests,
                        },
                        failure_reason=f"Time slot {booking_data.event_time} already booked",
                    )
                    logger.info(
                        f"Captured failed booking as lead for {booking_data.contact_email}"
                    )
                except Exception as e:
                    # Don't fail the booking flow if lead capture fails
                    logger.warning(
                        f"Failed to capture lead from failed booking: {e}"
                    )

            raise ConflictException(
                message=f"Time slot {booking_data.event_time} on {booking_data.event_date} is not available",
                error_code=ErrorCode.BOOKING_NOT_AVAILABLE,
            )

        # Check for duplicate bookings (same customer, same date/time)
        existing_booking = await self._check_duplicate_booking(
            customer_id=booking_data.customer_id,
            event_date=booking_data.event_date,
            event_time=booking_data.event_time,
        )

        if existing_booking:
            raise ConflictException(
                message=f"Booking already exists for this customer at {booking_data.event_time} on {booking_data.event_date}",
                error_code=ErrorCode.BOOKING_NOT_AVAILABLE,
            )

        # Create booking from validated data
        # Use model_dump() to convert Pydantic model to dict
        booking_dict = booking_data.model_dump(exclude_unset=True)

        # Convert event_date + event_time → booking_datetime
        if "event_date" in booking_dict and "event_time" in booking_dict:
            event_date = booking_dict.pop("event_date")
            event_time = booking_dict.pop("event_time")

            try:
                # Use strptime for robust parsing and validation (consistent with line 247)
                time_obj = datetime.strptime(event_time, "%H:%M").time()
                booking_dict["booking_datetime"] = datetime.combine(
                    event_date, time_obj, tzinfo=UTC
                )
            except ValueError as e:
                raise BusinessLogicException(
                    message=f"Invalid time format '{event_time}': expected HH:MM (24-hour format)",
                    error_code=ErrorCode.BAD_REQUEST,
                ) from e

        booking_dict["status"] = BookingStatus.PENDING

        # Dual deadline system:
        # - Customer sees 2-hour deadline (creates urgency)
        # - Internal enforcement at 24 hours (grace period)
        now = datetime.now(UTC)
        booking_dict["customer_deposit_deadline"] = now + timedelta(hours=2)
        booking_dict["internal_deadline"] = now + timedelta(hours=24)
        booking_dict["deposit_deadline"] = now + timedelta(
            hours=2
        )  # Backward compat

        # Record SMS consent timestamp if consent given
        if booking_data.sms_consent:
            booking_dict["sms_consent_timestamp"] = now

        # Create booking with race condition protection
        # Three-layer defense against double bookings:
        # 1. SELECT FOR UPDATE in check_availability() (row-level locking)
        # 2. UNIQUE constraint on (booking_datetime, status) at database level
        # 3. IntegrityError handling below (catches DB constraint violations)
        try:
            booking = self.repository.create(Booking(**booking_dict))
        except IntegrityError as e:
            # Unique constraint violation: Another request won the race
            # This means someone booked this exact datetime between our
            # availability check and our insert attempt
            logger.warning(
                f"Race condition detected: booking_datetime={event_datetime} "
                f"already exists. IntegrityError: {e!s}"
            )

            # Capture as lead for follow-up (same as availability failure above)
            if self.lead_service:
                try:
                    await self.lead_service.capture_failed_booking(
                        contact_info={
                            "email": booking_data.contact_email,
                            "phone": booking_data.contact_phone,
                        },
                        booking_data={
                            "event_date": booking_data.event_date,
                            "party_size": booking_data.party_size,
                            "event_time": booking_data.event_time,
                            "special_requests": booking_data.special_requests,
                        },
                        failure_reason=f"Race condition: Time slot {booking_data.event_time} was booked by another request",
                    )
                    logger.info(
                        f"Captured failed booking (race condition) as lead for {booking_data.contact_email}"
                    )
                except Exception as lead_err:
                    logger.warning(
                        f"Failed to capture lead from race condition: {lead_err}"
                    )

            # Return user-friendly error
            raise ConflictException(
                message=f"Time slot {booking_data.event_time} on {booking_data.event_date} was just booked by another customer. Please select a different time.",
                error_code=ErrorCode.BOOKING_NOT_AVAILABLE,
            ) from e

        # Audit log: Track booking creation
        if self.audit_service:
            try:
                await self.audit_service.log_change(
                    table_name="bookings",
                    record_id=booking.id,
                    action="INSERT",
                    new_values=booking_dict,
                    user_id=booking_data.customer_id,
                )
            except Exception as e:
                logger.warning(f"Failed to log booking creation audit: {e}")

        # Send terms & conditions acknowledgment for phone/SMS bookings
        booking_source = getattr(booking_data, "source", None) or getattr(
            booking_data, "booking_source", "web"
        )
        if booking_source in ["phone", "sms", "whatsapp"]:
            try:
                # Get customer info for SMS
                customer = (
                    self.repository.db.query(Customer)
                    .filter_by(id=booking_data.customer_id)
                    .first()
                )
                if customer and customer.phone:
                    await send_terms_for_phone_booking(
                        db=self.repository.db,
                        customer_phone=customer.phone,
                        customer_name=customer.name,
                        booking_id=booking.id,
                    )
                    logger.info(
                        f"📱 Terms SMS sent to {customer.phone[-4:]} for booking {booking.id}"
                    )
                else:
                    logger.warning(
                        f"⚠️ Cannot send terms SMS: customer {booking_data.customer_id} has no phone"
                    )
            except Exception as e:
                # Don't fail booking if terms SMS fails - staff can follow up manually
                logger.error(
                    f"❌ Failed to send terms SMS for booking {booking.id}: {e}"
                )

        # TODO: Send booking confirmation SMS with deposit deadline
        # "Booking confirmed! Pay $100 deposit within 2 hours to lock your date."
        # "Payment methods: Stripe, Venmo, Zelle - Reply HELP for instructions"

        logger.info(f"✅ Booking created: {booking.id}")
        return booking

    async def _check_duplicate_booking(
        self, customer_id: UUID, event_date: date, event_time: str
    ) -> Booking | None:
        """
        Check if customer already has a booking at this date/time

        Args:
            customer_id: Customer UUID
            event_date: Event date
            event_time: Event time (HH:MM)

        Returns:
            Existing booking if found, None otherwise
        """
        # Query for existing active bookings
        existing_bookings = self.repository.find_by_customer_and_date(
            customer_id=customer_id, event_date=event_date
        )

        # Check if any booking matches the time slot
        for booking in existing_bookings:
            if booking.event_time == event_time and booking.status not in [
                BookingStatus.CANCELLED,
                BookingStatus.COMPLETED,
            ]:
                return booking

        return None

    @invalidate_cache("booking:*")
    async def confirm_booking(self, booking_id: UUID) -> Booking:
        """
        Confirm a pending booking

        Args:
            booking_id: Booking UUID

        Returns:
            Updated booking

        Raises:
            NotFoundException: If booking not found
            BusinessLogicException: If booking cannot be confirmed
        """
        booking = await self.get_booking_by_id(booking_id)

        # Validate state transition
        if booking.status != BookingStatus.PENDING:
            raise BusinessLogicException(
                message=f"Cannot confirm booking with status {booking.status}",
                error_code=ErrorCode.BOOKING_ALREADY_CONFIRMED,
            )

        # Store old values for audit
        old_values = {"status": booking.status.value, "confirmed_at": None}

        # Update status
        booking.status = BookingStatus.CONFIRMED
        booking.confirmed_at = datetime.now(UTC)

        updated_booking = self.repository.update(booking)

        # Audit log: Track booking confirmation
        if self.audit_service:
            try:
                await self.audit_service.log_change(
                    table_name="bookings",
                    record_id=booking_id,
                    action="UPDATE",
                    old_values=old_values,
                    new_values={
                        "status": "confirmed",
                        "confirmed_at": booking.confirmed_at.isoformat(),
                    },
                )
            except Exception as e:
                logger.warning(
                    f"Failed to log booking confirmation audit: {e}"
                )

        logger.info(f"✅ Booking confirmed: {booking_id}")
        return updated_booking

    @invalidate_cache("booking:*")
    async def cancel_booking(
        self, booking_id: UUID, reason: str | None = None
    ) -> Booking:
        """
        Cancel a booking

        Args:
            booking_id: Booking UUID
            reason: Optional cancellation reason

        Returns:
            Updated booking

        Raises:
            NotFoundException: If booking not found
            BusinessLogicException: If booking cannot be cancelled
        """
        booking = await self.get_booking_by_id(booking_id)

        # Validate state transition
        if booking.status in [
            BookingStatus.CANCELLED,
            BookingStatus.COMPLETED,
        ]:
            raise BusinessLogicException(
                message=f"Cannot cancel booking with status {booking.status}",
                error_code=ErrorCode.BOOKING_CANNOT_BE_CANCELLED,
            )

        # Check if cancellation is allowed (e.g., within 24 hours)
        # Use booking_datetime directly (timezone-aware) for accurate calculation
        time_until_event = booking.booking_datetime - datetime.now(UTC)

        if time_until_event.days < 1:
            raise BusinessLogicException(
                message="Cannot cancel booking less than 24 hours before event",
                error_code=ErrorCode.BOOKING_CANNOT_BE_CANCELLED,
            )

        # Store old values for audit
        old_values = {
            "status": booking.status.value,
            "cancelled_at": None,
            "cancellation_reason": None,
        }

        # Update status
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.now(UTC)
        booking.cancellation_reason = reason

        updated_booking = self.repository.update(booking)

        # Audit log: Track booking cancellation
        if self.audit_service:
            try:
                await self.audit_service.log_change(
                    table_name="bookings",
                    record_id=booking_id,
                    action="UPDATE",
                    old_values=old_values,
                    new_values={
                        "status": "cancelled",
                        "cancelled_at": booking.cancelled_at.isoformat(),
                        "cancellation_reason": reason,
                    },
                )
            except Exception as e:
                logger.warning(
                    f"Failed to log booking cancellation audit: {e}"
                )

        logger.info(f"✅ Booking cancelled: {booking_id}")
        return updated_booking

    @invalidate_cache("booking:*")
    async def hold_booking(
        self,
        booking_id: UUID,
        staff_member: str,
        reason: str = "Hold requested by customer service",
    ) -> Booking:
        """
        Place an administrative hold on a booking to prevent auto-cancellation.

        When a booking is on hold:
        - Auto-cancel task will skip it even if deposit deadline passes
        - Customer service/admin can manually review and process
        - Useful for VIP clients, payment issues, special circumstances

        Args:
            booking_id: Booking UUID
            staff_member: Username/email of staff placing hold
            reason: Reason for hold (shown to staff, not customer)

        Returns:
            Updated booking with hold status

        Raises:
            NotFoundException: If booking not found
            BusinessLogicException: If booking already completed/cancelled
        """
        booking = await self.get_booking_by_id(booking_id)

        if booking.status in [
            BookingStatus.COMPLETED,
            BookingStatus.CANCELLED,
        ]:
            raise BusinessLogicException(
                message=f"Cannot hold booking with status {booking.status}",
                error_code=ErrorCode.INVALID_BOOKING_STATE,
            )

        # Place hold
        booking.hold_on_request = True
        booking.held_by = staff_member
        booking.held_at = datetime.now(UTC)
        booking.hold_reason = reason

        updated_booking = self.repository.update(booking)

        # Audit log
        if self.audit_service:
            try:
                await self.audit_service.log_change(
                    table_name="bookings",
                    record_id=booking.id,
                    action="UPDATE",
                    old_values={"hold_on_request": False},
                    new_values={
                        "hold_on_request": True,
                        "held_by": staff_member,
                        "held_at": booking.held_at.isoformat(),
                        "hold_reason": reason,
                    },
                    user_id=staff_member,
                )
            except Exception as e:
                logger.warning(f"Failed to log hold action: {e}")

        logger.info(
            f"📌 Booking {booking_id} placed on hold by {staff_member}. Reason: {reason}"
        )
        return updated_booking

    @invalidate_cache("booking:*")
    async def release_hold(
        self,
        booking_id: UUID,
        staff_member: str,
    ) -> Booking:
        """
        Release an administrative hold on a booking.

        After release:
        - Booking returns to normal auto-cancel rules
        - If deposit deadline already passed, may be immediately auto-cancelled

        Args:
            booking_id: Booking UUID
            staff_member: Username/email of staff releasing hold

        Returns:
            Updated booking with hold removed
        """
        booking = await self.get_booking_by_id(booking_id)

        if not booking.hold_on_request:
            raise BusinessLogicException(
                message=f"Booking {booking_id} is not on hold",
                error_code=ErrorCode.INVALID_BOOKING_STATE,
            )

        # Release hold
        old_held_by = booking.held_by
        old_reason = booking.hold_reason

        booking.hold_on_request = False
        booking.held_by = None
        booking.held_at = None
        booking.hold_reason = None

        updated_booking = self.repository.update(booking)

        # Audit log
        if self.audit_service:
            try:
                await self.audit_service.log_change(
                    table_name="bookings",
                    record_id=booking.id,
                    action="UPDATE",
                    old_values={
                        "hold_on_request": True,
                        "held_by": old_held_by,
                        "hold_reason": old_reason,
                    },
                    new_values={"hold_on_request": False},
                    user_id=staff_member,
                )
            except Exception as e:
                logger.warning(f"Failed to log hold release: {e}")

        logger.info(
            f"🔓 Hold released on booking {booking_id} by {staff_member}"
        )
        return updated_booking

    @invalidate_cache("booking:*")
    async def confirm_deposit_received(
        self,
        booking_id: UUID,
        staff_member: str,
        amount: float,
        payment_method: str,
        notes: str | None = None,
    ) -> Booking:
        """
        Manual admin confirmation that deposit has been received.
        Works with payment tracking system - admin clicks "Deposit Received" button.

        This function:
        - Updates booking status to CONFIRMED
        - Records who confirmed and when
        - Removes any holds (no longer needed)
        - Prevents auto-cancellation

        Args:
            booking_id: Booking UUID
            staff_member: Admin email who confirmed deposit
            amount: Deposit amount received (must be >= $100)
            payment_method: How customer paid (Stripe, Venmo, Zelle, Cash, etc)
            notes: Optional admin notes

        Returns:
            Updated booking with CONFIRMED status

        Raises:
            NotFoundException: If booking not found
            BusinessLogicException: If amount < $100 or booking already confirmed
        """
        booking = await self.get_booking_by_id(booking_id)

        # Validate amount
        if amount < 100.00:
            raise BusinessLogicException(
                message=f"Deposit amount ${amount:.2f} is less than required $100.00",
                error_code=ErrorCode.BAD_REQUEST,
            )

        # Check if already confirmed
        if booking.status == BookingStatus.CONFIRMED:
            raise BusinessLogicException(
                message=f"Booking {booking_id} is already confirmed",
                error_code=ErrorCode.BOOKING_ALREADY_CONFIRMED,
            )

        if booking.status in [
            BookingStatus.CANCELLED,
            BookingStatus.COMPLETED,
        ]:
            raise BusinessLogicException(
                message=f"Cannot confirm deposit for {booking.status} booking",
                error_code=ErrorCode.INVALID_BOOKING_STATE,
            )

        # Update booking
        old_status = booking.status
        booking.status = BookingStatus.CONFIRMED
        booking.confirmed_at = datetime.now(UTC)
        booking.deposit_confirmed_at = datetime.now(UTC)
        booking.deposit_confirmed_by = staff_member

        # Remove any holds (no longer needed since deposit confirmed)
        booking.hold_on_request = False
        booking.held_by = None
        booking.held_at = None
        booking.hold_reason = None

        updated_booking = self.repository.update(booking)

        # Audit log
        if self.audit_service:
            try:
                await self.audit_service.log_change(
                    table_name="bookings",
                    record_id=booking.id,
                    action="UPDATE",
                    old_values={"status": old_status.value},
                    new_values={
                        "status": BookingStatus.CONFIRMED.value,
                        "confirmed_at": booking.confirmed_at.isoformat(),
                        "deposit_confirmed_at": booking.deposit_confirmed_at.isoformat(),
                        "deposit_confirmed_by": staff_member,
                        "deposit_amount": amount,
                        "payment_method": payment_method,
                        "notes": notes,
                    },
                    user_id=staff_member,
                )
            except Exception as e:
                logger.warning(f"Failed to log deposit confirmation: {e}")

        logger.info(
            f"✅ Deposit confirmed for booking {booking_id} by {staff_member}: "
            f"${amount:.2f} via {payment_method}"
        )

        # TODO: Send confirmation SMS to customer
        # "Deposit received! Your event date is locked. We'll contact you for details."

        return updated_booking

    # Helper methods

    def _slots_overlap(
        self,
        slot1_start: str,
        slot1_end: str,
        slot2_start: str,
        duration_hours: int,
    ) -> bool:
        """Check if two time slots overlap (handles HH:MM format with minute precision)

        Args:
            slot1_start: Start time in HH:MM format
            slot1_end: End time in HH:MM format
            slot2_start: Start time in HH:MM format (from booking.event_time)
            duration_hours: Duration of slot2 in hours

        Returns:
            True if slots overlap, False otherwise

        Raises:
            BusinessLogicException: If time format is invalid
        """
        try:
            # Parse hours AND minutes for accurate comparison
            s1_h, s1_m = map(int, slot1_start.split(":"))
            s1_end_h, s1_end_m = map(int, slot1_end.split(":"))
            s2_h, s2_m = map(int, slot2_start.split(":"))

            # Validate time values
            if not (0 <= s1_h < 24 and 0 <= s1_m < 60):
                raise ValueError(f"Invalid time values: {slot1_start}")
            if not (0 <= s1_end_h < 24 and 0 <= s1_end_m < 60):
                raise ValueError(f"Invalid time values: {slot1_end}")
            if not (0 <= s2_h < 24 and 0 <= s2_m < 60):
                raise ValueError(f"Invalid time values: {slot2_start}")
        except (ValueError, AttributeError, IndexError) as e:
            logger.error(
                f"Invalid time format in overlap check: "
                f"slot1=({slot1_start}, {slot1_end}), slot2={slot2_start}",
                exc_info=True,
            )
            raise BusinessLogicException(
                message="Invalid time format detected in availability check",
                error_code=ErrorCode.DATA_INTEGRITY_ERROR,
            ) from e

        # Convert to minutes since midnight for accurate comparison
        s1_start_mins = s1_h * 60 + s1_m
        s1_end_mins = s1_end_h * 60 + s1_end_m
        s2_start_mins = s2_h * 60 + s2_m
        s2_end_mins = s2_start_mins + (duration_hours * 60)

        # Check overlap: slot1 and slot2 overlap if neither ends before the other starts
        return not (
            s1_end_mins <= s2_start_mins or s2_end_mins <= s1_start_mins
        )
