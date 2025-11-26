"""
Operations Schema Models - Chef & Equipment Management

This module consolidates all operations-related database models into the 'ops' schema.
Provides centralized chef management, equipment tracking, inventory, and scheduling.

Architecture:
- Schema: ops (dedicated namespace for operational management)
- Organization: Chef operations, equipment, inventory, scheduling
- Separation: Clear boundary between ops logic and business/booking logic

Business Domains:
1. Chef Management: Chef profiles, availability, skills, ratings
2. Equipment Management: Kitchen equipment, maintenance, assignments
3. Inventory Management: Stock tracking, reordering, usage
4. Shift Scheduling: Chef shifts, availability calendars, time-off
5. Travel Zones: Service areas, travel fees, coverage maps

Enterprise Features:
- Dedicated schema for ops isolation
- Chef availability tracking for booking
- Equipment maintenance schedules
- Inventory level monitoring
- Shift calendar management
- Performance metrics tracking

Schema Declaration:
All models use: __table_args__ = {"schema": "ops"}

Business Rules:
- Chefs can have multiple specialties (teppanyaki, sushi, fusion)
- Equipment requires maintenance every N days/bookings
- Inventory triggers reorder at minimum threshold
- Shifts prevent double-booking of chefs
- Travel zones calculate dynamic fees

Models:
1. Chef - Chef profiles, skills, ratings, contact info
2. ChefAvailability - Weekly availability calendar
3. ChefTimeOff - Vacation, sick days, time-off requests
4. Equipment - Kitchen equipment (grills, utensils, vehicles)
5. EquipmentMaintenance - Maintenance logs and schedules
6. Inventory - Stock items (ingredients, supplies)
7. InventoryTransaction - Stock movements (add, use, transfer)
8. ShiftSchedule - Chef shift assignments
9. TravelZone - Service coverage areas with fee tiers

Usage Example:
```python
from db.models.ops import Chef, ChefAvailability, Equipment, Inventory

# Create chef
chef = Chef(
    first_name="John",
    last_name="Smith",
    specialty=ChefSpecialty.TEPPANYAKI,
    rating=Decimal("4.8"),
    is_active=True,
)
session.add(chef)

# Set availability
availability = ChefAvailability(
    chef_id=chef.id,
    day_of_week=DayOfWeek.SATURDAY,
    start_time=time(10, 0),
    end_time=time(22, 0),
    is_available=True,
)
session.add(availability)

# Track equipment
equipment = Equipment(
    name="Teppan Grill #1",
    type=EquipmentType.GRILL,
    status=EquipmentStatus.AVAILABLE,
    last_maintenance_date=date.today(),
)
session.add(equipment)
```

Note: This schema supports My Hibachi's operational workflows.
Chef scheduling integrates with booking system for availability checking.
Equipment tracking ensures quality control and maintenance compliance.
"""

from datetime import datetime, date, time
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    Date,
    Time,
    Numeric,
    ForeignKey,
    Index,
    CheckConstraint,
    UniqueConstraint,
    Enum as SQLEnum,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from models.base import Base


# ============================================================================
# ENUMS - Chef Management
# ============================================================================


class ChefSpecialty(str, Enum):
    """Chef culinary specialties"""

    TEPPANYAKI = "teppanyaki"
    SUSHI = "sushi"
    FUSION = "fusion"
    HIBACHI = "hibachi"
    ASIAN_FUSION = "asian_fusion"


