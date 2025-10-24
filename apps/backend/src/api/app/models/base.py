"""Base model for lead and newsletter models."""

from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func

# Import unified Base from models package
from api.app.models.declarative_base import Base


class BaseModel(Base):
    """Base model with common fields."""
    __abstract__ = True
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)