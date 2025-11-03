"""
Customer Review Blog Post models
"""

from datetime import datetime
import json

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from .base import BaseModel


class CustomerReviewBlogPost(BaseModel):
    """Customer review blog post with admin approval workflow"""

    __tablename__ = "customer_review_blog_posts"

    # Relationships
    customer_id = Column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)

    # Customer Contact Info (stored directly for privacy control)
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    show_initials_only = Column(
        Boolean, default=False
    )  # Privacy option: show initials instead of full name

    # Content
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)

    # Images (stored as JSON array)
    images = Column(Text, default="[]")  # SQLite uses TEXT for JSON

    # Status (admin approval workflow)
    status = Column(String(20), default="pending", nullable=False, index=True)
    # Note: approved_by references users table - will be enabled when user authentication is implemented
    # approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(
        Integer, nullable=True
    )  # Temporarily without foreign key until users table exists
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # External reviews
    reviewed_on_google = Column(Boolean, default=False)
    reviewed_on_yelp = Column(Boolean, default=False)
    google_review_link = Column(Text, nullable=True)
    yelp_review_link = Column(Text, nullable=True)

    # Note: created_at, updated_at, is_deleted inherited from BaseModel

    # SEO
    slug = Column(String(255), unique=True, nullable=True, index=True)
    keywords = Column(Text, nullable=True)  # Comma-separated keywords

    # Engagement
    likes_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)

    # Constraints
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="rating_range"),
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="valid_status"),
    )

    # Relationships (define if Customer and User models exist)
    # customer = relationship("Customer", back_populates="reviews")
    # approved_by_user = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<CustomerReviewBlogPost(id={self.id}, title={self.title}, status={self.status})>"

    @property
    def is_pending(self) -> bool:
        """Check if review is pending approval"""
        return self.status == "pending"

    @property
    def is_approved(self) -> bool:
        """Check if review is approved"""
        return self.status == "approved"

    @property
    def is_rejected(self) -> bool:
        """Check if review is rejected"""
        return self.status == "rejected"

    def get_images(self) -> list[dict]:
        """Parse images from JSON string"""
        try:
            if self.images:
                return json.loads(self.images)
        except (json.JSONDecodeError, TypeError):
            pass
        return []

    def set_images(self, images: list[dict]):
        """Set images as JSON string"""
        self.images = json.dumps(images) if images else "[]"

    def get_keywords_list(self) -> list[str]:
        """Parse keywords from comma-separated string"""
        if self.keywords:
            return [k.strip() for k in self.keywords.split(",") if k.strip()]
        return []

    def set_keywords(self, keywords: list[str]):
        """Set keywords as comma-separated string"""
        self.keywords = ",".join(keywords) if keywords else None

    def approve(self, admin_id: int):
        """Approve the review"""
        self.status = "approved"
        self.approved_by = admin_id
        self.approved_at = datetime.utcnow()
        self.rejection_reason = None

    def reject(self, admin_id: int, reason: str):
        """Reject the review"""
        self.status = "rejected"
        self.approved_by = admin_id
        self.rejection_reason = reason
        self.approved_at = None

    def increment_likes(self):
        """Increment likes count (atomic)"""
        self.likes_count = (self.likes_count or 0) + 1

    def increment_helpful(self):
        """Increment helpful count (atomic)"""
        self.helpful_count = (self.helpful_count or 0) + 1

    def get_initials(self) -> str:
        """
        Generate initials from customer name
        Examples:
        - "John Doe" -> "JD"
        - "Sarah" -> "S"
        - "Mary Jane Watson" -> "MJ" (takes first and last word)
        """
        if not self.customer_name:
            return "?"

        words = self.customer_name.strip().split()
        if len(words) == 0:
            return "?"
        elif len(words) == 1:
            return words[0][0].upper()
        else:
            # Take first letter of first word and first letter of last word
            return (words[0][0] + words[-1][0]).upper()

    def get_display_name(self) -> str:
        """
        Get the name to display publicly based on privacy preference
        - If show_initials_only is True: return initials (e.g., "JD")
        - If show_initials_only is False: return full name (e.g., "John Doe")
        Admin always sees full name regardless of this setting.
        """
        if self.show_initials_only:
            return self.get_initials()
        return self.customer_name or "Anonymous"


class ReviewApprovalLog(BaseModel):
    """Audit trail of admin actions on reviews"""

    __tablename__ = "review_approval_log"

    # Relationships
    review_id = Column(
        Integer,
        ForeignKey("customer_review_blog_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Note: admin_id references users table - will be enabled when user authentication is implemented
    # admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    admin_id = Column(
        Integer, nullable=True, index=True
    )  # Temporarily without foreign key until users table exists

    # Action details
    action = Column(String(20), nullable=False)  # pending_review, approved, rejected
    comment = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "action IN ('pending_review', 'approved', 'rejected')", name="valid_action"
        ),
    )

    # Relationships
    # review = relationship("CustomerReviewBlogPost", back_populates="approval_logs")
    # admin = relationship("User", foreign_keys=[admin_id])

    def __repr__(self):
        return (
            f"<ReviewApprovalLog(id={self.id}, review_id={self.review_id}, action={self.action})>"
        )

    @classmethod
    def create_log(
        cls, review_id: int, action: str, admin_id: int | None = None, comment: str | None = None
    ):
        """Factory method to create approval log entry"""
        return cls(review_id=review_id, admin_id=admin_id, action=action, comment=comment)
