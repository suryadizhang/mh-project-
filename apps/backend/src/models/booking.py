"""
Booking model and related enums
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum
from datetime import datetime
from typing import Optional

from .base import BaseModel

class BookingStatus(str, Enum):
    """Booking status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SEATED = "seated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class Booking(BaseModel):
    """Booking model"""
    __tablename__ = "bookings"
    
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    booking_datetime = Column(DateTime, nullable=False, index=True)
    party_size = Column(Integer, nullable=False)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING, nullable=False, index=True)
    
    # Contact information (may be different from customer profile)
    contact_phone = Column(String(20))
    contact_email = Column(String(255))
    
    # Special requests and notes
    special_requests = Column(Text)
    internal_notes = Column(Text)
    
    # Status timestamps
    confirmed_at = Column(DateTime)
    seated_at = Column(DateTime)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)
    
    # Table assignment
    table_number = Column(String(10))
    
    # Relationships
    customer = relationship("Customer", back_populates="bookings", lazy="select")
    
    def __repr__(self):
        return f"<Booking(id={self.id}, customer_id={self.customer_id}, datetime={self.booking_datetime}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if booking is in an active state"""
        return self.status in [
            BookingStatus.PENDING,
            BookingStatus.CONFIRMED,
            BookingStatus.SEATED
        ]
    
    @property
    def can_be_cancelled(self) -> bool:
        """Check if booking can be cancelled"""
        return self.status in [
            BookingStatus.PENDING,
            BookingStatus.CONFIRMED,
            BookingStatus.SEATED
        ]
    
    @property
    def can_be_confirmed(self) -> bool:
        """Check if booking can be confirmed"""
        return self.status == BookingStatus.PENDING
    
    def get_time_until_booking(self) -> Optional[int]:
        """Get hours until booking (None if past)"""
        if self.booking_datetime <= datetime.utcnow():
            return None
        
        time_diff = self.booking_datetime - datetime.utcnow()
        return int(time_diff.total_seconds() / 3600)