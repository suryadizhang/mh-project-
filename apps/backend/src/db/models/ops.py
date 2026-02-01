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

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID

from sqlalchemy import ARRAY, Boolean, CheckConstraint, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

# MIGRATED: from models.base → ..base_class (NEW unified architecture)
from ..base_class import Base

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


class PayRateClass(str, Enum):
    """
    Chef pay rate classification for earnings calculation.

    Each tier has FIXED per-person rates (NOT a multiplier system):
    - NEW_CHEF (Junior): $10/adult, $5/kid, $0/toddler
    - CHEF (Standard): $12/adult, $6/kid, $0/toddler
    - SENIOR_CHEF (Senior): $13/adult, $6.50/kid, $0/toddler
    - STATION_MANAGER (Backup): $15/adult, $7.50/kid, $0/toddler

    Managed by super admin via SSoT UI (dynamic_variables table).
    """

    NEW_CHEF = "new_chef"  # Junior: $10/adult, $5/kid
    CHEF = "chef"  # Standard: $12/adult, $6/kid
    SENIOR_CHEF = "senior_chef"  # Senior: $13/adult, $6.50/kid
    STATION_MANAGER = "station_manager"  # Manager: $15/adult, $7.50/kid


class SeniorityLevel(str, Enum):
    """
    Chef seniority level for performance tracking.

    Performance-based rating assigned by admin after reviewing scores.
    Does NOT affect pay directly - only pay_rate_class affects pay.
    Used for reporting, skill matching, and manual level assignment.
    """

    JUNIOR = "junior"
    STANDARD = "standard"
    SENIOR = "senior"
    EXPERT = "expert"


class ScoreRaterType(str, Enum):
    """Who rated the chef"""

    CUSTOMER = "customer"
    ADMIN = "admin"
    STATION_MANAGER = "station_manager"
    SYSTEM = "system"  # Auto-generated scores


