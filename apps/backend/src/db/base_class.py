"""
SQLAlchemy Base Class
=====================

Declarative base for all SQLAlchemy models.
Provides common functionality and type checking.
"""

from typing import Any
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models

    Provides:
    - Declarative base functionality
    - Common table naming conventions
    - Type checking support
    """

    # Use type annotation helper for better IDE support
    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Auto-generate table name from class name
        Override in model if custom name needed
        """
        return cls.__name__.lower()

    def dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary
        Useful for serialization
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
        """String representation of model"""
        class_name = self.__class__.__name__
        attrs = ", ".join(
            f"{c.name}={getattr(self, c.name)!r}"
            for c in self.__table__.columns
            if c.primary_key
        )
        return f"{class_name}({attrs})"
