"""
User model for authentication and authorization
Supports multiple authentication providers (Google OAuth, email/password, etc.)
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Index, func, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from models.base import Base


class AuthProvider(str, enum.Enum):
    """Authentication provider types"""
    GOOGLE = "google"
    EMAIL = "email"
    MICROSOFT = "microsoft"
    APPLE = "apple"


class UserStatus(str, enum.Enum):
    """User account status"""
    PENDING = "pending"  # Awaiting super admin approval
    ACTIVE = "active"    # Approved and active
    SUSPENDED = "suspended"  # Temporarily disabled
    DEACTIVATED = "deactivated"  # Permanently disabled


class User(Base):
    """
    User model for authentication and authorization
    
    Multi-tenant support via station_users relationship
    Supports multiple auth providers (Google OAuth, email/password)
    """
    __tablename__ = "users"
    __table_args__ = {'schema': 'identity'}
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Basic information
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    
    # Authentication
    auth_provider = Column(SQLEnum(AuthProvider), default=AuthProvider.EMAIL, nullable=False)
    google_id = Column(String(255), unique=True, nullable=True, index=True)  # Google OAuth ID
    microsoft_id = Column(String(255), unique=True, nullable=True)
    apple_id = Column(String(255), unique=True, nullable=True)
    
    # Password auth (only for email provider)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status and permissions
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING, nullable=False, index=True)
    is_super_admin = Column(Boolean, default=False, nullable=False)  # Global super admin
    is_email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Security
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)  # TOTP secret
    backup_codes = Column(JSONB, nullable=True)  # List of backup codes
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Session management
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv6 max length
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    
    # Approval workflow (for new Google OAuth users)
    approved_by = Column(UUID(as_uuid=True), nullable=True)  # Super admin who approved
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Metadata
    settings = Column(JSONB, default={}, nullable=False)  # User preferences
    metadata = Column(JSONB, default={}, nullable=False)  # Additional data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Relationships (defined in station models to avoid circular imports)
    # station_assignments = relationship("StationUser", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, provider={self.auth_provider}, status={self.status})>"


# Indexes for performance
Index('idx_users_email_lower', func.lower(User.email), unique=True)  # Case-insensitive email
Index('idx_users_status_created', User.status, User.created_at.desc())
Index('idx_users_provider_status', User.auth_provider, User.status)
Index('idx_users_last_login', User.last_login_at.desc())
