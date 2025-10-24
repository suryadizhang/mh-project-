"""
Booking Service Layer
Encapsulates booking business logic and orchestrates repository operations
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from uuid import UUID
import logging

from ..core.exceptions import (
    NotFoundException, 
    BusinessLogicException, 
    ConflictException,
    ErrorCode
)
from ..core.cache import CacheService, cached, invalidate_cache
from ..repositories.booking_repository import BookingRepository
from ..models.booking import Booking, BookingStatus
from ..schemas.booking import BookingCreate, BookingUpdate

logger = logging.getLogger(__name__)


class BookingService:
    """
    Service layer for booking operations
    
    Responsibilities:
    - Business rule enforcement
    - Cross-cutting concerns (caching, logging)
    - Transaction coordination
    - Integration with external services
    """
    
    def __init__(
        self, 
        repository: BookingRepository,
        cache: Optional[CacheService] = None
    ):
        """
        Initialize booking service
        
        Args:
            repository: Booking repository instance
            cache: Optional cache service for performance
        """
        self.repository = repository
        self.cache = cache
    
    # Query Operations (with caching)
    
    @cached(ttl=300, key_prefix="booking:stats")
    async def get_dashboard_stats(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
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
            start_date=start_date,
            end_date=end_date,
            include_cancelled=False
        )
        
        # Calculate statistics
        total_bookings = len(bookings)
        total_revenue = sum(b.total_amount or 0 for b in bookings)
        confirmed_bookings = len([b for b in bookings if b.status == BookingStatus.CONFIRMED])
        pending_bookings = len([b for b in bookings if b.status == BookingStatus.PENDING])
        
        # Average party size
        avg_party_size = (
            sum(b.party_size for b in bookings) / total_bookings 
            if total_bookings > 0 else 0
        )
        
        return {
            "total_bookings": total_bookings,
            "total_revenue": float(total_revenue),
            "confirmed_bookings": confirmed_bookings,
            "pending_bookings": pending_bookings,
            "average_party_size": round(avg_party_size, 1),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    @cached(ttl=60, key_prefix="booking:availability")
    async def get_available_slots(
        self,
        event_date: date,
        duration_hours: int = 2
    ) -> List[Dict[str, Any]]:
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
            start_date=event_date,
            end_date=event_date,
            include_cancelled=False
        )
        
        # Build available slots
        available_slots = []
        for hour in range(business_start, business_end - duration_hours + 1):
            slot_start = f"{hour:02d}:00"
            slot_end = f"{(hour + duration_hours):02d}:00"
            
            # Check if slot conflicts with existing bookings
            is_available = True
            for booking in existing_bookings:
                if self._slots_overlap(slot_start, slot_end, booking.event_time, duration_hours):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append({
                    "start_time": slot_start,
                    "end_time": slot_end,
                    "available": True
                })
        
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
                message=f"Booking {booking_id} not found",
                error_code=ErrorCode.NOT_FOUND
            )
        
        return booking
    
    async def get_customer_bookings(
        self,
        customer_id: UUID,
        include_past: bool = False
    ) -> List[Booking]:
        """
        Get all bookings for a customer
        
        Args:
            customer_id: Customer UUID
            include_past: Include past bookings
            
        Returns:
            List of bookings
        """
        bookings = self.repository.find_by_customer(
            customer_id=customer_id,
            include_cancelled=False
        )
        
        if not include_past:
            today = date.today()
            bookings = [b for b in bookings if b.event_date >= today]
        
        return bookings
    
    # Command Operations (invalidate cache)
    
    @invalidate_cache("booking:*")
    async def create_booking(
        self,
        booking_data: BookingCreate
    ) -> Booking:
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
        
        # Check availability
        is_available = self.repository.check_availability(
            event_date=booking_data.event_date,
            event_time=booking_data.event_time,
            duration_hours=booking_data.duration_hours or 2
        )
        
        if not is_available:
            # Capture failed booking as lead for follow-up
            try:
                from ..services.lead_service import LeadService
                lead_service = LeadService(db=self.repository.db)
                
                await lead_service.capture_failed_booking(
                    contact_info={
                        "email": booking_data.contact_email,
                        "phone": booking_data.contact_phone
                    },
                    booking_data={
                        "event_date": booking_data.event_date,
                        "party_size": booking_data.party_size,
                        "event_time": booking_data.event_time,
                        "special_requests": booking_data.special_requests
                    },
                    failure_reason=f"Time slot {booking_data.event_time} already booked"
                )
                logger.info(f"Captured failed booking as lead for {booking_data.contact_email}")
            except Exception as e:
                # Don't fail the booking flow if lead capture fails
                logger.warning(f"Failed to capture lead from failed booking: {e}")
            
            raise ConflictException(
                message=f"Time slot {booking_data.event_time} on {booking_data.event_date} is not available",
                error_code=ErrorCode.BOOKING_NOT_AVAILABLE
            )
        
        # Check for duplicate bookings (same customer, same date/time)
        existing_booking = await self._check_duplicate_booking(
            customer_id=booking_data.customer_id,
            event_date=booking_data.event_date,
            event_time=booking_data.event_time
        )
        
        if existing_booking:
            raise ConflictException(
                message=f"Booking already exists for this customer at {booking_data.event_time} on {booking_data.event_date}",
                error_code=ErrorCode.BOOKING_NOT_AVAILABLE
            )
        
        # Create booking from validated data
        # Use model_dump() to convert Pydantic model to dict
        booking_dict = booking_data.model_dump(exclude_unset=True)
        booking_dict["status"] = BookingStatus.PENDING
        
        booking = self.repository.create(Booking(**booking_dict))
        
        logger.info(f"✅ Booking created: {booking.id}")
        return booking
    
    async def _check_duplicate_booking(
        self,
        customer_id: UUID,
        event_date: date,
        event_time: str
    ) -> Optional[Booking]:
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
            customer_id=customer_id,
            event_date=event_date
        )
        
        # Check if any booking matches the time slot
        for booking in existing_bookings:
            if (booking.event_time == event_time and 
                booking.status not in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]):
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
                error_code=ErrorCode.BOOKING_ALREADY_CONFIRMED
            )
        
        # Update status
        booking.status = BookingStatus.CONFIRMED
        booking.confirmed_at = datetime.utcnow()
        
        updated_booking = self.repository.update(booking)
        
        logger.info(f"✅ Booking confirmed: {booking_id}")
        return updated_booking
    
    @invalidate_cache("booking:*")
    async def cancel_booking(
        self,
        booking_id: UUID,
        reason: Optional[str] = None
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
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
            raise BusinessLogicException(
                message=f"Cannot cancel booking with status {booking.status}",
                error_code=ErrorCode.BOOKING_CANNOT_BE_CANCELLED
            )
        
        # Check if cancellation is allowed (e.g., within 24 hours)
        time_until_event = (
            datetime.combine(booking.event_date, datetime.min.time()) 
            - datetime.now()
        )
        
        if time_until_event.days < 1:
            raise BusinessLogicException(
                message="Cannot cancel booking less than 24 hours before event",
                error_code=ErrorCode.BOOKING_CANNOT_BE_CANCELLED
            )
        
        # Update status
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        booking.cancellation_reason = reason
        
        updated_booking = self.repository.update(booking)
        
        logger.info(f"✅ Booking cancelled: {booking_id}")
        return updated_booking
    
    # Helper methods
    
    def _slots_overlap(
        self,
        slot1_start: str,
        slot1_end: str,
        slot2_start: str,
        duration_hours: int
    ) -> bool:
        """Check if two time slots overlap"""
        # Convert to comparable format
        s1_start = int(slot1_start.split(':')[0])
        s1_end = int(slot1_end.split(':')[0])
        s2_start = int(slot2_start.split(':')[0])
        s2_end = s2_start + duration_hours
        
        # Check overlap
        return not (s1_end <= s2_start or s2_end <= s1_start)
