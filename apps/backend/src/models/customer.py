"""
Customer model and related types
ALIGNED WITH PRODUCTION DATABASE (public.customers)
"""

from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text
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
    """
    Customer model - PRODUCTION SCHEMA
    
    This model matches the actual production database structure in public.customers.
    DO NOT modify without corresponding database migration.
    
    Key fields:
    - id: VARCHAR (Stripe/Supabase customer ID, not auto-increment)
    - user_id: VARCHAR (Supabase auth.users reference)
    - stripe_customer_id: VARCHAR (Stripe customer identifier)
    - name: VARCHAR (single field, not first_name/last_name)
    """

    __tablename__ = "customers"

    # Primary identifiers (VARCHAR in production DB)
    id = Column(String, primary_key=True)  # Matches production: VARCHAR, not Integer!
    user_id = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    stripe_customer_id = Column(String, nullable=False, unique=True, index=True)

    # Basic information (single name field in production)
    name = Column(String, nullable=True)  # Production has single 'name', not first_name/last_name
    phone = Column(String, nullable=True)

    # Payment preferences
    preferred_payment_method = Column(String, nullable=True)

    # Financial tracking (Numeric in production for precision)
    total_spent = Column(Numeric(10, 2), default=0, nullable=True)
    zelle_savings = Column(Numeric(10, 2), default=0, nullable=True)

    # Loyalty program
    total_bookings = Column(Integer, default=0, nullable=True)
    loyalty_tier = Column(String, nullable=True)

    # Legacy fields (keep for backward compatibility but not in production DB)
    # These will be handled via computed properties or separate preference tables
    
    # Relationships
    bookings = relationship("Booking", back_populates="customer", lazy="select")
    # TODO: tone_preferences removed - no FK exists in production
    # TODO: Consider adding via separate migration if needed

    def __repr__(self):
        return f"<Customer(id={self.id}, email={self.email}, name={self.name})>"

    @property
    def full_name(self) -> str:
        """Get customer's full name (for backward compatibility)"""
        return self.name or "Unknown"

    @property
    def first_name(self) -> str:
        """Extract first name from full name (for backward compatibility)"""
        if self.name:
            parts = self.name.split()
            return parts[0] if parts else ""
        return ""

    @property
    def last_name(self) -> str:
        """Extract last name from full name (for backward compatibility)"""
        if self.name:
            parts = self.name.split()
            return " ".join(parts[1:]) if len(parts) > 1 else ""
        return ""

