"""
Email Label model for organizing emails with custom labels/tags

Labels can be:
- System labels (inbox, sent, trash, spam)
- User-created custom labels
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base_class import Base


class EmailLabel(Base):
    """
    Custom labels/tags for organizing emails
    Similar to Gmail labels or Outlook categories
    """

    __tablename__ = "email_labels"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Label Identifiers
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    """URL-safe identifier (e.g., 'follow-up', 'urgent', 'vip-customer')"""

    name: Mapped[str] = mapped_column(String(200), index=True)
    """Display name (e.g., 'Follow Up', 'Urgent', 'VIP Customer')"""

    # Appearance
    color: Mapped[str | None] = mapped_column(String(50))
    """Hex color code (e.g., '#FF5733') for label display"""

    icon: Mapped[str | None] = mapped_column(String(50))
    """Icon name or emoji for the label"""

    # Ordering
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    """Sort order for display (lower = first)"""

    # Type
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    """System labels cannot be deleted (inbox, sent, trash, etc.)"""

    # Status
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    """Label is archived (hidden from main list)"""

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    """Soft delete flag"""

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<EmailLabel(slug={self.slug}, name={self.name})>"
