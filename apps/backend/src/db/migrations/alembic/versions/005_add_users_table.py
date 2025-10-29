"""Add users table for Google OAuth authentication

Revision ID: 005_add_users_table
Revises: ea9069521d16
Create Date: 2025-10-28 23:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_users_table'
down_revision = 'ea9069521d16'
branch_labels = None
depends_on = None


def upgrade():
    # Create users table in identity schema
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.Text, nullable=True),
        
        # Authentication
        sa.Column('auth_provider', sa.Enum('google', 'email', 'microsoft', 'apple', name='authprovider'), nullable=False, server_default='email'),
        sa.Column('google_id', sa.String(255), nullable=True),
        sa.Column('microsoft_id', sa.String(255), nullable=True),
        sa.Column('apple_id', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Status and permissions
        sa.Column('status', sa.Enum('pending', 'active', 'suspended', 'deactivated', name='userstatus'), nullable=False, server_default='pending'),
        sa.Column('is_super_admin', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_email_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        
        # Security
        sa.Column('mfa_enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('mfa_secret', sa.String(255), nullable=True),
        sa.Column('backup_codes', postgresql.JSONB, nullable=True),
        sa.Column('failed_login_attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        
        # Session management
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_ip', sa.String(45), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        
        # Approval workflow
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_notes', sa.Text, nullable=True),
        
        # Metadata
        sa.Column('settings', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('user_metadata', postgresql.JSONB, nullable=False, server_default='{}'),  # Renamed from 'metadata' to avoid SQLAlchemy conflict
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        
        schema='identity'
    )
    
    # Create indexes
    op.create_index('idx_users_id', 'users', ['id'], schema='identity')
    op.create_index('idx_users_email', 'users', ['email'], unique=True, schema='identity')
    op.create_index('idx_users_email_lower', 'users', [sa.text('LOWER(email)')], unique=True, schema='identity')
    op.create_index('idx_users_google_id', 'users', ['google_id'], unique=True, schema='identity', postgresql_where=sa.text('google_id IS NOT NULL'))
    op.create_index('idx_users_status', 'users', ['status'], schema='identity')
    op.create_index('idx_users_status_created', 'users', ['status', sa.text('created_at DESC')], schema='identity')
    op.create_index('idx_users_provider_status', 'users', ['auth_provider', 'status'], schema='identity')
    op.create_index('idx_users_last_login', 'users', [sa.text('last_login_at DESC')], schema='identity')
    
    # Note: user_id column already exists in station_users table, skipping add_column
    # Add foreign key to station_users table if not already exists
    try:
        op.create_foreign_key('fk_station_users_user_id', 'station_users', 'users', ['user_id'], ['id'], source_schema='identity', referent_schema='identity', ondelete='CASCADE')
    except:
        pass  # Foreign key might already exist
    
    try:
        op.create_index('idx_station_users_user_id', 'station_users', ['user_id'], schema='identity')
    except:
        pass  # Index might already exist
    
    # Add foreign key for approved_by
    op.create_foreign_key('fk_users_approved_by', 'users', 'users', ['approved_by'], ['id'], source_schema='identity', referent_schema='identity', ondelete='SET NULL')
    
    print("✅ Users table created successfully")
    print("   - Email + Google OAuth authentication supported")
    print("   - Pending approval workflow for new users")
    print("   - Super admin designation")
    print("   - MFA support")


def downgrade():
    # Remove foreign keys first
    op.drop_constraint('fk_users_approved_by', 'users', schema='identity', type_='foreignkey')
    op.drop_constraint('fk_station_users_user_id', 'station_users', schema='identity', type_='foreignkey')
    op.drop_column('station_users', 'user_id', schema='identity')
    
    # Drop indexes
    op.drop_index('idx_station_users_user_id', 'station_users', schema='identity')
    op.drop_index('idx_users_last_login', 'users', schema='identity')
    op.drop_index('idx_users_provider_status', 'users', schema='identity')
    op.drop_index('idx_users_status_created', 'users', schema='identity')
    op.drop_index('idx_users_status', 'users', schema='identity')
    op.drop_index('idx_users_google_id', 'users', schema='identity')
    op.drop_index('idx_users_email_lower', 'users', schema='identity')
    op.drop_index('idx_users_email', 'users', schema='identity')
    op.drop_index('idx_users_id', 'users', schema='identity')
    
    # Drop table
    op.drop_table('users', schema='identity')
    
    # Drop enums
    sa.Enum(name='userstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='authprovider').drop(op.get_bind(), checkfirst=True)
