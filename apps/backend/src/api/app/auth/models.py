"""
OAuth 2.1 + OIDC + MFA Identity System with RBAC.
Implements modern authentication with proper security controls.
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from enum import Enum
from io import BytesIO
from typing import Any, Optional
from uuid import UUID, uuid4

import bcrypt
import jwt
import pyotp
import qrcode
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utils.encryption import FieldEncryption

Base = declarative_base()


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    PENDING_VERIFICATION = "pending_verification"


class SessionStatus(str, Enum):
    """Session status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    LOGGED_OUT = "logged_out"


class Role(str, Enum):
    """User roles with hierarchical permissions."""
    SUPER_ADMIN = "super_admin"      # Full system access
    ADMIN = "admin"                  # Full CRM access
    MANAGER = "manager"              # Booking management + reports
    STAFF = "staff"                  # Basic booking operations
    VIEWER = "viewer"                # Read-only access
    AI_SYSTEM = "ai_system"          # AI system permissions


class Permission(str, Enum):
    """Granular permissions."""
    # Booking permissions
    BOOKING_CREATE = "booking.create"
    BOOKING_READ = "booking.read"
    BOOKING_UPDATE = "booking.update"
    BOOKING_CANCEL = "booking.cancel"

    # Payment permissions
    PAYMENT_RECORD = "payment.record"
    PAYMENT_READ = "payment.read"
    PAYMENT_REFUND = "payment.refund"

    # Customer permissions
    CUSTOMER_READ = "customer.read"
    CUSTOMER_UPDATE = "customer.update"
    CUSTOMER_DELETE = "customer.delete"

    # Message permissions
    MESSAGE_READ = "message.read"
    MESSAGE_SEND = "message.send"
    MESSAGE_DELETE = "message.delete"

    # Admin permissions
    USER_MANAGE = "user.manage"
    SYSTEM_CONFIG = "system.config"
    AUDIT_READ = "audit.read"

    # Reports
    REPORTS_VIEW = "reports.view"
    REPORTS_EXPORT = "reports.export"


# Role-Permission Mapping
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.SUPER_ADMIN: set(Permission),  # All permissions
    Role.ADMIN: {
        Permission.BOOKING_CREATE, Permission.BOOKING_READ, Permission.BOOKING_UPDATE, Permission.BOOKING_CANCEL,
        Permission.PAYMENT_RECORD, Permission.PAYMENT_READ, Permission.PAYMENT_REFUND,
        Permission.CUSTOMER_READ, Permission.CUSTOMER_UPDATE, Permission.CUSTOMER_DELETE,
        Permission.MESSAGE_READ, Permission.MESSAGE_SEND, Permission.MESSAGE_DELETE,
        Permission.REPORTS_VIEW, Permission.REPORTS_EXPORT, Permission.AUDIT_READ
    },
    Role.MANAGER: {
        Permission.BOOKING_CREATE, Permission.BOOKING_READ, Permission.BOOKING_UPDATE, Permission.BOOKING_CANCEL,
        Permission.PAYMENT_RECORD, Permission.PAYMENT_READ,
        Permission.CUSTOMER_READ, Permission.CUSTOMER_UPDATE,
        Permission.MESSAGE_READ, Permission.MESSAGE_SEND,
        Permission.REPORTS_VIEW, Permission.REPORTS_EXPORT
    },
    Role.STAFF: {
        Permission.BOOKING_CREATE, Permission.BOOKING_READ, Permission.BOOKING_UPDATE,
        Permission.PAYMENT_RECORD, Permission.PAYMENT_READ,
        Permission.CUSTOMER_READ,
        Permission.MESSAGE_READ, Permission.MESSAGE_SEND
    },
    Role.VIEWER: {
        Permission.BOOKING_READ,
        Permission.CUSTOMER_READ,
        Permission.MESSAGE_READ
    },
    Role.AI_SYSTEM: {
        Permission.BOOKING_CREATE, Permission.BOOKING_READ,
        Permission.CUSTOMER_READ,
        Permission.MESSAGE_READ, Permission.MESSAGE_SEND
    }
}


