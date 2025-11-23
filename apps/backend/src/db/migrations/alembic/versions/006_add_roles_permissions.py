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
        # Create permissions table using raw SQL to avoid SQLAlchemy's automatic ENUM creation
        conn.execute(sa.text("""
            CREATE TABLE identity.permissions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name permissiontype UNIQUE NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                description TEXT,
                resource VARCHAR(50) NOT NULL,
                action VARCHAR(50) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))
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
        # Create roles table using raw SQL to avoid SQLAlchemy's automatic ENUM creation
        conn.execute(sa.text("""
            CREATE TABLE identity.roles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name roletype UNIQUE NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                description TEXT,
                is_system_role BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                created_by UUID REFERENCES identity.users(id) ON DELETE SET NULL,
                settings JSONB NOT NULL DEFAULT '{}'::jsonb
            )
        """))
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
        # Create role_permissions association table using raw SQL
        conn.execute(sa.text("""
            CREATE TABLE identity.role_permissions (
                role_id UUID NOT NULL REFERENCES identity.roles(id) ON DELETE CASCADE,
                permission_id UUID NOT NULL REFERENCES identity.permissions(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (role_id, permission_id)
            )
        """))
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
        # Create user_roles association table using raw SQL
        conn.execute(sa.text("""
            CREATE TABLE identity.user_roles (
                user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
                role_id UUID NOT NULL REFERENCES identity.roles(id) ON DELETE CASCADE,
                assigned_at TIMESTAMPTZ DEFAULT NOW(),
                assigned_by UUID REFERENCES identity.users(id) ON DELETE SET NULL,
                PRIMARY KEY (user_id, role_id)
            )
        """))
        print("✅ Created user_roles table")
    else:
        print("[SKIP] user_roles table already exists")
    
    # Create indexes using raw SQL with IF NOT EXISTS
    conn.execute(sa.text("CREATE UNIQUE INDEX IF NOT EXISTS idx_permissions_name ON identity.permissions(name)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_permissions_resource ON identity.permissions(resource)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_permissions_action ON identity.permissions(action)"))
    conn.execute(sa.text("CREATE UNIQUE INDEX IF NOT EXISTS idx_roles_name ON identity.roles(name)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_roles_created_at ON identity.roles(created_at)"))
    
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
