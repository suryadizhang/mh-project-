"""
Booking Repository Implementation
Handles booking-specific data access patterns and business logic
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import Session, joinedload
from enum import Enum

from core.repository import BaseRepository, FilterCriteria, SortCriteria
from core.exceptions import (
    NotFoundException, ConflictException, BusinessLogicException,
    ErrorCode, raise_not_found, raise_business_error
)
from models.booking import Booking, BookingStatus

class BookingSearchFilters(str, Enum):
    """Available search filters for bookings"""
    BY_DATE_RANGE = "date_range"
    BY_STATUS = "status"
    BY_CUSTOMER = "customer"
    BY_LOCATION = "location"
    BY_PARTY_SIZE = "party_size"
    BY_TIME_SLOT = "time_slot"
    BY_SPECIAL_REQUESTS = "special_requests"

class BookingRepository(BaseRepository[Booking]):
    """
    Repository for booking operations with specialized business logic
    
    Features:
    - Date range filtering
    - Availability checking
    - Conflict detection
    - Time slot management
    - Customer booking history
    - Status transition validation
    """
    
    def __init__(self, session: Session):
        super().__init__(session, Booking)
    
    # Specialized Find Methods
    
    def find_by_date_range(
        self,
        start_date: date,
        end_date: date,
        include_cancelled: bool = False
    ) -> List[Booking]:
        """Find bookings within a date range with eager loading"""
        query = self.session.query(self.model).options(
            joinedload(self.model.customer)  # Eager load customer to avoid N+1
        ).filter(
            and_(
                func.date(self.model.booking_datetime) >= start_date,
                func.date(self.model.booking_datetime) <= end_date
            )
        )
        
        if not include_cancelled:
            query = query.filter(self.model.status != BookingStatus.CANCELLED)
        
        return query.order_by(self.model.booking_datetime).all()
    
    def find_by_customer_id(
        self,
        customer_id: int,
        limit: Optional[int] = None,
        include_cancelled: bool = True
    ) -> List[Booking]:
        """Find bookings by customer ID with eager loading"""
        query = self.session.query(self.model).options(
            joinedload(self.model.customer)  # Eager load customer to avoid N+1
        ).filter(
            self.model.customer_id == customer_id
        )
        
        if not include_cancelled:
            query = query.filter(self.model.status != BookingStatus.CANCELLED)
        
        query = query.order_by(self.model.booking_datetime.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def find_by_status(self, status: BookingStatus) -> List[Booking]:
        """Find bookings by status with eager loading"""
        return self.session.query(self.model).options(
            joinedload(self.model.customer)  # Eager load customer to avoid N+1
        ).filter(
            self.model.status == status
        ).order_by(self.model.booking_datetime).all()
    
    def find_by_customer_and_date(
        self,
        customer_id: str,
        event_date: date
    ) -> List[Booking]:
        """
        Find all bookings for a specific customer on a specific date
        
        Args:
            customer_id: Customer UUID (as string)
            event_date: Event date to search
            
        Returns:
            List of bookings matching customer and date with eager loading
        """
        return self.session.query(self.model).options(
            joinedload(self.model.customer)  # Eager load customer to avoid N+1
        ).filter(
            and_(
                self.model.customer_id == customer_id,
                func.date(self.model.booking_datetime) == event_date
            )
        ).order_by(self.model.booking_datetime).all()
    
    def find_pending_confirmations(self, hours_old: int = 24) -> List[Booking]:
        """Find bookings pending confirmation for more than specified hours with eager loading"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
        
        return self.session.query(self.model).options(
            joinedload(self.model.customer)  # Eager load customer to avoid N+1
        ).filter(
            and_(
                self.model.status == BookingStatus.PENDING,
                self.model.created_at <= cutoff_time
            )
        ).all()
    
    def find_upcoming_bookings(
        self,
        customer_id: Optional[int] = None,
        days_ahead: int = 30
    ) -> List[Booking]:
        """Find upcoming confirmed bookings with eager loading"""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days_ahead)
        
        query = self.session.query(self.model).options(
            joinedload(self.model.customer)  # Eager load customer to avoid N+1
        ).filter(
            and_(
                self.model.booking_datetime >= start_date,
                self.model.booking_datetime <= end_date,
                self.model.status == BookingStatus.CONFIRMED
            )
        )
        
        if customer_id:
            query = query.filter(self.model.customer_id == customer_id)
        
        return query.order_by(self.model.booking_datetime).all()
    
    # Availability Methods
    
    def check_availability(
        self,
        booking_datetime: datetime,
        party_size: int,
        exclude_booking_id: Optional[int] = None
    ) -> bool:
        """Check if a time slot is available for the given party size"""
        # Get bookings in the same time window (±2 hours)
        time_window_start = booking_datetime - timedelta(hours=2)
        time_window_end = booking_datetime + timedelta(hours=2)
        
        query = self.session.query(self.model).filter(
            and_(
                self.model.booking_datetime >= time_window_start,
                self.model.booking_datetime <= time_window_end,
                self.model.status.in_([
                    BookingStatus.CONFIRMED,
                    BookingStatus.PENDING,
                    BookingStatus.SEATED
                ])
            )
        )
        
        if exclude_booking_id:
            query = query.filter(self.model.id != exclude_booking_id)
        
        existing_bookings = query.all()
        
        # Calculate total party size in the time window
        total_party_size = sum(booking.party_size for booking in existing_bookings)
        
        # Assume maximum capacity of 100 (this should come from configuration)
        max_capacity = 100
        
        return (total_party_size + party_size) <= max_capacity
    
    def get_available_time_slots(
        self,
        target_date: date,
        party_size: int,
        time_increment_minutes: int = 30
    ) -> List[datetime]:
        """Get available time slots for a given date and party size"""
        available_slots = []
        
        # Define restaurant hours (should come from configuration)
        opening_time = datetime.combine(target_date, datetime.min.time().replace(hour=11))
        closing_time = datetime.combine(target_date, datetime.min.time().replace(hour=22))
        
        current_time = opening_time
        
        while current_time <= closing_time:
            if self.check_availability(current_time, party_size):
                available_slots.append(current_time)
            
            current_time += timedelta(minutes=time_increment_minutes)
        
        return available_slots
    
    def find_conflicting_bookings(
        self,
        booking_datetime: datetime,
        party_size: int,
        exclude_booking_id: Optional[int] = None
    ) -> List[Booking]:
        """Find bookings that would conflict with the proposed booking with eager loading"""
        # Check for exact time conflicts (±1 hour)
        time_buffer = timedelta(hours=1)
        start_time = booking_datetime - time_buffer
        end_time = booking_datetime + time_buffer
        
        query = self.session.query(self.model).options(
            joinedload(self.model.customer)  # Eager load customer to avoid N+1
        ).filter(
            and_(
                self.model.booking_datetime >= start_time,
                self.model.booking_datetime <= end_time,
                self.model.status.in_([
                    BookingStatus.CONFIRMED,
                    BookingStatus.PENDING,
                    BookingStatus.SEATED
                ])
            )
        )
        
        if exclude_booking_id:
            query = query.filter(self.model.id != exclude_booking_id)
        
        return query.all()
    
    # Business Logic Methods
    
    def create_booking(
        self,
        customer_id: int,
        booking_datetime: datetime,
        party_size: int,
        special_requests: Optional[str] = None,
        contact_phone: Optional[str] = None,
        contact_email: Optional[str] = None
    ) -> Booking:
        """Create a new booking with validation"""
        # Validate booking time (must be in future)
        if booking_datetime <= datetime.utcnow():
            raise_business_error(
                "Booking time must be in the future",
                ErrorCode.BOOKING_NOT_AVAILABLE,
                "future_time_required"
            )
        
        # Validate party size
        if party_size <= 0 or party_size > 20:
            raise_business_error(
                "Party size must be between 1 and 20",
                ErrorCode.VALIDATION_ERROR,
                "valid_party_size_required"
            )
        
        # Check availability
        if not self.check_availability(booking_datetime, party_size):
            conflicting_bookings = self.find_conflicting_bookings(
                booking_datetime, party_size
            )
            raise_business_error(
                "Requested time slot is not available",
                ErrorCode.BOOKING_NOT_AVAILABLE,
                "time_slot_unavailable",
                details={
                    "requested_datetime": booking_datetime.isoformat(),
                    "party_size": party_size,
                    "conflicting_bookings": len(conflicting_bookings)
                }
            )
        
        # Create booking
        booking_data = {
            "customer_id": customer_id,
            "booking_datetime": booking_datetime,
            "party_size": party_size,
            "status": BookingStatus.PENDING,
            "special_requests": special_requests,
            "contact_phone": contact_phone,
            "contact_email": contact_email,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        return self.create(booking_data)
    
    def confirm_booking(self, booking_id: int) -> Booking:
        """Confirm a pending booking"""
        booking = self.get_by_id(booking_id)
        if not booking:
            raise_not_found("Booking", str(booking_id))
        
        if booking.status != BookingStatus.PENDING:
            raise_business_error(
                f"Booking cannot be confirmed. Current status: {booking.status.value}",
                ErrorCode.BOOKING_ALREADY_CONFIRMED,
                "invalid_status_transition",
                details={
                    "current_status": booking.status.value,
                    "required_status": BookingStatus.PENDING.value
                }
            )
        
        # Double-check availability before confirming
        if not self.check_availability(
            booking.booking_datetime,
            booking.party_size,
            exclude_booking_id=booking.id
        ):
            raise_business_error(
                "Booking cannot be confirmed - time slot is no longer available",
                ErrorCode.BOOKING_NOT_AVAILABLE,
                "availability_changed"
            )
        
        update_data = {
            "status": BookingStatus.CONFIRMED,
            "confirmed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        return self.update(booking.id, update_data)
    
    def cancel_booking(
        self,
        booking_id: int,
        cancellation_reason: Optional[str] = None
    ) -> Booking:
        """Cancel a booking"""
        booking = self.get_by_id(booking_id)
        if not booking:
            raise_not_found("Booking", str(booking_id))
        
        # Check if booking can be cancelled
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
            raise_business_error(
                f"Booking cannot be cancelled. Current status: {booking.status.value}",
                ErrorCode.BOOKING_CANNOT_BE_CANCELLED,
                "invalid_status_for_cancellation",
                details={
                    "current_status": booking.status.value,
                    "cancellable_statuses": [
                        BookingStatus.PENDING.value,
                        BookingStatus.CONFIRMED.value,
                        BookingStatus.SEATED.value
                    ]
                }
            )
        
        # Check cancellation policy (e.g., cannot cancel within 2 hours)
        time_until_booking = booking.booking_datetime - datetime.utcnow()
        if time_until_booking < timedelta(hours=2):
            raise_business_error(
                "Booking cannot be cancelled within 2 hours of the scheduled time",
                ErrorCode.BOOKING_CANNOT_BE_CANCELLED,
                "cancellation_policy_violation",
                details={
                    "hours_until_booking": time_until_booking.total_seconds() / 3600,
                    "minimum_hours_required": 2
                }
            )
        
        update_data = {
            "status": BookingStatus.CANCELLED,
            "cancelled_at": datetime.utcnow(),
            "cancellation_reason": cancellation_reason,
            "updated_at": datetime.utcnow()
        }
        
        return self.update(booking.id, update_data)
    
    def mark_as_seated(self, booking_id: int) -> Booking:
        """Mark a booking as seated"""
        booking = self.get_by_id(booking_id)
        if not booking:
            raise_not_found("Booking", str(booking_id))
        
        if booking.status != BookingStatus.CONFIRMED:
            raise_business_error(
                f"Only confirmed bookings can be marked as seated. Current status: {booking.status.value}",
                ErrorCode.VALIDATION_ERROR,
                "invalid_status_transition"
            )
        
        update_data = {
            "status": BookingStatus.SEATED,
            "seated_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        return self.update(booking.id, update_data)
    
    def complete_booking(self, booking_id: int) -> Booking:
        """Mark a booking as completed"""
        booking = self.get_by_id(booking_id)
        if not booking:
            raise_not_found("Booking", str(booking_id))
        
        if booking.status != BookingStatus.SEATED:
            raise_business_error(
                f"Only seated bookings can be completed. Current status: {booking.status.value}",
                ErrorCode.VALIDATION_ERROR,
                "invalid_status_transition"
            )
        
        update_data = {
            "status": BookingStatus.COMPLETED,
            "completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        return self.update(booking.id, update_data)
    
    # Analytics Methods
    
    def get_booking_statistics(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Get booking statistics for a date range"""
        # Total bookings
        total_bookings = self.session.query(func.count(self.model.id)).filter(
            and_(
                func.date(self.model.booking_datetime) >= start_date,
                func.date(self.model.booking_datetime) <= end_date
            )
        ).scalar()
        
        # Bookings by status
        status_stats = self.session.query(
            self.model.status,
            func.count(self.model.id)
        ).filter(
            and_(
                func.date(self.model.booking_datetime) >= start_date,
                func.date(self.model.booking_datetime) <= end_date
            )
        ).group_by(self.model.status).all()
        
        # Average party size
        avg_party_size = self.session.query(func.avg(self.model.party_size)).filter(
            and_(
                func.date(self.model.booking_datetime) >= start_date,
                func.date(self.model.booking_datetime) <= end_date,
                self.model.status != BookingStatus.CANCELLED
            )
        ).scalar()
        
        # Peak booking hours
        peak_hours = self.session.query(
            func.extract('hour', self.model.booking_datetime).label('hour'),
            func.count(self.model.id).label('count')
        ).filter(
            and_(
                func.date(self.model.booking_datetime) >= start_date,
                func.date(self.model.booking_datetime) <= end_date,
                self.model.status != BookingStatus.CANCELLED
            )
        ).group_by('hour').order_by(text('count DESC')).limit(5).all()
        
        return {
            "total_bookings": total_bookings,
            "status_breakdown": {status.value: count for status, count in status_stats},
            "average_party_size": float(avg_party_size) if avg_party_size else 0,
            "peak_hours": [
                {"hour": int(hour), "booking_count": count}
                for hour, count in peak_hours
            ]
        }
    
    def get_customer_booking_history(
        self,
        customer_id: int,
        limit: Optional[int] = 50
    ) -> Dict[str, Any]:
        """Get comprehensive booking history for a customer"""
        # Total bookings
        total_bookings = self.session.query(func.count(self.model.id)).filter(
            self.model.customer_id == customer_id
        ).scalar()
        
        # Recent bookings
        recent_bookings = self.find_by_customer_id(
            customer_id, 
            limit=limit, 
            include_cancelled=True
        )
        
        # Booking patterns
        status_counts = self.session.query(
            self.model.status,
            func.count(self.model.id)
        ).filter(
            self.model.customer_id == customer_id
        ).group_by(self.model.status).all()
        
        # Average party size for this customer
        avg_party_size = self.session.query(func.avg(self.model.party_size)).filter(
            and_(
                self.model.customer_id == customer_id,
                self.model.status != BookingStatus.CANCELLED
            )
        ).scalar()
        
        # Cancellation rate
        total_completed = sum(
            count for status, count in status_counts 
            if status in [BookingStatus.COMPLETED, BookingStatus.CONFIRMED]
        )
        total_cancelled = sum(
            count for status, count in status_counts 
            if status == BookingStatus.CANCELLED
        )
        
        cancellation_rate = (
            (total_cancelled / (total_completed + total_cancelled)) * 100
            if (total_completed + total_cancelled) > 0 else 0
        )
        
        return {
            "customer_id": customer_id,
            "total_bookings": total_bookings,
            "recent_bookings": [
                {
                    "id": booking.id,
                    "booking_datetime": booking.booking_datetime.isoformat(),
                    "party_size": booking.party_size,
                    "status": booking.status.value,
                    "special_requests": booking.special_requests
                }
                for booking in recent_bookings
            ],
            "status_breakdown": {status.value: count for status, count in status_counts},
            "average_party_size": float(avg_party_size) if avg_party_size else 0,
            "cancellation_rate": round(cancellation_rate, 2)
        }
    
    # Advanced Query Methods
    
    def search_bookings(
        self,
        search_criteria: Dict[str, Any],
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Booking], int]:
        """Advanced booking search with multiple criteria and eager loading"""
        query = self.session.query(self.model).options(
            joinedload(self.model.customer)  # Eager load customer to avoid N+1
        )
        
        # Apply filters based on search criteria
        if "date_range" in search_criteria:
            date_range = search_criteria["date_range"]
            if "start_date" in date_range:
                query = query.filter(
                    func.date(self.model.booking_datetime) >= date_range["start_date"]
                )
            if "end_date" in date_range:
                query = query.filter(
                    func.date(self.model.booking_datetime) <= date_range["end_date"]
                )
        
        if "status" in search_criteria:
            statuses = search_criteria["status"]
            if isinstance(statuses, list):
                query = query.filter(self.model.status.in_(statuses))
            else:
                query = query.filter(self.model.status == statuses)
        
        if "customer_id" in search_criteria:
            query = query.filter(self.model.customer_id == search_criteria["customer_id"])
        
        if "party_size_range" in search_criteria:
            size_range = search_criteria["party_size_range"]
            if "min_size" in size_range:
                query = query.filter(self.model.party_size >= size_range["min_size"])
            if "max_size" in size_range:
                query = query.filter(self.model.party_size <= size_range["max_size"])
        
        if "special_requests" in search_criteria:
            search_term = search_criteria["special_requests"]
            query = query.filter(
                self.model.special_requests.ilike(f"%{search_term}%")
            )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        bookings = query.order_by(
            self.model.booking_datetime.desc()
        ).offset(offset).limit(page_size).all()
        
        return bookings, total_count