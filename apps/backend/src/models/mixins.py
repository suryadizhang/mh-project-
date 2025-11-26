"""
SQLAlchemy Model Mixins - Enterprise Pattern

Composable mixins for building scalable database models.
Follows Django, Rails, and FastAPI best practices for model composition.

Architecture Benefits:
- Flexible composition vs rigid inheritance
- Clean separation of concerns
- Scalable for multi-tenant, white-label, sharding
- No override anti-patterns
- Industry-standard approach

Usage:
    from models.mixins import UUIDPKMixin, TimestampMixin, SoftDeleteTimestampMixin

    class Booking(Base, UUIDPKMixin, TimestampMixin, SoftDeleteTimestampMixin):
        __tablename__ = "bookings"
        # Only booking-specific fields here
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa


# ═══════════════════════════════════════════════════════════════════════════
# PRIMARY KEY MIXINS
# ═══════════════════════════════════════════════════════════════════════════


class IntegerPKMixin:
    """Integer primary key for traditional/legacy tables.

    Use when:
    - Legacy database compatibility required
    - Sequential IDs needed (invoices, receipts)
    - Single-database deployment

    Examples: Customer, Payment, EmailMessage, Lead
    """
    id = Column(Integer, primary_key=True, index=True)


class UUIDPKMixin:
    """UUID primary key for distributed systems.

    Use when:
    - Multi-region/distributed database
    - Avoiding ID collision across systems
    - Exposing IDs in URLs (security)
    - Sharding/partitioning planned

    Examples: Booking, Station, DomainEvent

    Note: PostgreSQL gen_random_uuid() used for performance
    """
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
        index=True
    )


# ═══════════════════════════════════════════════════════════════════════════
# TIMESTAMP MIXINS
# ═══════════════════════════════════════════════════════════════════════════


class TimestampMixin:
    """Add created_at and updated_at timestamps.

    Use for: ALL models (standard audit trail)

    Timezone-aware timestamps using UTC for consistency.
    updated_at automatically updates on row modification.
    """
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


# ═══════════════════════════════════════════════════════════════════════════
# SOFT DELETE MIXINS
# ═══════════════════════════════════════════════════════════════════════════


class SoftDeleteBooleanMixin:
    """Soft delete with Boolean flag (simple hide/show).

    Use when:
    - Simple visibility toggle needed
    - Don't need deletion timestamp
    - Legacy compatibility required

    Examples: Customer, EmailMessage, Lead

    Query pattern:
        .filter(Model.is_deleted == False)
    """
    is_deleted = Column(Boolean, default=False, nullable=False)


class SoftDeleteTimestampMixin:
    """Soft delete with timestamp (audit trail).

    Use when:
    - Need deletion timestamp for audit/compliance
    - Want to track WHO deleted and WHEN
    - GDPR/compliance requirements

    Examples: Booking, Payment, Transaction

    Query pattern:
        .filter(Model.deleted_at.is_(None))

    Benefits over Boolean:
    - Audit trail (when deleted)
    - Can track deleted_by with AuditableMixin
    - Restore capability with timestamp preservation
    """
    deleted_at = Column(DateTime(timezone=True), nullable=True)


# ═══════════════════════════════════════════════════════════════════════════
# MULTI-TENANT MIXINS (For Future Scalability)
# ═══════════════════════════════════════════════════════════════════════════


class StationTenantMixin:
    """Multi-station tenant isolation.

    Use when:
    - Table needs station-level data isolation
    - Row-Level Security (RLS) policies required
    - Multi-location business model

    Examples: Booking, Customer, MessageThread

    Prerequisites:
    - Requires identity.stations table (Migration 004)
    - Enable RLS policies for isolation

    Future: Sharding key for horizontal scaling
    """
    station_id = Column(
        UUID(as_uuid=True),
        # ForeignKey will be added when needed: ForeignKey("identity.stations.id")
        nullable=False,
        index=True,
        comment="Station tenant isolation - for multi-location scaling"
    )


class BusinessTenantMixin:
    """White-label business tenant isolation.

    Use when:
    - Table needs business-level data isolation
    - White-label SaaS deployment
    - Multi-business platform

    Examples: User, Booking, Lead, EmailTemplate

    Prerequisites:
    - Requires businesses table (see WHITE_LABEL_PREPARATION_GUIDE.md)

    Note: Some models may need BOTH StationTenantMixin AND BusinessTenantMixin
    """
    business_id = Column(
        UUID(as_uuid=True),
        # ForeignKey will be added when needed: ForeignKey("businesses.id")
        nullable=False,
        index=True,
        comment="Business tenant isolation - for white-label SaaS"
    )


# ═══════════════════════════════════════════════════════════════════════════
# AUDIT TRAIL MIXIN (For Compliance/Security)
# ═══════════════════════════════════════════════════════════════════════════


class AuditableMixin:
    """Full audit trail with user tracking.

    Use when:
    - Need to track WHO made changes
    - Compliance/regulatory requirements
    - Financial/payment models
    - Admin operations tracking

    Examples: Payment, Booking, UserRole, StationConfig

    Combines with SoftDeleteTimestampMixin for complete audit:
    - created_by + created_at
    - updated_by + updated_at
    - deleted_by + deleted_at (if using SoftDeleteTimestampMixin)

    Query pattern:
        booking.created_by.email  # Get creator email
        booking.updated_by.name   # Get last editor name
    """
    created_by = Column(
        UUID(as_uuid=True),
        # ForeignKey will be added when needed: ForeignKey("identity.users.id")
        nullable=True,
        comment="User who created this record"
    )
    updated_by = Column(
        UUID(as_uuid=True),
        # ForeignKey will be added when needed: ForeignKey("identity.users.id")
        nullable=True,
        comment="User who last updated this record"
    )
    # Note: Add deleted_by when combining with SoftDeleteTimestampMixin


# ═══════════════════════════════════════════════════════════════════════════
# OPTIMISTIC LOCKING MIXIN (For Concurrency)
# ═══════════════════════════════════════════════════════════════════════════


class OptimisticLockMixin:
    """Version column for optimistic locking.

    Use when:
    - Concurrent updates expected (booking, inventory)
    - Need to prevent lost updates
    - Race condition protection

    Examples: Booking (Bug #13 fix), Inventory, Seat

    SQLAlchemy automatically increments version on UPDATE.
    Raises StaleDataError if version mismatch detected.

    Pattern:
        booking.version = 1  # Initial
        # User A reads booking (version=1)
        # User B reads booking (version=1)
        # User A updates → version=2 ✅
        # User B updates → StaleDataError ❌ (version mismatch)
    """
    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Optimistic lock version - incremented on each UPDATE"
    )


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE COMPOSITIONS
# ═══════════════════════════════════════════════════════════════════════════

"""
Example 1: Modern Booking (UUID, timestamp soft-delete, optimistic lock)
--------------------------------------------------------------------------
from models.base import Base
from models.mixins import (
    UUIDPKMixin, TimestampMixin, SoftDeleteTimestampMixin,
    OptimisticLockMixin, StationTenantMixin
)

class Booking(Base, UUIDPKMixin, TimestampMixin,
              SoftDeleteTimestampMixin, OptimisticLockMixin, StationTenantMixin):
    __tablename__ = "bookings"
    __table_args__ = {'schema': 'core'}

    # Only booking-specific fields:
    customer_id = Column(UUID, ForeignKey("customers.id"))
    date = Column(Date, nullable=False)
    slot = Column(Time, nullable=False)
    # ...


Example 2: Legacy Customer (Integer ID, boolean soft-delete)
-------------------------------------------------------------
from models.base import Base
from models.mixins import IntegerPKMixin, TimestampMixin, SoftDeleteBooleanMixin

class Customer(Base, IntegerPKMixin, TimestampMixin, SoftDeleteBooleanMixin):
    __tablename__ = "customers"

    # Only customer-specific fields:
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    # ...


Example 3: Auditable Payment (track who created/updated)
---------------------------------------------------------
from models.base import Base
from models.mixins import (
    IntegerPKMixin, TimestampMixin, SoftDeleteTimestampMixin, AuditableMixin
)

class Payment(Base, IntegerPKMixin, TimestampMixin,
              SoftDeleteTimestampMixin, AuditableMixin):
    __tablename__ = "payments"

    # Gets: id, created_at, updated_at, deleted_at, created_by, updated_by
    amount = Column(Numeric(10, 2), nullable=False)
    # ...


Example 4: White-Label User (business + station isolation)
-----------------------------------------------------------
from models.base import Base
from models.mixins import (
    UUIDPKMixin, TimestampMixin, SoftDeleteBooleanMixin,
    BusinessTenantMixin, StationTenantMixin, AuditableMixin
)

class User(Base, UUIDPKMixin, TimestampMixin, SoftDeleteBooleanMixin,
           BusinessTenantMixin, StationTenantMixin, AuditableMixin):
    __tablename__ = "users"
    __table_args__ = {'schema': 'identity'}

    # Gets: id, created_at, updated_at, is_deleted, business_id, station_id,
    #       created_by, updated_by
    email = Column(String(255), unique=True, nullable=False)
    # ...
"""
