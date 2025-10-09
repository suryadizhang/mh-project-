"""Base model for lead and newsletter models."""

from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func

# Import the same Base used by core models
from .core import Base


class BaseModel(Base):
    """Base model with common fields."""
    __abstract__ = True
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)