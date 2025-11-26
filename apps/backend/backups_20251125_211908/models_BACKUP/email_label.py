"""
Email Label models for custom tagging and organization
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    Index,
)

from .base import BaseModel


class EmailLabel(BaseModel):
    """
    Custom email labels/tags for organization
    Examples: 'Follow-up', 'VIP', 'Bug Report', 'Urgent', 'Waiting for Response'
    """

    __tablename__ = "email_labels"

    # Label Properties
    name = Column(String(100), unique=True, nullable=False, index=True)
    """Label name (e.g., 'Follow-up', 'VIP', 'Bug Report')"""

    slug = Column(String(100), unique=True, nullable=False, index=True)
    """URL-friendly slug (e.g., 'follow-up', 'vip', 'bug-report')"""

    description = Column(Text, nullable=True)
    """Optional description of the label's purpose"""

    # Display Properties
    color = Column(String(7), nullable=False, default="#6B7280")
    """Hex color code for label display (e.g., '#3B82F6' for blue)"""

    icon = Column(String(50), nullable=True)
    """Optional icon name (e.g., 'flag', 'star', 'alert')"""

    # Behavior
    is_system = Column(Boolean, default=False, nullable=False)
    """Whether this is a system-defined label (cannot be deleted)"""

    is_archived = Column(Boolean, default=False, nullable=False)
    """Whether the label is archived (hidden from UI)"""

    # Usage Stats
    email_count = Column(Integer, default=0, nullable=False)
    """Number of emails with this label (for quick stats)"""

    # Sorting
    sort_order = Column(Integer, default=0, nullable=False)
    """Display order (lower numbers appear first)"""

    # Indexes
    __table_args__ = (
        Index("idx_name_archived", "name", "is_archived"),
        Index("idx_sort_order", "sort_order"),
    )

    def __repr__(self):
        return f"<EmailLabel(id={self.id}, name={self.name}, color={self.color})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
            "is_system": self.is_system,
            "is_archived": self.is_archived,
            "email_count": self.email_count,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
