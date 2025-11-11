"""Create base users table for authentication

Revision ID: 000_create_base_users
Revises: 
Create Date: 2025-10-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '000_create_base_users'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create base users table in public schema for authentication."""
    
    # Create users table in public schema (default)
    # This is the foundational table that other tables reference
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('role', sa.String(20), nullable=False, server_default='customer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.CheckConstraint("role IN ('customer', 'admin', 'super_admin', 'staff')", name='ck_users_role_valid')
    )
    
    # Create indexes for users table
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_users_active', 'users', ['is_active'])


def downgrade() -> None:
    """Drop users table."""
    op.drop_index('idx_users_active')
    op.drop_index('idx_users_role')
    op.drop_index('idx_users_email')
    op.drop_table('users')
