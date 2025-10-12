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
        customer_id: UUID,
        event_date: date,
        event_time: str,
        party_size: int,
        **kwargs
    ) -> Booking:
        """
        Create a new booking
        
        Args:
            customer_id: Customer UUID
            event_date: Date of event
            event_time: Time of event (HH:MM format)
            party_size: Number of guests
            **kwargs: Additional booking data
            
        Returns:
            Created booking
            
        Raises:
            BusinessLogicException: If business rules are violated
            ConflictException: If time slot is not available
        """
        logger.info(f"Creating booking for customer {customer_id} on {event_date} at {event_time}")
        
        # Validate event is in the future
        if event_date < date.today():
            raise BusinessLogicException(
                message="Cannot book events in the past",
                error_code=ErrorCode.BOOKING_NOT_AVAILABLE
            )
        
        # Validate party size
        if party_size < 1 or party_size > 50:
            raise BusinessLogicException(
                message="Party size must be between 1 and 50",
                error_code=ErrorCode.BOOKING_NOT_AVAILABLE
            )
        
        # Check availability
        is_available = self.repository.check_availability(
            event_date=event_date,
            event_time=event_time,
            duration_hours=kwargs.get('duration_hours', 2)
        )
        
        if not is_available:
            raise ConflictException(
                message=f"Time slot {event_time} on {event_date} is not available",
                error_code=ErrorCode.BOOKING_NOT_AVAILABLE
            )
        
        # Create booking
        booking_data = {
            "customer_id": customer_id,
            "event_date": event_date,
            "event_time": event_time,
            "party_size": party_size,
            "status": BookingStatus.PENDING,
            **kwargs
        }
        
        booking = self.repository.create(Booking(**booking_data))
        
        logger.info(f"✅ Booking created: {booking.id}")
        return booking
    
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