class User(Base):
    """User accounts with encrypted PII."""

    __tablename__ = "users"
    __table_args__ = {"schema": "identity"}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Identity (encrypted)
    email_encrypted = Column(String(500), nullable=False, unique=True)
    username = Column(String(100), nullable=False, unique=True)

    # Authentication
    password_hash = Column(String(100), nullable=False)  # bcrypt hash
    password_salt = Column(String(32), nullable=False)   # Additional salt

    # MFA
    mfa_enabled = Column(Boolean, nullable=False, default=False)
    mfa_secret_encrypted = Column(String(500), nullable=True)  # TOTP secret
    backup_codes_encrypted = Column(JSON, nullable=True)       # Recovery codes

    # Profile (encrypted)
    first_name_encrypted = Column(String(500), nullable=True)
    last_name_encrypted = Column(String(500), nullable=True)
    phone_encrypted = Column(String(500), nullable=True)

    # Access Control
    role = Column(String(20), nullable=False, default=Role.STAFF.value)
    status = Column(String(20), nullable=False, default=UserStatus.PENDING_VERIFICATION.value)
    additional_permissions = Column(JSON, nullable=False, default=list)  # Extra permissions beyond role

    # Security tracking
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    last_failed_login = Column(DateTime(timezone=True), nullable=True)
    lockout_until = Column(DateTime(timezone=True), nullable=True)

    # Activity
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    sessions = relationship("UserSession", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

    __table_args__ = (
        CheckConstraint(f"role IN {tuple(r.value for r in Role)}", name="user_role_valid"),
        CheckConstraint(f"status IN {tuple(s.value for s in UserStatus)}", name="user_status_valid"),
        CheckConstraint("failed_login_attempts >= 0", name="user_failed_attempts_non_negative"),
        Index("idx_user_email_hash", "email_encrypted"),
        Index("idx_user_status_role", "status", "role"),
        {"schema": "identity"}
    )


class UserSession(Base):
    """User sessions with JWT token management."""

    __tablename__ = "user_sessions"
    __table_args__ = {"schema": "identity"}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=False, index=True)

    # Session identification
    session_token = Column(String(64), nullable=False, unique=True)  # Secure random token
    refresh_token_hash = Column(String(100), nullable=False, unique=True)  # Hashed refresh token

    # JWT details
    access_token_jti = Column(String(36), nullable=False, unique=True)    # JWT ID for access token
    refresh_token_jti = Column(String(36), nullable=False, unique=True)   # JWT ID for refresh token

    # Session metadata
    device_fingerprint = Column(String(64), nullable=True)  # Device identification
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    location = Column(String(100), nullable=True)   # City, Country

    # MFA tracking
    mfa_verified = Column(Boolean, nullable=False, default=False)
    mfa_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Status and expiry
    status = Column(String(20), nullable=False, default=SessionStatus.ACTIVE.value)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        CheckConstraint(f"status IN {tuple(s.value for s in SessionStatus)}", name="session_status_valid"),
        Index("idx_session_user_status", "user_id", "status"),
        Index("idx_session_expires", "expires_at"),
        {"schema": "identity"}
    )


class AuditLog(Base):
    """Comprehensive audit logging for security and compliance."""

    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "identity"}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Who
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=True, index=True)
    session_id = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.user_sessions.id"), nullable=True)

    # What
    action = Column(String(50), nullable=False, index=True)  # LOGIN, LOGOUT, CREATE_BOOKING, etc.
    resource_type = Column(String(50), nullable=True)       # booking, customer, payment, etc.
    resource_id = Column(String(50), nullable=True)         # ID of affected resource

    # Context
    details = Column(JSON, nullable=False, default=dict)    # Action-specific details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Result
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_user_action", "user_id", "action"),
        Index("idx_audit_created", "created_at"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        {"schema": "identity"}
    )


class PasswordResetToken(Base):
    """Password reset tokens."""

    __tablename__ = "password_reset_tokens"
    __table_args__ = {"schema": "identity"}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=False, index=True)

    token_hash = Column(String(100), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        Index("idx_reset_token_expires", "expires_at"),
        {"schema": "identity"}
    )


