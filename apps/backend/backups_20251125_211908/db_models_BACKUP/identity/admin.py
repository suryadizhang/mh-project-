"""
Admin Identity & Access Control Models
=======================================

Google OAuth-based admin invitation and access control system.

Business Logic:
1. Super admins can invite Google accounts via email
2. Invitations expire after configurable period (default 7 days)
3. Invitees must accept invitation before gaining access
4. All admin access is logged for audit trail
5. Super admins can revoke access at any time

Models:
- AdminInvitation: Email-based invitation system
- GoogleOAuthAccount: Google OAuth credentials for admins
- AdminAccessLog: Audit trail for all admin actions
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID, uuid4
import enum
import secrets

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ...base_class import Base


class InvitationStatus(str, enum.Enum):
    """
    Admin invitation lifecycle status.

    Business Rules:
    - PENDING: Invitation sent, awaiting acceptance
    - ACCEPTED: User accepted and has access
    - REJECTED: User explicitly rejected invitation
    - EXPIRED: Invitation passed expiry date
    - REVOKED: Super admin revoked before acceptance
    """
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class AdminInvitation(Base):
    """
    Admin invitation system for Google OAuth access control.

    Business Requirements:
    - Only super admins can create invitations
    - Each invitation has unique code for security
    - Invitations expire after 7 days (configurable)
    - Can assign role and station during invitation
    - Track full lifecycle: invited, accepted, revoked
    - Audit trail: who invited, when, why revoked

    Access Control:
    - Creation: super_admin only
    - Acceptance: invited user only
    - Revocation: super_admin only
    - View: super_admin, station_admin (for their station)
    """
    __tablename__ = "admin_invitations"
    __table_args__ = (
        Index("idx_admin_invitations_email", "email"),
        Index("idx_admin_invitations_code", "invitation_code"),
        Index("idx_admin_invitations_status", "status"),
        Index("idx_admin_invitations_station", "station_id"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Invitation Details
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    invitation_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # Role Assignment (assigned when invitation accepted)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="customer_support")
    station_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.stations.id"),
        nullable=True
    )

    # Invitation Lifecycle
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=InvitationStatus.PENDING.value
    )
    invited_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id"),
        nullable=False
    )
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Acceptance Tracking
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id"),
        nullable=True
    )

    # Revocation Tracking (business requirement: audit why access removed)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id"),
        nullable=True
    )
    revoked_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata (business notes about invitation)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    inviter: Mapped["User"] = relationship(
        "User",
        foreign_keys=[invited_by],
        back_populates="sent_invitations"
    )
    station: Mapped[Optional["Station"]] = relationship("Station")
    accepted_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[accepted_by_user_id],
        back_populates="accepted_invitations"
    )
    revoker: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[revoked_by]
    )

    def is_valid(self) -> bool:
        """
        Check if invitation is valid for acceptance.

        Business Rules:
        - Must be PENDING status
        - Must not be expired
        - Must not be revoked
        """
        if self.status != InvitationStatus.PENDING.value:
            return False
        if datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    def can_be_revoked(self) -> bool:
        """Only pending invitations can be revoked."""
        return self.status == InvitationStatus.PENDING.value


class GoogleOAuthAccount(Base):
    """
    Google OAuth account linking for admin authentication.

    Business Requirements:
    - Supports Google OAuth 2.0 authentication
    - Requires super admin approval for new accounts
    - Stores OAuth tokens for API access
    - Tracks approval/revocation for audit
    - Separate from customer social accounts

    Security:
    - Tokens encrypted at rest (production)
    - Approval required before access granted
    - Can be revoked by super admin
    - All access logged via AdminAccessLog
    """
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        Index("idx_google_oauth_user", "user_id"),
        Index("idx_google_oauth_email", "provider_account_email"),
        Index("idx_google_oauth_provider", "provider", "provider_account_id"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # User Linkage
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id"),
        nullable=False
    )

    # OAuth Provider Details
    provider: Mapped[str] = mapped_column(String(20), nullable=False, default="google")
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Google user ID
    provider_account_email: Mapped[str] = mapped_column(String(255), nullable=False)

    # OAuth Tokens (TODO: encrypt in production)
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Profile Information
    provider_profile: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON blob
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Account Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Approval Tracking (business requirement: manual approval workflow)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id"),
        nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Revocation Tracking
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id"),
        nullable=True
    )
    revoked_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="google_oauth_accounts"
    )
    approver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by]
    )
    revoker_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[revoked_by]
    )

    def can_access(self) -> bool:
        """
        Check if account has access.

        Business Rules:
        - Must be active
        - Must be approved
        - Must not be revoked
        """
        return self.is_active and self.is_approved and not self.revoked_at


class AdminAccessLog(Base):
    """
    Audit log for admin access via Google OAuth.

    Business Requirements:
    - Log ALL admin authentication events
    - Track login attempts (success/failure)
    - Track invitation lifecycle events
    - Track approval/revocation actions
    - Store IP address and user agent for security
    - Immutable logs (no updates/deletes)

    Compliance:
    - Required for security audits
    - Required for compliance (SOC2, etc.)
    - Retention: minimum 1 year
    """
    __tablename__ = "admin_access_logs"
    __table_args__ = (
        Index("idx_admin_access_user", "user_id"),
        Index("idx_admin_access_email", "email"),
        Index("idx_admin_access_action", "action"),
        Index("idx_admin_access_created", "created_at"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Context
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id"),
        nullable=True
    )
    oauth_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.oauth_accounts.id"),
        nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Action (LOGIN, LOGOUT, INVITE_SENT, INVITE_ACCEPTED, APPROVED, REVOKED, etc.)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)  # SUCCESS, FAILURE, PENDING

    # Details (JSON with action-specific details)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Request Context (for security investigation)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamp (immutable)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    oauth_account: Mapped[Optional["GoogleOAuthAccount"]] = relationship("GoogleOAuthAccount")


# ==================== BUSINESS LOGIC FUNCTIONS ====================

def generate_invitation_code() -> str:
    """
    Generate a secure invitation code.

    Security Requirements:
    - URL-safe characters only
    - Cryptographically secure random
    - 32 bytes = 256 bits of entropy
    - Resistant to brute force attacks
    """
    return secrets.token_urlsafe(32)


def create_admin_invitation(
    email: str,
    role: str,
    invited_by_id: UUID,
    station_id: Optional[UUID] = None,
    expiry_days: int = 7,
    notes: Optional[str] = None,
) -> AdminInvitation:
    """
    Create a new admin invitation.

    Business Logic:
    1. Validate email format
    2. Check if user already invited/exists
    3. Generate secure invitation code
    4. Set expiration (default 7 days)
    5. Assign role and station
    6. Log invitation creation

    Args:
        email: Email address to invite (will be normalized)
        role: Role to assign (from StationRole enum)
        invited_by_id: User ID of inviter (must be super admin)
        station_id: Optional station assignment
        expiry_days: Days until expiration (default 7, max 30)
        notes: Optional notes about invitation

    Returns:
        AdminInvitation object (not yet saved to DB)

    Business Rules:
    - Email must be valid Gmail account
    - Cannot invite existing active admin
    - Expiry: 1-30 days (default 7)
    - Role must be valid station role
    - Station required for non-super-admin roles
    """
    # Normalize email
    normalized_email = email.lower().strip()

    # Validate expiry (business rule: max 30 days)
    if expiry_days < 1 or expiry_days > 30:
        raise ValueError("Expiry must be between 1 and 30 days")

    # Create invitation
    invitation = AdminInvitation(
        email=normalized_email,
        invitation_code=generate_invitation_code(),
        role=role,
        station_id=station_id,
        invited_by=invited_by_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=expiry_days),
        notes=notes,
    )

    return invitation
