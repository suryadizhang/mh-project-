import enum
import uuid

from sqlalchemy import Boolean, Column, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UserRole(str, enum.Enum):
    """User roles in the system."""

    CUSTOMER = "customer"
    ADMIN = "admin"
    CHEF = "chef"


class BookingStatus(str, enum.Enum):
    """Booking status options."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class TimeSlotEnum(str, enum.Enum):
    """Available time slots for bookings."""

    SLOT_12PM = "12PM"
    SLOT_3PM = "3PM"
    SLOT_6PM = "6PM"
    SLOT_9PM = "9PM"


class PreferredCommunication(str, enum.Enum):
    """Preferred communication methods."""

    PHONE = "phone"
    TEXT = "text"
    EMAIL = "email"


class User(Base):
    """User model for authentication and profile management."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    bookings = relationship("Booking", back_populates="user")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class TimeSlotConfiguration(Base):
    """Configuration for available time slots."""

    __tablename__ = "time_slot_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    time_slot = Column(SQLEnum(TimeSlotEnum), nullable=False, unique=True)
    max_capacity = Column(Integer, nullable=False, default=2)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Booking(Base):
    """Main booking model linking all booking information."""

    __tablename__ = "bookings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_reference = Column(
        String(50), unique=True, nullable=False, index=True
    )  # e.g., MH-20250828-EF56

    # User information
    user_id = Column(
        String, ForeignKey("users.id"), nullable=True
    )  # Nullable for guest bookings
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_phone = Column(String(20), nullable=False)
    preferred_communication = Column(
        SQLEnum(PreferredCommunication), nullable=True
    )

    # Event details
    event_date = Column(Date, nullable=False)
    event_time = Column(SQLEnum(TimeSlotEnum), nullable=False)
    guest_count = Column(Integer, nullable=False)

    # Venue address
    venue_street = Column(String(255), nullable=False)
    venue_city = Column(String(100), nullable=False)
    venue_state = Column(String(2), nullable=False)
    venue_zipcode = Column(String(10), nullable=False)

    # Billing address (if different from venue)
    billing_street = Column(String(255), nullable=True)
    billing_city = Column(String(100), nullable=True)
    billing_state = Column(String(2), nullable=True)
    billing_zipcode = Column(String(10), nullable=True)
    same_as_venue = Column(Boolean, default=True)

    # Booking status and financials
    status = Column(
        SQLEnum(BookingStatus), nullable=False, default=BookingStatus.PENDING
    )
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    deposit_amount = Column(Numeric(10, 2), nullable=False, default=100.00)
    deposit_paid = Column(Boolean, default=False)
    remaining_balance = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Additional information
    special_requests = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)  # Admin notes

    # Travel information
    travel_distance_miles = Column(Numeric(5, 2), nullable=True)
    travel_fee = Column(Numeric(8, 2), nullable=True, default=0.00)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="bookings")
    menu_items = relationship(
        "BookingMenuItem",
        back_populates="booking",
        cascade="all, delete-orphan",
    )
    addons = relationship(
        "BookingAddon", back_populates="booking", cascade="all, delete-orphan"
    )

    @property
    def venue_address(self):
        return {
            "street": self.venue_street,
            "city": self.venue_city,
            "state": self.venue_state,
            "zipcode": self.venue_zipcode,
        }

    @property
    def billing_address(self):
        if self.same_as_venue:
            return self.venue_address
        return {
            "street": self.billing_street,
            "city": self.billing_city,
            "state": self.billing_state,
            "zipcode": self.billing_zipcode,
        }


class MenuItem(Base):
    """Base menu items available for booking."""

    __tablename__ = "menu_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    base_price = Column(Numeric(8, 2), nullable=False)
    category = Column(
        String(100), nullable=False
    )  # "Adult Menu", "Kids Menu", etc.
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AddonItem(Base):
    """Available addon items for bookings."""

    __tablename__ = "addon_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(8, 2), nullable=False)
    category = Column(
        String(100), nullable=False
    )  # "Protein Upgrades", "Equipment", etc.
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BookingMenuItem(Base):
    """Junction table for booking menu items with quantities."""

    __tablename__ = "booking_menu_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=False)
    menu_item_id = Column(String, ForeignKey("menu_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(
        Numeric(8, 2), nullable=False
    )  # Price at time of booking
    total_price = Column(
        Numeric(8, 2), nullable=False
    )  # quantity * unit_price

    # Relationships
    booking = relationship("Booking", back_populates="menu_items")
    menu_item = relationship("MenuItem")


class BookingAddon(Base):
    """Junction table for booking addons with quantities."""

    __tablename__ = "booking_addons"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=False)
    addon_item_id = Column(
        String, ForeignKey("addon_items.id"), nullable=False
    )
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(
        Numeric(8, 2), nullable=False
    )  # Price at time of booking
    total_price = Column(
        Numeric(8, 2), nullable=False
    )  # quantity * unit_price

    # Relationships
    booking = relationship("Booking", back_populates="addons")
    addon_item = relationship("AddonItem")


class BookingAvailability(Base):
    """Track available slots for each date and time."""

    __tablename__ = "booking_availability"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(Date, nullable=False)
    time_slot = Column(SQLEnum(TimeSlotEnum), nullable=False)
    max_capacity = Column(Integer, nullable=False, default=2)
    booked_count = Column(Integer, nullable=False, default=0)
    is_available = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def available_slots(self):
        return max(0, self.max_capacity - self.booked_count)


# Create performance indexes
Index("idx_bookings_date_time", Booking.event_date, Booking.event_time)
Index("idx_bookings_status_date", Booking.status, Booking.event_date)
Index("idx_bookings_customer_email", Booking.customer_email)
Index("idx_bookings_reference", Booking.booking_reference)
Index(
    "idx_booking_availability_date_time",
    BookingAvailability.date,
    BookingAvailability.time_slot,
)
Index("idx_users_email", User.email)
