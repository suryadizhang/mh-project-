"""
Business Model for White-Label Multi-Tenancy

Purpose: Enable multiple restaurant brands to run on same infrastructure.
Currently: "My Hibachi Chef" as the first and only business.
Future: Other hibachi catering companies can white-label the platform.

Usage:
    from src.models.business import Business

    # Get current business from context
    business = await Business.get_by_slug("my-hibachi-chef")

    # Access branding
    print(business.name, business.logo_url, business.primary_color)
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, Numeric, String, Text, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import Base


class Business(Base):
    """
    Business entity for white-label multi-tenancy support.

    Each business represents a restaurant brand using the platform.
    All user-facing data (bookings, leads, menus) belongs to a business.
    """

    __tablename__ = "businesses"

    # Primary Key
    id: UUID = Column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, server_default="gen_random_uuid()"
    )

    # Identity
    name: str = Column(String(255), nullable=False)  # "My Hibachi Chef"
    slug: str = Column(String(100), unique=True, nullable=False, index=True)  # "my-hibachi-chef"
    domain: Optional[str] = Column(String(255), unique=True, nullable=True)  # "myhibachichef.com"

    # Branding
    logo_url: Optional[str] = Column(String(500), nullable=True)
    primary_color: str = Column(String(7), nullable=True, default="#FF6B6B")  # Coral red
    secondary_color: str = Column(String(7), nullable=True, default="#4ECDC4")  # Teal

    # Contact Information
    phone: Optional[str] = Column(String(20), nullable=True)
    email: Optional[str] = Column(String(255), nullable=True)
    address: Optional[str] = Column(Text, nullable=True)

    # Business Settings
    timezone: str = Column(String(50), nullable=False, default="America/Los_Angeles")
    currency: str = Column(String(3), nullable=False, default="USD")
    settings: Dict[str, Any] = Column(JSONB, nullable=False, default={})

    # Subscription (White-Label Revenue Model)
    subscription_tier: str = Column(String(50), nullable=False, default="self_hosted")
    # Tiers: "self_hosted" (free, us), "basic" ($500/mo), "pro" ($1500/mo), "enterprise" ($3000/mo)
    subscription_status: str = Column(String(20), nullable=False, default="active")
    # Status: "active", "trial", "suspended", "canceled"
    monthly_fee: float = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Metadata
    is_active: bool = Column(Boolean, nullable=False, default=True)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: datetime = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships (will be populated as we add business_id to other models)
    # users = relationship("User", back_populates="business")
    # bookings = relationship("Booking", back_populates="business")
    # leads = relationship("Lead", back_populates="business")
    # reviews = relationship("Review", back_populates="business")
    # newsletter_subscribers = relationship("NewsletterSubscriber", back_populates="business")

    def __repr__(self) -> str:
        return f"<Business {self.name} ({self.slug})>"

    @property
    def brand_name(self) -> str:
        """Alias for compatibility with existing config.BRAND_NAME usage"""
        return self.name

    @classmethod
    async def get_by_id(cls, session: AsyncSession, business_id: UUID) -> Optional["Business"]:
        """Get business by UUID"""
        result = await session.execute(select(cls).where(cls.id == business_id))
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_slug(cls, session: AsyncSession, slug: str) -> Optional["Business"]:
        """Get business by slug (my-hibachi-chef)"""
        result = await session.execute(select(cls).where(cls.slug == slug))
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_domain(cls, session: AsyncSession, domain: str) -> Optional["Business"]:
        """Get business by domain (myhibachichef.com)"""
        result = await session.execute(select(cls).where(cls.domain == domain))
        return result.scalar_one_or_none()

    @classmethod
    async def get_default(cls, session: AsyncSession) -> Optional["Business"]:
        """Get My Hibachi Chef (the default business)"""
        return await cls.get_by_slug(session, "my-hibachi-chef")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize business to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "domain": self.domain,
            "branding": {
                "logo_url": self.logo_url,
                "primary_color": self.primary_color,
                "secondary_color": self.secondary_color,
            },
            "contact": {
                "phone": self.phone,
                "email": self.email,
                "address": self.address,
            },
            "timezone": self.timezone,
            "currency": self.currency,
            "settings": self.settings,
            "subscription": {
                "tier": self.subscription_tier,
                "status": self.subscription_status,
                "monthly_fee": float(self.monthly_fee),
            },
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
