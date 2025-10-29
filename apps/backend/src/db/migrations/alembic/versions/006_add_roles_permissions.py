"""Create roles and permissions tables

Revision ID: 006_add_roles_permissions
Revises: 005_add_users_table
Create Date: 2025-10-29 07:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '006_add_roles_permissions'
down_revision = '005_add_users_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create role and permission enums
    roletype_enum = postgresql.ENUM(
        'super_admin', 'admin', 'manager', 'staff', 'viewer',
        name='roletype',
        create_type=True
    )
    roletype_enum.create(op.get_bind())
    
    permissiontype_enum = postgresql.ENUM(
        'user:create', 'user:read', 'user:update', 'user:delete', 'user:approve',
        'station:create', 'station:read', 'station:update', 'station:delete',
        'booking:create', 'booking:read', 'booking:update', 'booking:delete', 'booking:cancel',
        'customer:create', 'customer:read', 'customer:update', 'customer:delete',
        'payment:create', 'payment:read', 'payment:refund',
        'review:read', 'review:moderate', 'review:respond',
        'analytics:view', 'analytics:export',
        'settings:read', 'settings:update',
        name='permissiontype',
        create_type=True
    )
    permissiontype_enum.create(op.get_bind())
    
    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.Enum('user:create', 'user:read', 'user:update', 'user:delete', 'user:approve',
                                   'station:create', 'station:read', 'station:update', 'station:delete',
                                   'booking:create', 'booking:read', 'booking:update', 'booking:delete', 'booking:cancel',
                                   'customer:create', 'customer:read', 'customer:update', 'customer:delete',
                                   'payment:create', 'payment:read', 'payment:refund',
                                   'review:read', 'review:moderate', 'review:respond',
                                   'analytics:view', 'analytics:export',
                                   'settings:read', 'settings:update',
                                   name='permissiontype'), unique=True, nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('resource', sa.String(50), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='identity'
    )
    
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.Enum('super_admin', 'admin', 'manager', 'staff', 'viewer', name='roletype'), 
                  unique=True, nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_system_role', sa.Boolean, default=False, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('identity.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('settings', postgresql.JSONB, default={}, nullable=False),
        schema='identity'
    )
    
    # Create role_permissions association table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('identity.roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('identity.permissions.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema='identity'
    )
    
    # Create user_roles association table
    op.create_table(
        'user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('identity.users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('identity.roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('identity.users.id', ondelete='SET NULL'), nullable=True),
        schema='identity'
    )
    
    # Create indexes
    op.create_index('idx_permissions_name', 'permissions', ['name'], unique=True, schema='identity')
    op.create_index('idx_permissions_resource', 'permissions', ['resource'], schema='identity')
    op.create_index('idx_permissions_action', 'permissions', ['action'], schema='identity')
    op.create_index('idx_roles_name', 'roles', ['name'], unique=True, schema='identity')
    op.create_index('idx_roles_created_at', 'roles', ['created_at'], schema='identity')
    
    print("✅ Roles and permissions tables created successfully")


def downgrade() -> None:
    # Drop tables
    op.drop_table('user_roles', schema='identity')
    op.drop_table('role_permissions', schema='identity')
    op.drop_table('roles', schema='identity')
    op.drop_table('permissions', schema='identity')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS identity.roletype')
    op.execute('DROP TYPE IF EXISTS identity.permissiontype')
    
    print("✅ Roles and permissions tables dropped successfully")