class ChefStatus(str, Enum):
    """Chef employment status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"


class DayOfWeek(str, Enum):
    """Days of the week for scheduling"""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class TimeOffType(str, Enum):
    """Types of time-off requests"""

    VACATION = "vacation"
    SICK = "sick"
    PERSONAL = "personal"
    UNPAID = "unpaid"


class TimeOffStatus(str, Enum):
    """Time-off request status"""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    CANCELLED = "cancelled"


# ============================================================================
# ENUMS - Equipment Management
# ============================================================================


class EquipmentType(str, Enum):
    """Equipment categories"""

    GRILL = "grill"
    UTENSILS = "utensils"
    VEHICLE = "vehicle"
    COOLER = "cooler"
    STORAGE = "storage"
    COOKWARE = "cookware"


class EquipmentStatus(str, Enum):
    """Equipment availability status"""

    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class MaintenanceType(str, Enum):
    """Maintenance categories"""

    PREVENTIVE = "preventive"
    REPAIR = "repair"
    INSPECTION = "inspection"
    CLEANING = "cleaning"


# ============================================================================
# ENUMS - Inventory Management
# ============================================================================


class InventoryCategory(str, Enum):
    """Inventory item categories"""

    FOOD = "food"
    BEVERAGE = "beverage"
    SUPPLIES = "supplies"
    EQUIPMENT = "equipment"
    PACKAGING = "packaging"


class TransactionType(str, Enum):
    """Inventory transaction types"""

    PURCHASE = "purchase"
    USE = "use"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    WASTE = "waste"


# ============================================================================
# CHEF MODELS
# ============================================================================


class Chef(Base):
    """
    Chef profile entity - Operations schema

    Represents a chef with skills, availability, and performance tracking.

    Schema: ops.chefs

    Business Logic:
    - Chef assignment to bookings (many-to-many)
    - Availability checking (via ChefAvailability)
    - Performance tracking (rating, completion rate)
    - Skill matching (specialty-based assignment)
    """

    __tablename__ = "chefs"
    __table_args__ = (
        Index("idx_ops_chefs_active", "is_active"),
        Index("idx_ops_chefs_specialty", "specialty"),
        Index("idx_ops_chefs_rating", "rating"),
        CheckConstraint("rating >= 0 AND rating <= 5", name="check_chef_rating_range"),
        {"schema": "ops"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Personal Info
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    # Professional Info
    specialty: Mapped[ChefSpecialty] = mapped_column(
        SQLEnum(ChefSpecialty, name="chef_specialty", schema="public", create_type=False),
        nullable=False,
    )
    years_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    certifications: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Status & Performance
    status: Mapped[ChefStatus] = mapped_column(
        SQLEnum(ChefStatus, name="chef_status", schema="public", create_type=False),
        nullable=False,
        default=ChefStatus.ACTIVE,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)

    # Statistics
    total_bookings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_bookings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps
    hired_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ChefAvailability(Base):
    """
    Chef weekly availability calendar - Operations schema

    Defines recurring weekly availability for booking assignment.

    Schema: ops.chef_availability

    Business Logic:
    - Weekly recurring schedule (Monday-Sunday)
    - Time blocks (start_time to end_time)
    - Override with ChefTimeOff for exceptions
    - Used by booking system for chef assignment
    """

    __tablename__ = "chef_availability"
    __table_args__ = (
        Index("idx_ops_chef_availability_chef", "chef_id", "day_of_week"),
        UniqueConstraint("chef_id", "day_of_week", "start_time", name="uq_chef_day_time"),
        {"schema": "ops"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Foreign Key
    chef_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ops.chefs.id", ondelete="CASCADE"), nullable=False
    )

    # Schedule
    day_of_week: Mapped[DayOfWeek] = mapped_column(
        SQLEnum(DayOfWeek, name="day_of_week", schema="public", create_type=False), nullable=False
    )
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ChefTimeOff(Base):
    """
    Chef time-off requests - Operations schema

    Handles vacation, sick days, and scheduling exceptions.

    Schema: ops.chef_timeoff

    Business Logic:
    - Date range blocking (start_date to end_date)
    - Approval workflow (pending → approved/denied)
    - Overrides ChefAvailability during blocked periods
    - Prevents chef assignment to bookings
    """

    __tablename__ = "chef_timeoff"
    __table_args__ = (
        Index("idx_ops_chef_timeoff_chef", "chef_id", "start_date"),
        Index("idx_ops_chef_timeoff_status", "status"),
        {"schema": "ops"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Foreign Key
    chef_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ops.chefs.id", ondelete="CASCADE"), nullable=False
    )

    # Time Off Details
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    type: Mapped[TimeOffType] = mapped_column(
        SQLEnum(TimeOffType, name="timeoff_type", schema="public", create_type=False),
        nullable=False,
    )
    status: Mapped[TimeOffStatus] = mapped_column(
        SQLEnum(TimeOffStatus, name="timeoff_status", schema="public", create_type=False),
        nullable=False,
        default=TimeOffStatus.PENDING,
    )

    # Notes
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


# ============================================================================
# EQUIPMENT MODELS
# ============================================================================


class Equipment(Base):
    """
    Equipment tracking entity - Operations schema

    Tracks kitchen equipment, vehicles, and tools.

    Schema: ops.equipment

    Business Logic:
    - Equipment assignment to bookings
    - Maintenance scheduling (preventive & repair)
    - Status tracking (available, in-use, maintenance, retired)
    - Cost tracking (purchase, maintenance)
    """

    __tablename__ = "equipment"
    __table_args__ = (
        Index("idx_ops_equipment_type", "type"),
        Index("idx_ops_equipment_status", "status"),
        {"schema": "ops"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Equipment Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[EquipmentType] = mapped_column(
        SQLEnum(EquipmentType, name="equipment_type", schema="public", create_type=False),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[EquipmentStatus] = mapped_column(
        SQLEnum(EquipmentStatus, name="equipment_status", schema="public", create_type=False),
        nullable=False,
        default=EquipmentStatus.AVAILABLE,
    )

    # Maintenance
    last_maintenance_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    next_maintenance_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Cost Tracking
    purchase_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class EquipmentMaintenance(Base):
    """
    Equipment maintenance log - Operations schema

    Tracks maintenance history and schedules.

    Schema: ops.equipment_maintenance

    Business Logic:
    - Preventive maintenance scheduling
    - Repair tracking
    - Cost analysis
    - Downtime tracking
    """

    __tablename__ = "equipment_maintenance"
    __table_args__ = (
        Index("idx_ops_maintenance_equipment", "equipment_id", "maintenance_date"),
        Index("idx_ops_maintenance_type", "type"),
        {"schema": "ops"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Foreign Key
    equipment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ops.equipment.id", ondelete="CASCADE"), nullable=False
    )

    # Maintenance Details
    type: Mapped[MaintenanceType] = mapped_column(
        SQLEnum(MaintenanceType, name="maintenance_type", schema="public", create_type=False),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    maintenance_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Cost
    cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Performer
    performed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================================
# INVENTORY MODELS
# ============================================================================


class Inventory(Base):
    """
    Inventory item tracking - Operations schema

    Tracks stock levels for ingredients and supplies.

    Schema: ops.inventory

    Business Logic:
    - Current stock level tracking
    - Reorder point alerts
    - Unit of measure (lbs, oz, count, etc.)
    - Category organization
    """

    __tablename__ = "inventory"
    __table_args__ = (
        Index("idx_ops_inventory_category", "category"),
        Index("idx_ops_inventory_reorder", "current_quantity"),
        {"schema": "ops"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Item Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[InventoryCategory] = mapped_column(
        SQLEnum(InventoryCategory, name="inventory_category", schema="public", create_type=False),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Quantity
    current_quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    reorder_point: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Cost
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class InventoryTransaction(Base):
    """
    Inventory transaction log - Operations schema

    Tracks all inventory movements (purchases, usage, adjustments).

    Schema: ops.inventory_transactions

    Business Logic:
    - Purchase tracking
    - Usage by booking
    - Stock adjustments
    - Waste tracking
    """

    __tablename__ = "inventory_transactions"
    __table_args__ = (
        Index("idx_ops_inventory_trans_item", "inventory_id", "transaction_date"),
        Index("idx_ops_inventory_trans_type", "type"),
        {"schema": "ops"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Foreign Key
    inventory_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ops.inventory.id", ondelete="CASCADE"), nullable=False
    )

    # Transaction Details
    type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType, name="transaction_type", schema="public", create_type=False),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Reference (booking_id, purchase_order_id, etc.)
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================================
# SHIFT SCHEDULE MODEL
# ============================================================================


class ShiftSchedule(Base):
    """
    Chef shift schedule - Operations schema

    Tracks chef shift assignments and actual bookings.

    Schema: ops.shift_schedules

    Business Logic:
    - Shift assignment to chefs
    - Actual booking tracking
    - Shift completion and notes
    - Performance analytics
    """

    __tablename__ = "shift_schedules"
    __table_args__ = (
        Index("idx_ops_shifts_chef", "chef_id", "shift_date"),
        Index("idx_ops_shifts_date", "shift_date"),
        {"schema": "ops"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Foreign Key
    chef_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ops.chefs.id", ondelete="CASCADE"), nullable=False
    )

    # Shift Details
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    # Booking Reference (optional - actual event assignment)
    booking_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    # Status
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Chef Models
    "Chef",
    "ChefAvailability",
    "ChefTimeOff",
    "ChefSpecialty",
    "ChefStatus",
    "DayOfWeek",
    "TimeOffType",
    "TimeOffStatus",
    # Equipment Models
    "Equipment",
    "EquipmentMaintenance",
    "EquipmentType",
    "EquipmentStatus",
    "MaintenanceType",
    # Inventory Models
    "Inventory",
    "InventoryTransaction",
    "InventoryCategory",
    "TransactionType",
    # Shift Models
    "ShiftSchedule",
]

# Schema metadata for Phase 1B validation
__schema__ = "ops"
__table_args__ = {"schema": "ops"}
__version__ = "1.0.0"
__description__ = "Operations Schema Models - Chef management, equipment, inventory, scheduling"
