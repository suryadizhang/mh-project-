"""
User Models - Identity Schema

This module contains user account models for the identity schema.

Business Requirements:
- User authentication and profile management
- Support multiple authentication providers (Google, Facebook, Email)
- User status lifecycle (ACTIVE, INACTIVE, SUSPENDED, PENDING)
- Email verification workflow
- User metadata for extensibility
- Last login tracking for security
- Audit trail integration

Models:
- User: Core user account with authentication and profile
- UserStatus: User account status enum
- AuthProvider: OAuth authentication providers enum
"""

import enum
from datetime import datetime
from typing import List, Optional, Type
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, String, TypeDecorator
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base_class import Base


# ==================== CUSTOM TYPE FOR LOWERCASE ENUMS ====================


class LowercaseEnumType(TypeDecorator):
    """
    SQLAlchemy TypeDecorator for PostgreSQL enums with lowercase values.

    Solves the mismatch between:
    - Python enum NAMES: ACTIVE, GOOGLE, EMAIL (uppercase)
    - PostgreSQL enum VALUES: active, google, email (lowercase)

    This properly handles BOTH:
    - Writing: Python enum → lowercase value for database
    - Reading: lowercase value from database → Python enum

    IMPORTANT: We use String as the implementation (NOT PG_ENUM) to ensure
    process_bind_param is always called. Using PG_ENUM causes SQLAlchemy
    to bypass process_bind_param and use its internal enum lookup which fails.
    PostgreSQL will still cast the string to the enum type automatically.
    """

    impl = String  # MUST be String, not PG_ENUM - see docstring
    cache_ok = True

    def __init__(self, enum_class: Type[enum.Enum], pg_enum_name: str, schema: str = "public"):
        self.enum_class = enum_class
        self.pg_enum_name = pg_enum_name
        self.schema = schema
        super().__init__()

    def load_dialect_impl(self, dialect):
        """
        Return String type for all dialects.

        NOTE: We intentionally return String instead of PG_ENUM because:
        1. When PG_ENUM is returned, SQLAlchemy uses its internal _object_lookup
           which tries to match Python enum names ('ACTIVE') against PostgreSQL
           values ('active') and fails.
        2. By using String, we ensure process_bind_param is always called.
        3. PostgreSQL will automatically cast the string to the enum type.
        """
        return dialect.type_descriptor(String(50))

    def process_bind_param(self, value, dialect):
        """Convert Python enum to database value (lowercase string)."""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value.value  # Return lowercase: "active", "google"
        if isinstance(value, str):
            # Already a string, validate it
            valid_values = [e.value for e in self.enum_class]
            if value in valid_values:
                return value
            # Try to find by name (uppercase)
            try:
                return self.enum_class[value].value
            except KeyError:
                pass
        raise ValueError(f"Invalid value for {self.enum_class.__name__}: {value}")

    def process_result_value(self, value, dialect):
        """Convert database value (lowercase string) to Python enum."""
        if value is None:
            return None
        # Find enum member by value (lowercase)
        for member in self.enum_class:
            if member.value == value:
                return member
        raise ValueError(f"Unknown {self.enum_class.__name__} value: {value}")


# ==================== ENUMS ====================


