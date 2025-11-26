from typing import Any, Optional
import datetime
import decimal
import uuid

from sqlalchemy import ARRAY, Boolean, CheckConstraint, DateTime, Enum, ForeignKeyConstraint, Index, Integer, JSON, Numeric, PrimaryKeyConstraint, String, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Businesses(Base):
    __tablename__ = 'businesses'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='businesses_pkey'),
        UniqueConstraint('domain', name='businesses_domain_key'),
        UniqueConstraint('slug', name='businesses_slug_key')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'America/Los_Angeles'::character varying"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'USD'::character varying"))
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    subscription_tier: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'self_hosted'::character varying"))
    subscription_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'active'::character varying"))
    monthly_fee: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default=text('0.00'))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('now()'))
    domain: Mapped[Optional[str]] = mapped_column(String(255))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    primary_color: Mapped[Optional[str]] = mapped_column(String(7), server_default=text("'#FF6B6B'::character varying"))
    secondary_color: Mapped[Optional[str]] = mapped_column(String(7), server_default=text("'#4ECDC4'::character varying"))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    address: Mapped[Optional[str]] = mapped_column(Text)

    users: Mapped[list['Users_']] = relationship('Users_', back_populates='business')


class Permissions(Base):
    __tablename__ = 'permissions'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='permissions_pkey'),
        UniqueConstraint('name', name='permissions_name_key'),
        Index('idx_permissions_action', 'action'),
        Index('idx_permissions_name', 'name', unique=True),
        Index('idx_permissions_resource', 'resource'),
        {'schema': 'identity'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(Enum('user:create', 'user:read', 'user:update', 'user:delete', 'user:approve', 'station:create', 'station:read', 'station:update', 'station:delete', 'booking:create', 'booking:read', 'booking:update', 'booking:delete', 'booking:cancel', 'customer:create', 'customer:read', 'customer:update', 'customer:delete', 'payment:create', 'payment:read', 'payment:refund', 'review:read', 'review:moderate', 'review:respond', 'analytics:view', 'analytics:export', 'settings:read', 'settings:update', name='permissiontype'), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    description: Mapped[Optional[str]] = mapped_column(Text)

    role_permissions: Mapped[list['RolePermissions']] = relationship('RolePermissions', back_populates='permission')


class Stations(Base):
    __tablename__ = 'stations'
    __table_args__ = (
        CheckConstraint('booking_lead_time_hours >= 0', name='station_lead_time_non_negative'),
        CheckConstraint('max_concurrent_bookings > 0', name='station_max_bookings_positive'),
        CheckConstraint("status::text = ANY (ARRAY['active'::character varying, 'inactive'::character varying, 'suspended'::character varying, 'maintenance'::character varying]::text[])", name='station_status_valid'),
        PrimaryKeyConstraint('id', name='stations_pkey'),
        UniqueConstraint('code', name='unique_station_code'),
        Index('idx_station_code', 'code'),
        Index('idx_station_status', 'status'),
        {'schema': 'identity'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, server_default=text("'US'::character varying"))
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'America/New_York'::character varying"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'active'::character varying"))
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, server_default=text("'{}'::json"))
    max_concurrent_bookings: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('10'))
    booking_lead_time_hours: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('24'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    business_hours: Mapped[Optional[dict]] = mapped_column(JSON)
    service_area_radius: Mapped[Optional[int]] = mapped_column(Integer)
    branding_config: Mapped[Optional[dict]] = mapped_column(JSON)

    station_access_tokens: Mapped[list['StationAccessTokens']] = relationship('StationAccessTokens', back_populates='station')
    station_audit_logs: Mapped[list['StationAuditLogs']] = relationship('StationAuditLogs', back_populates='station')
    station_users: Mapped[list['StationUsers']] = relationship('StationUsers', back_populates='station')


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint("role::text = ANY (ARRAY['customer'::character varying, 'admin'::character varying, 'super_admin'::character varying, 'staff'::character varying]::text[])", name='ck_users_role_valid'),
        PrimaryKeyConstraint('id', name='users_pkey'),
        UniqueConstraint('email', name='uq_users_email'),
        Index('idx_users_active', 'is_active'),
        Index('idx_users_email', 'email', unique=True),
        Index('idx_users_role', 'role')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'customer'::character varying"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    phone: Mapped[Optional[str]] = mapped_column(String(20))

    station_access_tokens: Mapped[list['StationAccessTokens']] = relationship('StationAccessTokens', back_populates='user')
    station_audit_logs: Mapped[list['StationAuditLogs']] = relationship('StationAuditLogs', back_populates='user')
    station_users: Mapped[list['StationUsers']] = relationship('StationUsers', foreign_keys='[StationUsers.assigned_by]', back_populates='users')
    station_users_: Mapped[list['StationUsers']] = relationship('StationUsers', foreign_keys='[StationUsers.user_id]', back_populates='user')


class StationAccessTokens(Base):
    __tablename__ = 'station_access_tokens'
    __table_args__ = (
        ForeignKeyConstraint(['station_id'], ['identity.stations.id'], ondelete='CASCADE', name='station_access_tokens_station_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='station_access_tokens_user_id_fkey'),
        PrimaryKeyConstraint('id', name='station_access_tokens_pkey'),
        UniqueConstraint('jwt_id', name='unique_station_jwt_id'),
        UniqueConstraint('token_hash', name='unique_station_token_hash'),
        Index('idx_station_token_expires', 'expires_at'),
        Index('idx_station_token_revoked', 'is_revoked'),
        Index('idx_station_token_user_station', 'user_id', 'station_id'),
        {'schema': 'identity'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    station_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    jwt_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    permissions: Mapped[dict] = mapped_column(JSON, nullable=False, server_default=text("'[]'::json"))
    issued_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    scope: Mapped[Optional[str]] = mapped_column(String(500))
    revoked_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    station: Mapped['Stations'] = relationship('Stations', back_populates='station_access_tokens')
    user: Mapped['Users'] = relationship('Users', back_populates='station_access_tokens')


class StationAuditLogs(Base):
    __tablename__ = 'station_audit_logs'
    __table_args__ = (
        ForeignKeyConstraint(['station_id'], ['identity.stations.id'], ondelete='CASCADE', name='station_audit_logs_station_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL', name='station_audit_logs_user_id_fkey'),
        PrimaryKeyConstraint('id', name='station_audit_logs_pkey'),
        Index('idx_station_audit_created', 'created_at'),
        Index('idx_station_audit_resource', 'station_id', 'resource_type', 'resource_id'),
        Index('idx_station_audit_user_action', 'station_id', 'user_id', 'action'),
        {'schema': 'identity'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    station_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, server_default=text("'{}'::json"))
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50))
    resource_id: Mapped[Optional[str]] = mapped_column(String(50))
    user_role: Mapped[Optional[str]] = mapped_column(String(30))
    permissions_used: Mapped[Optional[dict]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    station: Mapped['Stations'] = relationship('Stations', back_populates='station_audit_logs')
    user: Mapped[Optional['Users']] = relationship('Users', back_populates='station_audit_logs')


class Users_(Base):
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint("role = ANY (ARRAY['SUPER_ADMIN'::user_role, 'ADMIN'::user_role, 'CUSTOMER_SUPPORT'::user_role, 'STATION_MANAGER'::user_role])", name='ck_users_role_valid'),
        ForeignKeyConstraint(['approved_by'], ['identity.users.id'], ondelete='SET NULL', name='fk_users_approved_by'),
        ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE', name='fk_users_business'),
        PrimaryKeyConstraint('id', name='users_pkey'),
        Index('idx_users_business_id', 'business_id'),
        Index('idx_users_email', 'email', unique=True),
        Index('idx_users_email_lower', unique=True),
        Index('idx_users_google_id', 'google_id', unique=True),
        Index('idx_users_id', 'id'),
        Index('idx_users_ip_verification', 'ip_verification_enabled'),
        Index('idx_users_last_login', 'last_login_at'),
        Index('idx_users_provider_status', 'auth_provider', 'status'),
        Index('idx_users_role', 'role'),
        Index('idx_users_station_manager', 'assigned_station_id'),
        Index('idx_users_status', 'status'),
        Index('idx_users_status_created', 'status', 'created_at'),
        {'schema': 'identity'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_provider: Mapped[str] = mapped_column(Enum('google', 'email', 'microsoft', 'apple', name='authprovider'), nullable=False, server_default=text("'email'::authprovider"))
    status: Mapped[str] = mapped_column(Enum('pending', 'active', 'suspended', 'deactivated', name='userstatus'), nullable=False, server_default=text("'pending'::userstatus"))
    is_super_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    user_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    role: Mapped[str] = mapped_column(Enum('SUPER_ADMIN', 'ADMIN', 'CUSTOMER_SUPPORT', 'STATION_MANAGER', name='user_role'), nullable=False, server_default=text("'CUSTOMER_SUPPORT'::user_role"), comment='User role for RBAC')
    business_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    ip_verification_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    google_id: Mapped[Optional[str]] = mapped_column(String(255))
    microsoft_id: Mapped[Optional[str]] = mapped_column(String(255))
    apple_id: Mapped[Optional[str]] = mapped_column(String(255))
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255))
    password_changed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    email_verified_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(255))
    backup_codes: Mapped[Optional[dict]] = mapped_column(JSONB)
    locked_until: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    last_login_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45))
    last_activity_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    approved_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    approval_notes: Mapped[Optional[str]] = mapped_column(Text)
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    assigned_station_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, comment='Station assigned to STATION_MANAGER (NULL for other roles)')
    mfa_backup_codes: Mapped[Optional[dict]] = mapped_column(JSONB)
    trusted_ips: Mapped[Optional[list[Any]]] = mapped_column(ARRAY(INET()))
    last_known_ip: Mapped[Optional[Any]] = mapped_column(INET)

    users: Mapped[Optional['Users_']] = relationship('Users_', remote_side=[id], back_populates='users_reverse')
    users_reverse: Mapped[list['Users_']] = relationship('Users_', remote_side=[approved_by], back_populates='users')
    business: Mapped['Businesses'] = relationship('Businesses', back_populates='users')
    roles: Mapped[list['Roles']] = relationship('Roles', back_populates='users')
    station_users: Mapped[list['StationUsers']] = relationship('StationUsers', back_populates='user_')
    user_roles: Mapped[list['UserRoles']] = relationship('UserRoles', foreign_keys='[UserRoles.assigned_by]', back_populates='users')
    user_roles_: Mapped[list['UserRoles']] = relationship('UserRoles', foreign_keys='[UserRoles.user_id]', back_populates='user')


