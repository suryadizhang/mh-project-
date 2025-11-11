"""
Customer model and related types
"""

from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import BaseModel


class CustomerStatus(str, Enum):
    """Customer status enumeration"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    VIP = "vip"


class CustomerPreference(str, Enum):
    """Customer dining preferences"""

    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    NUT_ALLERGY = "nut_allergy"
    SHELLFISH_ALLERGY = "shellfish_allergy"


class Customer(BaseModel):
    """Customer model"""

    __tablename__ = "customers"

    # Basic information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), index=True)

    # Status and preferences
    status = Column(SQLEnum(CustomerStatus), default=CustomerStatus.ACTIVE, nullable=False)
    dietary_preferences = Column(Text)  # JSON string of preferences
    special_notes = Column(Text)

    # Communication preferences
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    marketing_emails = Column(Boolean, default=True)

    # Profile completion
    date_of_birth = Column(DateTime)
    anniversary_date = Column(DateTime)

    # Loyalty information
    loyalty_points = Column(Integer, default=0)
    total_visits = Column(Integer, default=0)
    total_spent = Column(Integer, default=0)  # in cents

    # Last activity
    last_booking_date = Column(DateTime)
    last_visit_date = Column(DateTime)

    # Relationships
    bookings = relationship("Booking", back_populates="customer", lazy="select")

    def __repr__(self):
        return f"<Customer(id={self.id}, email={self.email}, name={self.full_name})>"

    @property
    def full_name(self) -> str:
        """Get customer's full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_active(self) -> bool:
        """Check if customer is active"""
        return self.status == CustomerStatus.ACTIVE

    @property
    def is_vip(self) -> bool:
        """Check if customer has VIP status"""
        return self.status == CustomerStatus.VIP

    def get_dietary_preferences_list(self) -> list[str]:
        """Parse dietary preferences from JSON string"""
        import json

        try:
            if self.dietary_preferences:
                return json.loads(self.dietary_preferences)
        except (json.JSONDecodeError, TypeError):
            pass
        return []

    def set_dietary_preferences(self, preferences: list[str]):
        """Set dietary preferences as JSON string"""
        import json

        self.dietary_preferences = json.dumps(preferences) if preferences else None

    def add_loyalty_points(self, points: int):
        """Add loyalty points to customer account"""
        self.loyalty_points = (self.loyalty_points or 0) + points

    def can_receive_notifications(self, notification_type: str = "email") -> bool:
        """Check if customer can receive notifications"""
        if notification_type == "email":
            return self.email_notifications and self.status != CustomerStatus.SUSPENDED
        elif notification_type == "sms":
            return self.sms_notifications and self.phone and self.status != CustomerStatus.SUSPENDED
        return False
