"""add user roles and station assignment

Revision ID: 008_add_user_roles
Revises: 007_add_soft_delete_support
Create Date: 2025-10-28 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '008_add_user_roles'
down_revision: Union[str, None] = '007_add_soft_delete_support'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add 4-tier role system and station assignment to users table.
    Roles: SUPER_ADMIN, ADMIN, CUSTOMER_SUPPORT, STATION_MANAGER
    """
    
    # Check if role column already exists
    conn = op.get_bind()
    role_check = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'users' 
        AND column_name = 'role'
    """))
    
    if role_check.fetchone() is None:
        # Add role column (user_role enum was created in migration 006)
        op.add_column(
            'users',
            sa.Column(
                'role',
                postgresql.ENUM('SUPER_ADMIN', 'ADMIN', 'CUSTOMER_SUPPORT', 'STATION_MANAGER', name='user_role'),
                nullable=True,  # Temporarily nullable for migration
                server_default='CUSTOMER_SUPPORT',
                comment='User role for RBAC'
            )
        )
        print("[SUCCESS] Added role column to users table")
    else:
        print("[SKIP] role column already exists in users table")
    
    # Check if assigned_station_id column already exists
    station_check = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'users' 
        AND column_name = 'assigned_station_id'
    """))
    
    if station_check.fetchone() is None:
        # Add station assignment for STATION_MANAGER role
        op.add_column(
            'users',
            sa.Column(
                'assigned_station_id',
                sa.UUID(),
                nullable=True,
                comment='Station assigned to STATION_MANAGER (NULL for other roles)'
            )
        )
        print("[SUCCESS] Added assigned_station_id column to users table")
    else:
        print("[SKIP] assigned_station_id column already exists in users table")
    
    # Create foreign key to stations table (if it exists)
    # Note: Uncomment this if stations table exists
    # op.create_foreign_key(
    #     'fk_users_assigned_station',
    #     'users',
    #     'stations',
    #     ['assigned_station_id'],
    #     ['id'],
    #     ondelete='SET NULL'
    # )
    
    # Migrate existing users based on their current role values
    print("\n[MIGRATION] Migrating existing users to new role system...")
    
    # Map existing roles to new role system:
    # - 'super_admin' -> 'SUPER_ADMIN'
    # - 'admin' -> 'ADMIN'
    # - 'staff' -> 'CUSTOMER_SUPPORT'
    # - 'customer' -> 'CUSTOMER_SUPPORT' (default)
    
    # Update super_admin users
    op.execute("""
        UPDATE users 
        SET role = 'SUPER_ADMIN' 
        WHERE role = 'super_admin'
    """)
    
    # Update admin users
    op.execute("""
        UPDATE users 
        SET role = 'ADMIN' 
        WHERE role = 'admin'
    """)
    
    # Update staff users to CUSTOMER_SUPPORT
    op.execute("""
        UPDATE users 
        SET role = 'CUSTOMER_SUPPORT' 
        WHERE role IN ('staff', 'customer')
    """)
    
    # Set CUSTOMER_SUPPORT as default for any remaining NULL or unknown roles
    op.execute("""
        UPDATE users 
        SET role = 'CUSTOMER_SUPPORT'
        WHERE role IS NULL 
        OR role NOT IN ('SUPER_ADMIN', 'ADMIN', 'CUSTOMER_SUPPORT', 'STATION_MANAGER')
    """)
    
    # Drop old CHECK constraint
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_role_valid CASCADE")
    
    # Add new CHECK constraint for new role values
    op.execute("""
        ALTER TABLE users ADD CONSTRAINT ck_users_role_valid 
        CHECK (role IN ('SUPER_ADMIN', 'ADMIN', 'CUSTOMER_SUPPORT', 'STATION_MANAGER'))
    """)
    
    # Now make role NOT NULL (it should already be NOT NULL from base migration)
    op.alter_column('users', 'role', nullable=False)
    
    # Drop old role index if it exists
    op.execute("DROP INDEX IF EXISTS idx_users_role CASCADE")
    
    # Create new index for role-based queries
    op.create_index('idx_users_role', 'users', ['role'])
    
    # Create index for station managers
    op.create_index(
        'idx_users_station_manager',
        'users',
        ['assigned_station_id'],
        postgresql_where=sa.text("role = 'STATION_MANAGER'")
    )
    
    print("\n[SUCCESS] User role system configured!")
    print("\n[ROLE HIERARCHY]")
    print("   1. SUPER_ADMIN - Full system access")
    print("   2. ADMIN - Most operations, cannot manage admins")
    print("   3. CUSTOMER_SUPPORT - Customer-facing operations")
    print("   4. STATION_MANAGER - Station-specific operations")
    print("\n[NEXT STEPS]")
    print("   1. Update SUPER_ADMIN emails in migration if needed")
    print("   2. Assign stations to STATION_MANAGER users")
    print("   3. Review and adjust user roles as needed")


def downgrade() -> None:
    """Remove role system"""
    
    # Drop indexes
    op.drop_index('idx_users_station_manager', 'users')
    op.drop_index('idx_users_role', 'users')
    
    # Drop foreign key if it was created
    # op.drop_constraint('fk_users_assigned_station', 'users', type_='foreignkey')
    
    # Drop columns
    op.drop_column('users', 'assigned_station_id')
    op.drop_column('users', 'role')
    
    print("[ROLLBACK] Removed user role system")
