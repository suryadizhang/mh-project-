"""
Base model classes and common types

CRITICAL: Uses unified Base from core.database to avoid registry conflicts

DEPRECATED: BaseModel is being phased out in favor of mixin composition.

Migration Path:
- NEW models: Use mixins from models.mixins (UUIDPKMixin, TimestampMixin, etc.)
- EXISTING models: Continue using BaseModel for backward compatibility
- REFACTORING: Gradually migrate models to mixins (see Booking model as example)

Why mixins are better:
- Flexible composition vs rigid inheritance
- Supports diverse ID strategies (Integer, UUID, BigInteger)
- Supports diverse soft-delete patterns (Boolean, Timestamp)
- Ready for multi-tenant (StationTenantMixin, BusinessTenantMixin)
- Industry-standard (Django, Rails, FastAPI pattern)

Example migration:
    # OLD:
    class MyModel(BaseModel):
        pass  # Gets: Integer id, created_at, updated_at, is_deleted

    # NEW:
    from models.mixins import IntegerPKMixin, TimestampMixin, SoftDeleteBooleanMixin
    class MyModel(Base, IntegerPKMixin, TimestampMixin, SoftDeleteBooleanMixin):
        pass  # Same fields, but composable and flexible
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Integer

# MUST import Base from single source to avoid "Multiple classes found" errors
# Fixed: Import from core.database instead of missing legacy_declarative_base
from core.database import Base


class BaseModel(Base):
    """Base model with common fields

    DEPRECATED: Use mixin composition instead.

    This class is kept for backward compatibility with existing models.
    For new models, use mixins from models.mixins:
    - IntegerPKMixin or UUIDPKMixin (primary key)
    - TimestampMixin (created_at, updated_at)
    - SoftDeleteBooleanMixin or SoftDeleteTimestampMixin (deletion tracking)

    See models/booking.py for migration example.
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    is_deleted = Column(Boolean, default=False, nullable=False)

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary"""
        return {
            column.key: getattr(self, column.key)
            for column in self.__table__.columns
        }

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
