"""
Recording Linking Service - Links call recordings to customers and bookings.

This service automatically associates call recordings with:
1. Customers - by matching phone numbers (from_phone/to_phone)
2. Bookings - by correlating call timing with booking dates

Used by: workers/recording_tasks.py (link_recording_entities)
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import phonenumbers
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.core import Booking, BookingStatus, Customer

# MIGRATED: from models.call_recording → db.models.call_recording
from db.models.call_recording import CallRecording

logger = logging.getLogger(__name__)


class RecordingLinkingService:
    """Service for linking call recordings to business entities"""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def normalize_phone(phone: str, default_region: str = "US") -> Optional[str]:
        """
        Normalize phone number to E.164 format: +1XXXXXXXXXX

        Args:
            phone: Phone number in any format
            default_region: Default country code (US, CA, etc.)

        Returns:
            Normalized phone in E.164 format, or None if invalid

        Examples:
            "555-0123" → "+15550123"
            "(555) 012-3456" → "+15550123456"
            "+1-555-012-3456" → "+15550123456"
        """
        if not phone:
            return None

        try:
            parsed = phonenumbers.parse(phone, default_region)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            pass

        # Fallback: strip non-digits, add +1 for US numbers
        digits = re.sub(r"\D", "", phone)
        if len(digits) == 7:  # US local number (no area code)
            logger.warning(f"Phone has no area code, cannot normalize: {phone}")
            return None
        elif len(digits) == 10:  # US number without country code
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith("1"):  # US with country code
            return f"+{digits}"
        else:
            logger.warning(f"Could not normalize phone: {phone}")
            return None

    async def link_customer_by_phone(self, recording: CallRecording) -> Optional[UUID]:
        """
        Match recording to customer by phone number.

        Tries both from_phone (inbound calls) and to_phone (outbound calls).
        Normalizes phone numbers before matching.

        Args:
            recording: CallRecording object with phone numbers

        Returns:
            Customer UUID if found, None otherwise
        """
        # Try from_phone first (customer calling in)
        from_phone = self.normalize_phone(recording.from_phone)
        if from_phone:
            customer = await self._find_customer_by_phone(from_phone)
            if customer:
                logger.info(
                    f"Matched recording {recording.id} to customer {customer.id} "
                    f"via from_phone {from_phone}"
                )
                return customer.id

        # Try to_phone (business calling customer)
        to_phone = self.normalize_phone(recording.to_phone)
        if to_phone:
            customer = await self._find_customer_by_phone(to_phone)
            if customer:
                logger.info(
                    f"Matched recording {recording.id} to customer {customer.id} "
                    f"via to_phone {to_phone}"
                )
                return customer.id

        # Also try raw phone numbers if normalization failed
        if recording.from_phone:
            customer = await self._find_customer_by_phone(recording.from_phone)
            if customer:
                logger.info(
                    f"Matched recording {recording.id} to customer {customer.id} "
                    f"via raw from_phone"
                )
                return customer.id

        if recording.to_phone:
            customer = await self._find_customer_by_phone(recording.to_phone)
            if customer:
                logger.info(
                    f"Matched recording {recording.id} to customer {customer.id} "
                    f"via raw to_phone"
                )
                return customer.id

        logger.info(
            f"No customer match for recording {recording.id} "
            f"(from={recording.from_phone}, to={recording.to_phone})"
        )
        return None

    async def _find_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """Query database for customer by phone number"""
        stmt = select(Customer).where(Customer.phone == phone)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def link_booking_by_context(
        self, recording: CallRecording, customer_id: UUID
    ) -> Optional[UUID]:
        """
        Match recording to booking by timing and context.

        Strategy:
        1. Find bookings for customer within ±24 hours of call
        2. Score each booking by relevance (date proximity, status, etc.)
        3. Return highest scoring booking

        Args:
            recording: CallRecording object with timestamp
            customer_id: Customer UUID (must be set)

        Returns:
            Booking UUID if confident match found, None otherwise
        """
        if not customer_id or not recording.call_started_at:
            return None

        # Define time window for booking search (±24 hours)
        call_time = recording.call_started_at
        time_window_start = call_time - timedelta(hours=24)
        time_window_end = call_time + timedelta(hours=24)

        # Query bookings for this customer near the call time
        stmt = (
            select(Booking)
            .where(
                and_(
                    Booking.customer_id == customer_id,
                    Booking.booking_datetime >= time_window_start,
                    Booking.booking_datetime <= time_window_end,
                    Booking.status.in_(
                        [
                            BookingStatus.PENDING,
                            BookingStatus.CONFIRMED,
                            BookingStatus.SEATED,
                            BookingStatus.COMPLETED,
                        ]
                    ),
                )
            )
            .order_by(
                # Order by closest booking time
                func.abs(
                    func.extract("epoch", Booking.booking_datetime)
                    - func.extract("epoch", call_time)
                )
            )
        )

        result = await self.db.execute(stmt)
        bookings = result.scalars().all()

        if not bookings:
            logger.info(
                f"No bookings found for customer {customer_id} "
                f"within ±24h of call at {call_time}"
            )
            return None

        # Score each booking by relevance
        best_booking = None
        best_score = 0

        for booking in bookings:
            score = self._calculate_booking_relevance_score(booking, call_time, recording)
            if score > best_score:
                best_score = score
                best_booking = booking

        if best_booking and best_score >= 3:  # Minimum confidence threshold
            logger.info(
                f"Matched recording {recording.id} to booking {best_booking.id} "
                f"(score={best_score}, booking_time={best_booking.booking_datetime})"
            )
            return best_booking.id
        else:
            logger.info(
                f"No confident booking match for recording {recording.id} "
                f"(best_score={best_score}, threshold=3)"
            )
            return None

    def _calculate_booking_relevance_score(
        self, booking: Booking, call_time: datetime, recording: CallRecording
    ) -> float:
        """
        Calculate relevance score for a booking match.

        Scoring:
        - Same day: +5 points
        - Within 3 hours: +5 points
        - Within 1 hour: +3 points
        - Booking in future (pre-booking call): +2 points
        - Active status (pending/confirmed): +3 points
        - Contact phone matches: +10 points

        Returns:
            Relevance score (higher = better match)
        """
        score = 0.0
        time_diff = abs((booking.booking_datetime - call_time).total_seconds())

        # Same day bonus
        if booking.booking_datetime.date() == call_time.date():
            score += 5

        # Time proximity bonuses
        if time_diff < 3600:  # Within 1 hour
            score += 3
        elif time_diff < 10800:  # Within 3 hours
            score += 5

        # Future booking (pre-booking call)
        if booking.booking_datetime > call_time:
            score += 2

        # Active booking status
        if booking.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            score += 3

        # Check if contact phone in booking matches recording phones
        if booking.contact_phone:
            normalized_contact = self.normalize_phone(booking.contact_phone)
            normalized_from = self.normalize_phone(recording.from_phone)
            normalized_to = self.normalize_phone(recording.to_phone)

            if normalized_contact and (
                normalized_contact == normalized_from or normalized_contact == normalized_to
            ):
                score += 10

        return score

    async def link_recording(self, recording_id: UUID) -> dict:
        """
        Complete linking process for a recording.

        Workflow:
        1. Get recording from database
        2. Link to customer by phone number
        3. Link to booking (if customer found)
        4. Update database with results
        5. Return summary

        Args:
            recording_id: UUID of CallRecording to link

        Returns:
            dict with linking results: {
                "recording_id": UUID,
                "customer_linked": bool,
                "customer_id": UUID or None,
                "booking_linked": bool,
                "booking_id": UUID or None,
                "error": str or None
            }
        """
        result = {
            "recording_id": recording_id,
            "customer_linked": False,
            "customer_id": None,
            "booking_linked": False,
            "booking_id": None,
            "error": None,
        }

        try:
            # Get recording
            stmt = select(CallRecording).where(CallRecording.id == recording_id)
            db_result = await self.db.execute(stmt)
            recording = db_result.scalar_one_or_none()

            if not recording:
                result["error"] = f"Recording {recording_id} not found"
                logger.error(result["error"])
                return result

            # Skip if already linked
            if recording.customer_id and recording.booking_id:
                logger.info(f"Recording {recording_id} already fully linked")
                result["customer_linked"] = True
                result["customer_id"] = recording.customer_id
                result["booking_linked"] = True
                result["booking_id"] = recording.booking_id
                return result

            # Link customer
            if not recording.customer_id:
                customer_id = await self.link_customer_by_phone(recording)
                if customer_id:
                    recording.customer_id = customer_id
                    result["customer_linked"] = True
                    result["customer_id"] = customer_id
            else:
                result["customer_linked"] = True
                result["customer_id"] = recording.customer_id

            # Link booking (only if customer found)
            if recording.customer_id and not recording.booking_id:
                booking_id = await self.link_booking_by_context(recording, recording.customer_id)
                if booking_id:
                    recording.booking_id = booking_id
                    result["booking_linked"] = True
                    result["booking_id"] = booking_id

            # Commit changes
            await self.db.commit()
            await self.db.refresh(recording)

            logger.info(
                f"Linking complete for recording {recording_id}: "
                f"customer={result['customer_id']}, booking={result['booking_id']}"
            )

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error linking recording {recording_id}: {e}", exc_info=True)
            await self.db.rollback()

        return result

    async def bulk_link_recordings(self, recording_ids: list[UUID], batch_size: int = 50) -> dict:
        """
        Link multiple recordings in batch (for backfilling).

        Args:
            recording_ids: List of recording UUIDs to link
            batch_size: Number of recordings to process at once

        Returns:
            dict with summary statistics
        """
        total = len(recording_ids)
        customers_linked = 0
        bookings_linked = 0
        errors = []

        logger.info(f"Starting bulk link for {total} recordings")

        for i in range(0, total, batch_size):
            batch = recording_ids[i : i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} recordings)")

            for recording_id in batch:
                result = await self.link_recording(recording_id)
                if result["customer_linked"]:
                    customers_linked += 1
                if result["booking_linked"]:
                    bookings_linked += 1
                if result["error"]:
                    errors.append(result["error"])

        logger.info(
            f"Bulk linking complete: {customers_linked}/{total} customers linked, "
            f"{bookings_linked}/{total} bookings linked, {len(errors)} errors"
        )

        return {
            "total_recordings": total,
            "customers_linked": customers_linked,
            "bookings_linked": bookings_linked,
            "errors": errors[:10],  # First 10 errors only
        }
