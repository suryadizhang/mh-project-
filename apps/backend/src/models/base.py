"""
Base model classes and common types
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields"""

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