class UserStatus(str, enum.Enum):
    """
    User account status.

    Business Rules:
    - ACTIVE: User can log in and access system
    - INACTIVE: User account disabled (can be reactivated)
    - SUSPENDED: User suspended for policy violation (requires admin review)
    - PENDING: New account awaiting email verification

    Status Transitions:
    - PENDING → ACTIVE (after email verification)
    - ACTIVE ↔ INACTIVE (admin action)
    - ACTIVE → SUSPENDED (policy violation)
    - SUSPENDED → ACTIVE (after admin review)
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class AuthProvider(str, enum.Enum):
    """
    OAuth authentication providers.

    Business Rules:
    - GOOGLE: Google OAuth 2.0 (primary for admin accounts)
    - FACEBOOK: Facebook OAuth (customer social login)
    - INSTAGRAM: Instagram OAuth (customer social login)
    - EMAIL: Email/password authentication (traditional)

    Access Control:
    - Admin accounts: GOOGLE only (via GoogleOAuthAccount)
    - Customer accounts: Any provider (via OAuthAccount)
    - Station users: EMAIL or GOOGLE
    """

    GOOGLE = "google"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    EMAIL = "email"


# ==================== MODELS ====================


class User(Base):
    """
    User entity (in identity schema).

    Core user account with authentication and profile.
    Referenced by identity.stations and other schemas.

    Business Requirements:
    - Unique email address per user
    - Support OAuth and password authentication
    - Track verification status
    - Track last login for security
    - Store user metadata (flexible JSON)
    - Support multiple roles (via UserRole)
    - Support multiple OAuth accounts (via OAuthAccount, GoogleOAuthAccount)
    - Support multiple station assignments (via StationUser)

    Authentication Methods:
    1. Email/Password: password_hash populated
    2. OAuth (Google/Facebook/Instagram): password_hash NULL, oauth_accounts populated
    3. Admin Google OAuth: password_hash NULL, google_oauth_accounts populated

    Status Lifecycle:
    - New user: PENDING → requires email verification
    - Verified: ACTIVE → can access system
    - Disabled: INACTIVE → temporarily disabled
    - Policy violation: SUSPENDED → requires admin review

    Security:
    - Email must be unique and validated
    - Password hash uses bcrypt (if password auth)
    - OAuth tokens stored in separate tables (encrypted in production)
    - Last login tracked for audit
    - Status changes logged via audit tables

    Access Control:
    - User can view/update their own profile
    - Super admin can view/update any user
    - Station admin can view users in their station
    """

    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_status", "status"),
        Index("idx_users_created_at", "created_at"),
        {"schema": "identity"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Authentication
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # NULL for OAuth-only users

    # OAuth Provider IDs (for social login linking)
    google_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    microsoft_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    apple_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Auth provider tracking
    auth_provider: Mapped[AuthProvider] = mapped_column(
        LowercaseEnumType(AuthProvider, "authprovider", "public"),
        nullable=False,
        default=AuthProvider.EMAIL,
    )

    # Profile
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status
    status: Mapped[UserStatus] = mapped_column(
        LowercaseEnumType(UserStatus, "userstatus", "public"),
        nullable=False,
        default=UserStatus.ACTIVE,
        index=True,
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Metadata (extensible JSON for custom fields)
    user_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # MFA / Security (WebAuthn, PIN, Lockout)
    # These columns exist in production database - do NOT remove
    webauthn_credentials: Mapped[list] = mapped_column(JSONB, nullable=True, default=list)
    pin_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pin_attempts: Mapped[int] = mapped_column(default=0)
    pin_locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    mfa_setup_complete: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    mfa_setup_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    pin_reset_required: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    lockout_count: Mapped[int] = mapped_column(default=0)
    last_lockout_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_security_disabled: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)

    # Relationships
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", foreign_keys="[UserRole.user_id]", back_populates="user"
    )
    oauth_accounts: Mapped[List["OAuthAccount"]] = relationship(
        "OAuthAccount", back_populates="user"
    )
    google_oauth_accounts: Mapped[List["GoogleOAuthAccount"]] = relationship(
        "GoogleOAuthAccount", foreign_keys="[GoogleOAuthAccount.user_id]", back_populates="user"
    )
    station_users: Mapped[List["StationUser"]] = relationship("StationUser", back_populates="user")
    sent_invitations: Mapped[List["AdminInvitation"]] = relationship(
        "AdminInvitation", foreign_keys="[AdminInvitation.invited_by]", back_populates="inviter"
    )
    accepted_invitations: Mapped[List["AdminInvitation"]] = relationship(
        "AdminInvitation",
        foreign_keys="[AdminInvitation.accepted_by_user_id]",
        back_populates="accepted_user",
    )

    # NOTE: The following relationships are commented out because the models
    # (UserSession, AuditLog, PasswordResetToken) are defined in core/auth/models.py
    # but not registered with the main SQLAlchemy ORM registry. This causes mapper
    # initialization failures. TODO: Properly integrate these models or move them
    # to db/models/identity/ and register in __init__.py
    #
    # # Auth session tracking (from core/auth/models.py UserSession)
    # sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user")
    #
    # # Audit logs (from core/auth/models.py AuditLog)
    # audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user")
    #
    # # Password reset tokens (from core/auth/models.py PasswordResetToken)
    # password_reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(
    #     "PasswordResetToken", back_populates="user"
    # )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, status={self.status})>"

    def get_display_name(self) -> str:
        """Get user's display name (computed from first_name/last_name or stored full_name)."""
        # Prefer stored full_name if set
        if self.full_name:
            return self.full_name
        # Fall back to computed name
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email

    def has_super_admin_role(self) -> bool:
        """Check if user has SUPER_ADMIN role via the user_roles relationship."""
        if not self.user_roles:
            return False
        for user_role in self.user_roles:
            if (
                user_role.role
                and user_role.role.role_type
                and str(user_role.role.role_type).upper() in ("SUPER_ADMIN", "SUPERADMIN")
            ):
                return True
        return False

    def is_active_user(self) -> bool:
        """Check if user is active and verified."""
        return self.status == UserStatus.ACTIVE and self.is_verified
