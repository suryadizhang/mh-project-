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
    # Check if enums exist and create them if needed using raw SQL
    conn = op.get_bind()
    
    # Check for roletype enum
    roletype_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'roletype'
        )
    """)).scalar()
    
    if not roletype_exists:
        conn.execute(sa.text("""
            CREATE TYPE roletype AS ENUM (
                'super_admin', 'admin', 'manager', 'staff', 'viewer'
            )
        """))
        print("✅ Created roletype enum")
    else:
        print("[SKIP] roletype enum already exists")
    
    # Check for permissiontype enum
    permissiontype_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'permissiontype'
        )
    """)).scalar()
    
    if not permissiontype_exists:
        conn.execute(sa.text("""
            CREATE TYPE permissiontype AS ENUM (
                'user:create', 'user:read', 'user:update', 'user:delete', 'user:approve',
                'station:create', 'station:read', 'station:update', 'station:delete',
                'booking:create', 'booking:read', 'booking:update', 'booking:delete', 'booking:cancel',
                'customer:create', 'customer:read', 'customer:update', 'customer:delete',
                'payment:create', 'payment:read', 'payment:refund',
                'review:read', 'review:moderate', 'review:respond',
                'analytics:view', 'analytics:export',
                'settings:read', 'settings:update'
            )
        """))
        print("✅ Created permissiontype enum")
    else:
        print("[SKIP] permissiontype enum already exists")
    
    # Check if permissions table exists
    permissions_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'identity' 
            AND table_name = 'permissions'
        )
    """)).scalar()
    
    if not permissions_exists:
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
        print("✅ Created permissions table")
    else:
        print("[SKIP] permissions table already exists")
    
    # Check if roles table exists
    roles_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'identity' 
            AND table_name = 'roles'
        )
    """)).scalar()
    
    if not roles_exists:
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
        print("✅ Created roles table")
    else:
        print("[SKIP] roles table already exists")
    
    # Check if role_permissions table exists
    role_permissions_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'identity' 
            AND table_name = 'role_permissions'
        )
    """)).scalar()
    
    if not role_permissions_exists:
        # Create role_permissions association table
        op.create_table(
            'role_permissions',
            sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('identity.roles.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('identity.permissions.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            schema='identity'
        )
        print("✅ Created role_permissions table")
    else:
        print("[SKIP] role_permissions table already exists")
    
    # Check if user_roles table exists
    user_roles_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'identity' 
            AND table_name = 'user_roles'
        )
    """)).scalar()
    
    if not user_roles_exists:
        # Create user_roles association table
        op.create_table(
            'user_roles',
            sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('identity.users.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('identity.roles.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('identity.users.id', ondelete='SET NULL'), nullable=True),
            schema='identity'
        )
        print("✅ Created user_roles table")
    else:
        print("[SKIP] user_roles table already exists")
    
    # Check and create indexes only if they don't exist
    try:
        op.create_index('idx_permissions_name', 'permissions', ['name'], unique=True, schema='identity', if_not_exists=True)
    except:
        print("[SKIP] idx_permissions_name already exists")
    
    try:
        op.create_index('idx_permissions_resource', 'permissions', ['resource'], schema='identity', if_not_exists=True)
    except:
        print("[SKIP] idx_permissions_resource already exists")
    
    try:
        op.create_index('idx_permissions_action', 'permissions', ['action'], schema='identity', if_not_exists=True)
    except:
        print("[SKIP] idx_permissions_action already exists")
    
    try:
        op.create_index('idx_roles_name', 'roles', ['name'], unique=True, schema='identity', if_not_exists=True)
    except:
        print("[SKIP] idx_roles_name already exists")
    
    try:
        op.create_index('idx_roles_created_at', 'roles', ['created_at'], schema='identity', if_not_exists=True)
    except:
        print("[SKIP] idx_roles_created_at already exists")
    
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
