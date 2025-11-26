"""
Customer model and related types

⚠️ DEPRECATED: This is the LEGACY customer model mapping to public.customers

For NEW code, use: from db.models.core import Customer
Production table: core.customers (schema-qualified, modern architecture)

This model will be removed in a future version after full migration.
See: CUSTOMER_MODEL_DUPLICATION_ANALYSIS.md for migration plan
"""

from enum import Enum
import warnings

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
    """Customer model

    ⚠️ DEPRECATED: Use db.models.core.Customer for new code
    This legacy model maps to public.customers (deprecated table)
    Production uses core.customers (schema-qualified)
    """

    __tablename__ = "customers"
    __table_args__ = {"extend_existing": True}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        warnings.warn(
            "models.customer.Customer is deprecated. Use db.models.core.Customer instead.",
            DeprecationWarning,
            stacklevel=2
        )

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
    sms_notifications = Column(Boolean, default=True)
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

    # Relationships (temporarily commented bookings for Bug #13 schema fixes)
    # Use fully-qualified module path to avoid "Multiple classes found for path 'Booking'" error
    # This explicitly references models.booking.Booking, not legacy_core.Booking
    # bookings = relationship("models.booking.Booking", back_populates="customer", lazy="select")
    escalations = relationship("Escalation", back_populates="customer", lazy="select", cascade="all, delete-orphan")
    # Note: tone_preferences relationship removed due to cross-registry incompatibility
    # CustomerTonePreference uses models.base.Base, Customer uses models.base.BaseModel (same Base but registered differently)
    # Access tone preferences directly via query: session.query(CustomerTonePreference).filter_by(customer_id=customer.id)
    terms_acknowledgments = relationship("TermsAcknowledgment", back_populates="customer", lazy="select")

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