class Roles(Base):
    __tablename__ = 'roles'
    __table_args__ = (
        ForeignKeyConstraint(['created_by'], ['identity.users.id'], ondelete='SET NULL', name='roles_created_by_fkey'),
        PrimaryKeyConstraint('id', name='roles_pkey'),
        UniqueConstraint('name', name='roles_name_key'),
        Index('idx_roles_created_at', 'created_at'),
        Index('idx_roles_name', 'name', unique=True),
        {'schema': 'identity'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(Enum('super_admin', 'admin', 'manager', 'staff', 'viewer', name='roletype'), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_system_role: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    users: Mapped[Optional['Users_']] = relationship('Users_', back_populates='roles')
    role_permissions: Mapped[list['RolePermissions']] = relationship('RolePermissions', back_populates='role')
    user_roles: Mapped[list['UserRoles']] = relationship('UserRoles', back_populates='role')


class StationUsers(Base):
    __tablename__ = 'station_users'
    __table_args__ = (
        CheckConstraint("role::text = ANY (ARRAY['super_admin'::character varying, 'admin'::character varying, 'station_admin'::character varying, 'customer_support'::character varying]::text[])", name='station_user_role_valid'),
        ForeignKeyConstraint(['assigned_by'], ['users.id'], ondelete='SET NULL', name='station_users_assigned_by_fkey'),
        ForeignKeyConstraint(['station_id'], ['identity.stations.id'], ondelete='CASCADE', name='station_users_station_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='station_users_user_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['identity.users.id'], ondelete='CASCADE', name='fk_station_users_user_id'),
        PrimaryKeyConstraint('id', name='station_users_pkey'),
        UniqueConstraint('user_id', 'station_id', name='unique_user_station'),
        Index('idx_station_user_active', 'user_id', 'station_id', 'is_active'),
        Index('idx_station_user_primary', 'user_id', 'is_primary_station'),
        Index('idx_station_users_user_id', 'user_id'),
        {'schema': 'identity'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    station_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'customer_support'::character varying"))
    additional_permissions: Mapped[dict] = mapped_column(JSON, nullable=False, server_default=text("'[]'::json"))
    assigned_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    is_primary_station: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    assigned_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    users: Mapped[Optional['Users']] = relationship('Users', foreign_keys=[assigned_by], back_populates='station_users')
    station: Mapped['Stations'] = relationship('Stations', back_populates='station_users')
    user: Mapped['Users'] = relationship('Users', foreign_keys=[user_id], back_populates='station_users_')
    user_: Mapped['Users_'] = relationship('Users_', back_populates='station_users')


class RolePermissions(Base):
    __tablename__ = 'role_permissions'
    __table_args__ = (
        ForeignKeyConstraint(['permission_id'], ['identity.permissions.id'], ondelete='CASCADE', name='role_permissions_permission_id_fkey'),
        ForeignKeyConstraint(['role_id'], ['identity.roles.id'], ondelete='CASCADE', name='role_permissions_role_id_fkey'),
        PrimaryKeyConstraint('role_id', 'permission_id', name='role_permissions_pkey'),
        {'schema': 'identity'}
    )

    role_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    permission: Mapped['Permissions'] = relationship('Permissions', back_populates='role_permissions')
    role: Mapped['Roles'] = relationship('Roles', back_populates='role_permissions')


class UserRoles(Base):
    __tablename__ = 'user_roles'
    __table_args__ = (
        ForeignKeyConstraint(['assigned_by'], ['identity.users.id'], ondelete='SET NULL', name='user_roles_assigned_by_fkey'),
        ForeignKeyConstraint(['role_id'], ['identity.roles.id'], ondelete='CASCADE', name='user_roles_role_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['identity.users.id'], ondelete='CASCADE', name='user_roles_user_id_fkey'),
        PrimaryKeyConstraint('user_id', 'role_id', name='user_roles_pkey'),
        {'schema': 'identity'}
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    assigned_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    assigned_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    users: Mapped[Optional['Users_']] = relationship('Users_', foreign_keys=[assigned_by], back_populates='user_roles')
    role: Mapped['Roles'] = relationship('Roles', back_populates='user_roles')
    user: Mapped['Users_'] = relationship('Users_', foreign_keys=[user_id], back_populates='user_roles_')