class AuthenticationService:
    """Core authentication service with comprehensive security."""

    def __init__(self, encryption: FieldEncryption, jwt_secret: str, jwt_issuer: str = "myhibachi-crm"):
        self.encryption = encryption
        self.jwt_secret = jwt_secret
        self.jwt_issuer = jwt_issuer
        self.jwt_algorithm = "HS256"

        # Security settings
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.password_min_length = 8
        self.session_lifetime = timedelta(hours=8)
        self.refresh_lifetime = timedelta(days=30)

    def hash_password(self, password: str) -> tuple[str, str]:
        """Hash password with salt using bcrypt + additional salt."""
        # Generate additional salt for double protection
        additional_salt = secrets.token_hex(16)

        # Combine password with additional salt
        salted_password = f"{password}{additional_salt}"

        # Bcrypt hash (includes its own salt)
        bcrypt_hash = bcrypt.hashpw(salted_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        return bcrypt_hash, additional_salt

    def verify_password(self, password: str, password_hash: str, password_salt: str) -> bool:
        """Verify password against hash."""
        try:
            salted_password = f"{password}{password_salt}"
            return bcrypt.checkpw(salted_password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False

    def generate_mfa_secret(self) -> str:
        """Generate TOTP secret for MFA."""
        return pyotp.random_base32()

    def generate_mfa_qr_code(self, email: str, secret: str) -> bytes:
        """Generate QR code for MFA setup."""
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=email,
            issuer_name="My Hibachi CRM"
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        return img_buffer.getvalue()

    def verify_mfa_token(self, secret: str, token: str, window: int = 1) -> bool:
        """Verify TOTP token with time window."""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)
        except Exception:
            return False

    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """Generate backup codes for MFA recovery."""
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes

    def hash_backup_codes(self, codes: list[str]) -> list[dict[str, Any]]:
        """Hash backup codes for storage."""
        hashed_codes = []
        for code in codes:
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            hashed_codes.append({
                'hash': code_hash,
                'used': False,
                'created_at': datetime.utcnow().isoformat()
            })
        return hashed_codes

    def verify_backup_code(self, hashed_codes: list[dict[str, Any]], provided_code: str) -> tuple[bool, list[dict[str, Any]]]:
        """Verify backup code and mark as used."""
        provided_hash = hashlib.sha256(provided_code.encode()).hexdigest()

        for i, code_data in enumerate(hashed_codes):
            if code_data['hash'] == provided_hash and not code_data['used']:
                # Mark as used
                hashed_codes[i]['used'] = True
                hashed_codes[i]['used_at'] = datetime.utcnow().isoformat()
                return True, hashed_codes

        return False, hashed_codes

    def create_jwt_tokens(self, user: User, session_id: UUID) -> tuple[str, str]:
        """Create access and refresh JWT tokens."""
        now = datetime.utcnow()

        # Access token (short-lived)
        access_jti = str(uuid4())
        access_payload = {
            'iss': self.jwt_issuer,
            'sub': str(user.id),
            'aud': 'myhibachi-api',
            'iat': now,
            'exp': now + timedelta(minutes=15),  # 15 minute access tokens
            'jti': access_jti,
            'typ': 'access',
            'session_id': str(session_id),
            'role': user.role,
            'permissions': list(self.get_user_permissions(user))
        }

        # Refresh token (long-lived)
        refresh_jti = str(uuid4())
        refresh_payload = {
            'iss': self.jwt_issuer,
            'sub': str(user.id),
            'aud': 'myhibachi-api',
            'iat': now,
            'exp': now + self.refresh_lifetime,
            'jti': refresh_jti,
            'typ': 'refresh',
            'session_id': str(session_id)
        }

        access_token = jwt.encode(access_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm=self.jwt_algorithm)

        return access_token, refresh_token, access_jti, refresh_jti

    def verify_jwt_token(self, token: str, token_type: str = 'access') -> Optional[dict[str, Any]]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                audience='myhibachi-api',
                issuer=self.jwt_issuer
            )

            if payload.get('typ') != token_type:
                return None

            return payload
        except jwt.InvalidTokenError:
            return None

    def get_user_permissions(self, user: User) -> set[str]:
        """Get all permissions for a user based on role and additional permissions."""
        role = Role(user.role)
        permissions = ROLE_PERMISSIONS.get(role, set())

        # Add additional permissions
        if user.additional_permissions:
            for perm in user.additional_permissions:
                try:
                    permissions.add(Permission(perm))
                except ValueError:
                    pass  # Invalid permission, skip

        return {p.value for p in permissions}

    def generate_session_token(self) -> str:
        """Generate secure session token."""
        return secrets.token_urlsafe(48)

    def hash_refresh_token(self, refresh_token: str) -> str:
        """Hash refresh token for storage."""
        return hashlib.sha256(refresh_token.encode()).hexdigest()

    def generate_device_fingerprint(self, user_agent: str, ip_address: str) -> str:
        """Generate device fingerprint for session tracking."""
        fingerprint_data = f"{user_agent}|{ip_address}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]

    def validate_password_strength(self, password: str) -> tuple[bool, list[str]]:
        """Validate password meets security requirements."""
        errors = []

        if len(password) < self.password_min_length:
            errors.append(f"Password must be at least {self.password_min_length} characters long")

        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")

        return len(errors) == 0, errors


__all__ = [
    "User",
    "UserSession",
    "AuditLog",
    "PasswordResetToken",
    "AuthenticationService",
    "UserStatus",
    "SessionStatus",
    "Role",
    "Permission",
    "ROLE_PERMISSIONS"
]
