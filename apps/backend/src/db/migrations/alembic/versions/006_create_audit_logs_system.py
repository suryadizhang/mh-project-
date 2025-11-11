"""create audit logs system

Revision ID: 006_create_audit_logs_system
Revises: 005_add_qr_code_tracking
Create Date: 2025-10-28 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006_create_audit_logs_system'
down_revision: Union[str, None] = '005_add_qr_code_tracking'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create comprehensive audit logging system for all admin actions.
    Tracks WHO, WHAT, WHEN, WHERE, WHY with full context.
    """
    
    # Create audit_action enum (with IF NOT EXISTS check)
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audit_action') THEN
                CREATE TYPE audit_action AS ENUM (
                    'VIEW',
                    'CREATE', 
                    'UPDATE',
                    'DELETE'
                );
            END IF;
        END $$;
    """)
    
    # Create user_role enum (will be used in next migration for users table)
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                CREATE TYPE user_role AS ENUM (
                    'SUPER_ADMIN',
                    'ADMIN',
                    'CUSTOMER_SUPPORT',
                    'STATION_MANAGER'
                );
            END IF;
        END $$;
    """)
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # WHO - User information
        sa.Column('user_id', sa.UUID(), nullable=False, comment='User who performed the action'),
        sa.Column('user_role', sa.String(50), nullable=False, comment='Role of user at time of action'),
        sa.Column('user_name', sa.String(255), nullable=False, comment='Display name of user'),
        sa.Column('user_email', sa.String(255), nullable=False, comment='Email of user'),
        
        # WHAT - Action details
        sa.Column('action', postgresql.ENUM('VIEW', 'CREATE', 'UPDATE', 'DELETE', name='audit_action', create_type=False), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False, comment='Type of resource (booking, customer, etc)'),
        sa.Column('resource_id', sa.String(255), nullable=False, comment='ID of affected resource'),
        sa.Column('resource_name', sa.String(255), nullable=True, comment='Friendly name for UI display'),
        
        # WHERE - Context information
        sa.Column('ip_address', postgresql.INET(), nullable=True, comment='IP address of request'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='Browser/device information'),
        sa.Column('station_id', sa.UUID(), nullable=True, comment='Station context if applicable'),
        
        # WHY - Delete reason (mandatory for DELETE actions)
        sa.Column('delete_reason', sa.Text(), nullable=True, comment='Reason for deletion (required for DELETE)'),
        
        # DETAILS - State changes
        sa.Column('old_values', postgresql.JSONB(), nullable=True, comment='State before change (JSON)'),
        sa.Column('new_values', postgresql.JSONB(), nullable=True, comment='State after change (JSON)'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, comment='Additional context'),
        
        sa.PrimaryKeyConstraint('id'),
        
        # Add check constraint: DELETE actions must have reason >= 10 chars
        sa.CheckConstraint(
            "action != 'DELETE' OR (delete_reason IS NOT NULL AND length(delete_reason) >= 10)",
            name='delete_must_have_reason'
        ),
        
        comment='Comprehensive audit log for all admin actions'
    )
    
    # Create indexes for fast queries
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', [sa.text('created_at DESC')])
    op.create_index('idx_audit_logs_station_id', 'audit_logs', ['station_id'], postgresql_where=sa.text('station_id IS NOT NULL'))
    op.create_index('idx_audit_logs_user_role', 'audit_logs', ['user_role'])
    
    # Composite index for common queries (user + date range)
    op.create_index('idx_audit_logs_user_created', 'audit_logs', ['user_id', sa.text('created_at DESC')])
    
    # Composite index for resource lookups
    op.create_index('idx_audit_logs_resource_action', 'audit_logs', ['resource_type', 'resource_id', 'action'])
    
    print("[SUCCESS] Created audit_logs table with 8 indexes")
    print("[SUCCESS] Created audit_action enum (VIEW, CREATE, UPDATE, DELETE)")
    print("[SUCCESS] Created user_role enum (SUPER_ADMIN, ADMIN, CUSTOMER_SUPPORT, STATION_MANAGER)")
    print("[SUCCESS] Added delete_must_have_reason constraint")


def downgrade() -> None:
    """Remove audit logging system"""
    
    # Drop indexes
    op.drop_index('idx_audit_logs_resource_action', 'audit_logs')
    op.drop_index('idx_audit_logs_user_created', 'audit_logs')
    op.drop_index('idx_audit_logs_user_role', 'audit_logs')
    op.drop_index('idx_audit_logs_station_id', 'audit_logs')
    op.drop_index('idx_audit_logs_created_at', 'audit_logs')
    op.drop_index('idx_audit_logs_action', 'audit_logs')
    op.drop_index('idx_audit_logs_resource', 'audit_logs')
    op.drop_index('idx_audit_logs_user_id', 'audit_logs')
    
    # Drop table
    op.drop_table('audit_logs')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS audit_action")
    op.execute("DROP TYPE IF EXISTS user_role")
    
    print("[ROLLBACK] Dropped audit_logs table and related enums")
