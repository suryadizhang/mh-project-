"""
OAuth Account Models - Identity Schema

This module contains OAuth authentication models for customer social login.

Business Requirements:
- Social login for customers (Google, Facebook, Instagram)
- OAuth token storage and management
- Support multiple OAuth providers per user
- Profile data synchronization from providers
- Token refresh capability
- Separate from admin OAuth (GoogleOAuthAccount)

Models:
- OAuthAccount: OAuth-linked social account for customer authentication

Note:
- This is for CUSTOMER social login (Google/Facebook/Instagram)
- For ADMIN Google OAuth, see admin.py (GoogleOAuthAccount)
- For BUSINESS social media, see lead schema (SocialAccount)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base_class import Base


# ==================== MODELS ====================

class OAuthAccount(Base):
    """
    OAuth-linked social account for customer authentication.

    Stores OAuth tokens for third-party login (Google, Facebook, Instagram).
    Different from lead.SocialAccount (business social media pages).
    Different from admin.GoogleOAuthAccount (admin Google OAuth).

    Business Requirements:
    - Customer social login (alternative to email/password)
    - Support multiple providers: Google, Facebook, Instagram
    - Store OAuth access/refresh tokens
    - Sync profile data from provider
    - Unique (provider, provider_account_id) per user
    - Token expiration tracking

    Use Cases:
    - Customer signs up with Google
    - Customer logs in with Facebook
    - Customer links Instagram account
    - Customer switches between providers

    Security:
    - Tokens encrypted at rest (production)
    - Refresh tokens used to get new access tokens
    - Expired tokens refreshed automatically
    - Profile data validated before storage

    Access Control:
    - Creation: Customer (during social login)
    - Update: System (token refresh, profile sync)
    - Delete: Customer (unlink account), super_admin
    - View: Customer (own accounts), super_admin

    Token Management:
    - access_token: Short-lived (1 hour typical)
    - refresh_token: Long-lived (60 days typical)
    - expires_at: When access_token expires
    - Token refresh: Automatic when expires_at < now

    Profile Sync:
    - profile_data (JSONB): Name, email, picture, etc.
    - Synced on login
    - Used to update user profile (optional)

    Relationship to User:
    - Many OAuthAccounts → One User
    - User can have Google + Facebook + Instagram accounts
    - Primary authentication method tracked via user.oauth_accounts
    """
    __tablename__ = "social_accounts"
    __table_args__ = (
        Index("idx_social_accounts_user_id", "user_id"),
        Index("idx_social_accounts_provider", "provider"),
        UniqueConstraint("provider", "provider_account_id", name="uq_social_accounts_provider"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Foreign Keys
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id"),
        nullable=False
    )

    # Provider Details
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # "google", "facebook", "instagram"
    provider_account_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )  # OAuth provider's user ID

    # OAuth Tokens
    access_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )  # Encrypted in production
    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )  # Encrypted in production
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )  # When access_token expires

    # Profile Data (synced from provider)
    profile_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )  # {name, email, picture, etc.}

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")

    def __repr__(self) -> str:
        return f"<OAuthAccount(id={self.id}, provider={self.provider}, user_id={self.user_id})>"

    def is_token_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.expires_at:
            return False
        from datetime import timezone
        return datetime.now(timezone.utc) >= self.expires_at