class EarningsStatus(str, Enum):
    """Status of chef earnings record"""

    PENDING = "pending"  # Event not yet completed
    CALCULATED = "calculated"  # Auto-calculated after event
    ADJUSTED = "adjusted"  # Manually adjusted by admin
    PAID = "paid"  # Payment processed
    DISPUTED = "disputed"  # Under review


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
        SQLEnum(
            ChefSpecialty, name="chef_specialty", schema="public", create_type=False
        ),
        nullable=False,
    )
    years_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    certifications: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )

    # Status & Performance
    status: Mapped[ChefStatus] = mapped_column(
        SQLEnum(ChefStatus, name="chef_status", schema="public", create_type=False),
        nullable=False,
        default=ChefStatus.ACTIVE,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)

    # Pay Rate System (SSoT: chef_pay category)
    pay_rate_class: Mapped[PayRateClass] = mapped_column(
        SQLEnum(
            PayRateClass, name="pay_rate_class", schema="public", create_type=False
        ),
        nullable=False,
        default=PayRateClass.NEW_CHEF,
        comment="Pay multiplier: NEW_CHEF=80%, CHEF=100%, SENIOR_CHEF=115%",
    )
    seniority_level: Mapped[SeniorityLevel] = mapped_column(
        SQLEnum(
            SeniorityLevel, name="seniority_level", schema="public", create_type=False
        ),
        nullable=False,
        default=SeniorityLevel.JUNIOR,
        comment="Performance-based level assigned by admin after reviewing scores",
    )

    # Statistics
    total_bookings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_bookings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps
    hired_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
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
        UniqueConstraint(
            "chef_id", "day_of_week", "start_time", name="uq_chef_day_time"
        ),
        {"schema": "ops"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Foreign Key
    chef_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ops.chefs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Schedule
    day_of_week: Mapped[DayOfWeek] = mapped_column(
        SQLEnum(DayOfWeek, name="day_of_week", schema="public", create_type=False),
        nullable=False,
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
        PGUUID(as_uuid=True),
        ForeignKey("ops.chefs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Time Off Details
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    type: Mapped[TimeOffType] = mapped_column(
        SQLEnum(TimeOffType, name="timeoff_type", schema="public", create_type=False),
        nullable=False,
    )
    status: Mapped[TimeOffStatus] = mapped_column(
        SQLEnum(
            TimeOffStatus, name="timeoff_status", schema="public", create_type=False
        ),
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
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ============================================================================
# CHEF PAY SYSTEM MODELS
# ============================================================================


class ChefScore(Base):
    """
    Individual chef performance scores - Operations schema

    Stores every score from every rater for complete history.
    Admin views all scores, then manually assigns seniority level.

    Schema: ops.chef_scores

    Business Logic:
    - Track individual ratings from customers, admin, station managers
    - Used for performance review and seniority level decisions
    - Does NOT auto-calculate level - admin decides manually
    - Immutable records (no updates, only inserts)
    """

    __tablename__ = "chef_scores"
    __table_args__ = (
        Index("idx_chef_scores_chef_id", "chef_id"),
        Index("idx_chef_scores_booking_id", "booking_id"),
        Index("idx_chef_scores_rater_type", "rater_type"),
        Index("idx_chef_scores_scored_at", "scored_at"),
        CheckConstraint("score >= 1 AND score <= 5", name="check_score_range"),
        {"schema": "ops"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Foreign Keys
    chef_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ops.chefs.id", ondelete="CASCADE"),
        nullable=False,
    )
    booking_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.bookings.id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional - some scores may be admin-assigned without booking",
    )

    # Score Details
    score: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        comment="Score from 1.00 to 5.00",
    )
    rater_type: Mapped[ScoreRaterType] = mapped_column(
        SQLEnum(
            ScoreRaterType, name="score_rater_type", schema="public", create_type=False
        ),
        nullable=False,
    )
    rater_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="User ID of rater (if authenticated)",
    )
    rater_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Name for display (customer name or admin name)",
    )

    # Feedback
    comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional feedback text",
    )
    categories: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Breakdown scores: {food_quality: 5, presentation: 4, timeliness: 5}",
    )

    # Timestamps (immutable - no updated_at)
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class ChefEarnings(Base):
    """
    Chef earnings per booking - Operations schema

    Detailed breakdown of chef payment for each event.
    Formula: (adults × $13) + (kids × $6.50) + (toddlers × $0) + travel_fee
    Pay rate multiplier applied based on pay_rate_class.

    Schema: ops.chef_earnings

    Business Logic:
    - Auto-calculated after event completion
    - Shows detailed breakdown: cooking_fee, travel_fee, base_total, multiplier, final_amount
    - Headcount-based split when multiple chefs assigned
    - Status tracks payment lifecycle: pending → calculated → paid
    - Only station manager and admin can view pay details
    """

    __tablename__ = "chef_earnings"
    __table_args__ = (
        Index("idx_chef_earnings_chef_id", "chef_id"),
        Index("idx_chef_earnings_booking_id", "booking_id"),
        Index("idx_chef_earnings_status", "status"),
        Index("idx_chef_earnings_calculated_at", "calculated_at"),
        UniqueConstraint("chef_id", "booking_id", name="uq_chef_booking_earnings"),
        {"schema": "ops"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Foreign Keys
    chef_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ops.chefs.id", ondelete="CASCADE"),
        nullable=False,
    )
    booking_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.bookings.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Headcount at time of event (snapshot for historical accuracy)
    adults_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of adults (13+) at event",
    )
    children_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of children (6-12) at event",
    )
    toddlers_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of toddlers (under 6) at event - $0 rate",
    )
    total_chefs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Total chefs assigned - for split calculation",
    )

    # Earnings Breakdown (all amounts in cents)
    cooking_fee_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="(adults × adult_rate + kids × kid_rate) / total_chefs",
    )
    travel_fee_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="100% of travel fee to chef (not split)",
    )
    base_total_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="cooking_fee + travel_fee before multiplier",
    )

    # Pay Rate Applied
    pay_rate_class: Mapped[PayRateClass] = mapped_column(
        SQLEnum(
            PayRateClass, name="pay_rate_class", schema="public", create_type=False
        ),
        nullable=False,
        comment="Chef's pay rate class at time of event",
    )
    rate_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        comment="Multiplier applied: 0.80, 1.00, or 1.15",
    )
    final_amount_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="base_total × rate_multiplier = final chef payment",
    )

    # Status
    status: Mapped[EarningsStatus] = mapped_column(
        SQLEnum(
            EarningsStatus, name="earnings_status", schema="public", create_type=False
        ),
        nullable=False,
        default=EarningsStatus.PENDING,
    )

    # Adjustment tracking
    adjustment_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for manual adjustment if status=ADJUSTED",
    )
    adjusted_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Admin/manager who made adjustment",
    )

    # Timestamps
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


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
        SQLEnum(
            EquipmentType, name="equipment_type", schema="public", create_type=False
        ),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[EquipmentStatus] = mapped_column(
        SQLEnum(
            EquipmentStatus, name="equipment_status", schema="public", create_type=False
        ),
        nullable=False,
        default=EquipmentStatus.AVAILABLE,
    )

    # Maintenance
    last_maintenance_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    next_maintenance_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Cost Tracking
    purchase_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
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
        PGUUID(as_uuid=True),
        ForeignKey("ops.equipment.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Maintenance Details
    type: Mapped[MaintenanceType] = mapped_column(
        SQLEnum(
            MaintenanceType, name="maintenance_type", schema="public", create_type=False
        ),
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
        SQLEnum(
            InventoryCategory,
            name="inventory_category",
            schema="public",
            create_type=False,
        ),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Quantity
    current_quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    reorder_point: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    # Cost
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
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
        PGUUID(as_uuid=True),
        ForeignKey("ops.inventory.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Transaction Details
    type: Mapped[TransactionType] = mapped_column(
        SQLEnum(
            TransactionType, name="transaction_type", schema="public", create_type=False
        ),
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
        PGUUID(as_uuid=True),
        ForeignKey("ops.chefs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Shift Details
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    # Booking Reference (optional - actual event assignment)
    booking_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    # Status
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================================
# TRAVEL ZONE MODEL (Phase 2A - Distance Agent)
# ============================================================================


class TravelZone(Base):
    """
    Travel zones with dynamic fee calculation - Operations schema

    Defines service areas with zip codes and travel fee structures.
    Used by Distance Agent for dynamic travel fee calculation.

    Schema: ops.travel_zones

    Business Logic:
    - NO hardcoded travel fees (violates Rule 01)
    - Fees based on zone and distance
    - Supports multiple zip codes per zone
    - Max distance enforcement
    """

    __tablename__ = "travel_zones"
    __table_args__ = (
        Index("idx_ops_travel_zones_active", "is_active"),
        {"schema": "ops"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Zone Details
    name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "Downtown Phoenix"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Coverage (JSONB for flexible zip code lists)
    zip_codes: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=list
    )  # ["85001", "85002", ...]

    # Pricing Structure
    base_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )  # Base travel fee
    per_mile_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("2.00")
    )  # Fee per mile
    max_distance_miles: Mapped[int] = mapped_column(
        Integer, nullable=False, default=50
    )  # Maximum service distance

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# ============================================================================
# MENU ITEM MODEL (Phase 2A - Menu Advisor Agent)
# ============================================================================


class MenuItem(Base):
    """
    Menu items catalog for recommendations - Operations schema

    Menu items with pricing, dietary info, and availability.
    Used by Menu Advisor Agent for dynamic recommendations.

    Schema: ops.menu_items

    Business Logic:
    - NO hardcoded menu prices (violates Rule 01)
    - Dietary tag filtering
    - Seasonal availability
    - Ingredient tracking for allergies
    """

    __tablename__ = "menu_items"
    __table_args__ = (
        Index("idx_ops_menu_items_category", "category"),
        Index("idx_ops_menu_items_available", "is_available"),
        {"schema": "ops"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Item Details
    name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )  # e.g., "Hibachi Chicken"
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "protein", "side", "appetizer", "dessert"

    # Pricing
    base_price_per_person: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )  # Price per person

    # Dietary & Ingredients (JSONB for flexible arrays)
    dietary_tags: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=list
    )  # ["gluten-free", "vegetarian", "vegan"]
    ingredients: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=list
    )  # ["chicken", "soy sauce", "garlic"]

    # Availability
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    seasonal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# ============================================================================
# PRICING RULE MODEL (Phase 2A - Pricing Calculator Agent)
# ============================================================================


class PricingRule(Base):
    """
    Dynamic pricing rules (NO HARDCODED VALUES) - Operations schema

    Defines pricing formulas based on conditions.
    Used by Pricing Calculator Agent for dynamic pricing.

    Schema: ops.pricing_rules

    Business Logic:
    - NO hardcoded prices (violates Rule 01)
    - Condition-based pricing
    - Priority-based conflict resolution
    - Effective date ranges
    """

    __tablename__ = "pricing_rules"
    __table_args__ = (
        Index("idx_ops_pricing_rules_type", "rule_type"),
        Index("idx_ops_pricing_rules_active", "is_active"),
        Index("idx_ops_pricing_rules_priority", "priority"),
        {"schema": "ops"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Rule Details
    rule_name: Mapped[str] = mapped_column(String(200), nullable=False)
    rule_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "base_price", "travel_fee", "discount", "service_fee"

    # Conditions & Formula (JSONB for flexible rules)
    conditions: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )  # {"guest_count": ">10", "day": "weekend"}
    pricing_formula: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )  # {"base": 55, "per_person": 50, "multiplier": 1.2}

    # Effective Dates
    effective_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    effective_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Priority (higher = takes precedence)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# ============================================================================
# ENUMS - Negotiation Incentives (Smart Scheduling Phase 1)
# ============================================================================


class FoodIncentiveType(str, Enum):
    """
    Food-based incentives for time negotiations.

    Strategy: Start with cheapest first (noodles ~$3), then appetizer (~$5).
    NO protein upgrades for negotiation incentives.
    """

    NONE = "none"  # 0-15 min shift - no incentive needed
    FREE_NOODLES = "free_noodles"  # 16-30 min shift - yakisoba noodles for party
    FREE_APPETIZER = (
        "free_appetizer"  # 31+ min shift - edamame or gyoza (customer choice)
    )


# ============================================================================
# MODELS - Negotiation Incentives (Smart Scheduling Phase 1)
# ============================================================================


class NegotiationIncentive(Base):
    """
    Configurable food incentive tiers for time negotiation.

    Business Logic:
    - When asking customer to shift their booking time
    - Offer food incentives proportional to inconvenience
    - NO cash discounts, only food items

    Shift Options & Incentives:
    - ±30 min: Free yakisoba noodles for entire party
    - ±60 min: Free appetizer (edamame or gyoza, customer choice)

    ⚠️ NOTE: actual_cost_usd is per-party estimate for P&L tracking.
    """

    __tablename__ = "negotiation_incentives"
    __table_args__ = {"schema": "ops"}

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Time shift range (in minutes)
    min_shift_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    max_shift_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Incentive type (enum)
    incentive_type: Mapped[FoodIncentiveType] = mapped_column(
        SQLEnum(
            FoodIncentiveType,
            name="food_incentive_type",
            schema="public",
            create_type=False,  # Already created in database
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )

    # Customer-facing description
    incentive_description: Mapped[str] = mapped_column(Text, nullable=False)

    # Cost tracking for P&L
    actual_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), nullable=False, default=0
    )  # What it costs us per party
    perceived_value_usd: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), nullable=False, default=0
    )  # What customer thinks it's worth

    # Status and priority
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

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
    # Chef Pay System
    "PayRateClass",
    "SeniorityLevel",
    "ScoreRaterType",
    "EarningsStatus",
    "ChefScore",
    "ChefEarnings",
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
    # Phase 2A Models (Distance, Menu, Pricing Agents)
    "TravelZone",
    "MenuItem",
    "PricingRule",
    # Smart Scheduling Phase 1 (Negotiation Incentives)
    "NegotiationIncentive",
    "FoodIncentiveType",
]

# Schema metadata for Phase 1B validation
__schema__ = "ops"
__table_args__ = {"schema": "ops"}
__version__ = "1.0.0"
__description__ = (
    "Operations Schema Models - Chef management, equipment, inventory, scheduling"
)
