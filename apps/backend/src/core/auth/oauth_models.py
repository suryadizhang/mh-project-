"""
Google OAuth Authentication Models
Supports any Google account with super admin approval/invitation system.
"""

from datetime import datetime, timezone, timedelta
from enum import Enum
from uuid import UUID, uuid4

from models.base import BaseModel as Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class InvitationStatus(str, Enum):
    """Status of admin invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""

    GOOGLE = "google"
    # Future: MICROSOFT = "microsoft", APPLE = "apple"


class AdminInvitation(Base):
    """
    Admin invitation system for Google OAuth access control.
    Super admins can invite any Google account.
    """

    __tablename__ = "admin_invitations"
    __table_args__ = {"schema": "identity"}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Invitation details
    email = Column(String(255), nullable=False, index=True)
    invitation_code = Column(String(100), nullable=False, unique=True, index=True)

    # Role assignment
    role = Column(String(30), nullable=False, default="customer_support")  # StationRole
    station_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=True, index=True
    )

    # Invitation lifecycle
    status = Column(String(20), nullable=False, default=InvitationStatus.PENDING.value)
    invited_by = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=False)
    invited_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Acceptance tracking
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    accepted_by_user_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=True
    )

    # Revocation tracking
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=True)
    revoked_reason = Column(Text, nullable=True)

    # Metadata
    notes = Column(Text, nullable=True)  # Admin notes about the invitation

    # Relationships
    inviter = relationship("User", foreign_keys=[invited_by])
    station = relationship("Station")
    accepted_user = relationship("User", foreign_keys=[accepted_by_user_id])
    revoker = relationship("User", foreign_keys=[revoked_by])


class OAuthAccount(Base):
    """
    OAuth account linking for Google authentication.
    Supports multiple OAuth providers per user.
    """

    __tablename__ = "oauth_accounts"
    __table_args__ = {"schema": "identity"}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # User linkage
    user_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=False, index=True
    )

    # OAuth provider details
    provider = Column(String(20), nullable=False, default=OAuthProvider.GOOGLE.value)
    provider_account_id = Column(String(255), nullable=False)  # Google user ID
    provider_account_email = Column(String(255), nullable=False, index=True)

    # OAuth tokens (encrypted in production)
    access_token = Column(Text, nullable=True)  # Current access token
    refresh_token = Column(Text, nullable=True)  # Refresh token
    token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Profile information from provider
    provider_profile = Column(Text, nullable=True)  # JSON blob with profile data
    profile_picture_url = Column(String(500), nullable=True)

    # Account status
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)

    # Approval tracking (for manual approval workflow)
    is_approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Revocation tracking
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=True)
    revoked_reason = Column(Text, nullable=True)

    # Timestamps
    linked_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="oauth_accounts")
    approver = relationship("User", foreign_keys=[approved_by])
    revoker = relationship("User", foreign_keys=[revoked_by])


class AdminAccessLog(Base):
    """
    Audit log for admin access via Google OAuth.
    Tracks login attempts, approvals, revocations.
    """

    __tablename__ = "admin_access_logs"
    __table_args__ = {"schema": "identity"}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Context
    user_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=True, index=True
    )
    oauth_account_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("identity.oauth_accounts.id"), nullable=True
    )
    email = Column(String(255), nullable=False, index=True)

    # Action
    action = Column(
        String(50), nullable=False, index=True
    )  # LOGIN, LOGOUT, INVITE, APPROVE, REVOKE, etc.
    result = Column(String(20), nullable=False)  # SUCCESS, FAILURE, PENDING

    # Details
    details = Column(Text, nullable=True)  # JSON with action-specific details
    error_message = Column(Text, nullable=True)

    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    oauth_account = relationship("OAuthAccount")


def generate_invitation_code() -> str:
    """Generate a secure invitation code."""
    import secrets

    return secrets.token_urlsafe(32)


def create_admin_invitation(
    email: str,
    role: str,
    invited_by_id: UUID,
    station_id: UUID | None = None,
    expiry_days: int = 7,
    notes: str | None = None,
) -> AdminInvitation:
    """
    Create a new admin invitation.

    Args:
        email: Email address to invite
        role: Role to assign (from StationRole enum)
        invited_by_id: User ID of the inviter (super admin)
        station_id: Optional station assignment
        expiry_days: Number of days until invitation expires (default 7)
        notes: Optional notes about the invitation

    Returns:
        AdminInvitation object
    """
    invitation = AdminInvitation(
        email=email.lower().strip(),
        invitation_code=generate_invitation_code(),
        role=role,
        station_id=station_id,
        invited_by=invited_by_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=expiry_days),
        notes=notes,
    )
    return invitation


__all__ = [
    "AdminAccessLog",
    "AdminInvitation",
    "InvitationStatus",
    "OAuthAccount",
    "OAuthProvider",
    "create_admin_invitation",
    "generate_invitation_code",
]
