"""Multi-tenant station architecture migration

Revision ID: 004_station_rbac
Revises: 003_add_lead_newsletter_schemas
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_station_rbac'
down_revision = '003_add_lead_newsletter_schemas'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add multi-tenant station architecture with RBAC."""
    
    # Create identity schema for station/user/RBAC tables
    op.execute("CREATE SCHEMA IF NOT EXISTS identity")
    
    # Create stations table
    op.create_table(
        'stations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('country', sa.String(100), nullable=False, server_default="US"),
        sa.Column('timezone', sa.String(50), nullable=False, server_default="America/New_York"),
        sa.Column('status', sa.String(20), nullable=False, server_default="active"),
        sa.Column('settings', sa.JSON(), nullable=False, server_default="{}"),
        sa.Column('business_hours', sa.JSON(), nullable=True),
        sa.Column('service_area_radius', sa.Integer(), nullable=True),
        sa.Column('max_concurrent_bookings', sa.Integer(), nullable=False, server_default="10"),
        sa.Column('booking_lead_time_hours', sa.Integer(), nullable=False, server_default="24"),
        sa.Column('branding_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='unique_station_code'),
        sa.CheckConstraint("status IN ('active', 'inactive', 'suspended', 'maintenance')", name='station_status_valid'),
        sa.CheckConstraint('max_concurrent_bookings > 0', name='station_max_bookings_positive'),
        sa.CheckConstraint('booking_lead_time_hours >= 0', name='station_lead_time_non_negative'),
        schema='identity'
    )
    
    # Create indexes for stations
    op.create_index('idx_station_status', 'stations', ['status'], schema='identity')
    op.create_index('idx_station_code', 'stations', ['code'], schema='identity')
    
    # Create station_users junction table for user-station assignments
    op.create_table(
        'station_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('station_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(30), nullable=False, server_default="customer_support"),
        sa.Column('additional_permissions', sa.JSON(), nullable=False, server_default="[]"),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default="true"),
        sa.Column('is_primary_station', sa.Boolean(), nullable=False, server_default="false"),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        # Reference public.users table (created in 000_create_base_users migration)
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['station_id'], ['identity.stations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('user_id', 'station_id', name='unique_user_station'),
        sa.CheckConstraint("role IN ('super_admin', 'admin', 'station_admin', 'customer_support')", name='station_user_role_valid'),
        schema='identity'
    )
    
    # Create indexes for station_users
    op.create_index('idx_station_user_active', 'station_users', ['user_id', 'station_id', 'is_active'], schema='identity')
    op.create_index('idx_station_user_primary', 'station_users', ['user_id', 'is_primary_station'], schema='identity')
    
    # Create station audit logs table
    op.create_table(
        'station_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('station_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(50), nullable=True),
        sa.Column('user_role', sa.String(30), nullable=True),
        sa.Column('permissions_used', sa.JSON(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=False, server_default="{}"),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['station_id'], ['identity.stations.id'], ondelete='CASCADE'),
        # Reference public.users table
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        # Note: user_sessions table doesn't exist yet, will be added in future migration
        # sa.ForeignKeyConstraint(['session_id'], ['identity.user_sessions.id'], ondelete='SET NULL'),
        schema='identity'
    )
    
    # Create indexes for station audit logs
    op.create_index('idx_station_audit_user_action', 'station_audit_logs', ['station_id', 'user_id', 'action'], schema='identity')
    op.create_index('idx_station_audit_created', 'station_audit_logs', ['created_at'], schema='identity')
    op.create_index('idx_station_audit_resource', 'station_audit_logs', ['station_id', 'resource_type', 'resource_id'], schema='identity')
    
    # Create station access tokens table
    op.create_table(
        'station_access_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('station_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(100), nullable=False),
        sa.Column('jwt_id', sa.String(36), nullable=False),
        sa.Column('role', sa.String(30), nullable=False),
        sa.Column('permissions', sa.JSON(), nullable=False, server_default="[]"),
        sa.Column('scope', sa.String(500), nullable=True),
        sa.Column('issued_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint('id'),
        # Reference public.users table
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['station_id'], ['identity.stations.id'], ondelete='CASCADE'),
        # Note: user_sessions table doesn't exist yet, will be added in future migration
        # sa.ForeignKeyConstraint(['session_id'], ['identity.user_sessions.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('token_hash', name='unique_station_token_hash'),
        sa.UniqueConstraint('jwt_id', name='unique_station_jwt_id'),
        schema='identity'
    )
    
    # Create indexes for station access tokens
    op.create_index('idx_station_token_user_station', 'station_access_tokens', ['user_id', 'station_id'], schema='identity')
    op.create_index('idx_station_token_expires', 'station_access_tokens', ['expires_at'], schema='identity')
    op.create_index('idx_station_token_revoked', 'station_access_tokens', ['is_revoked'], schema='identity')
    
    # Add station_id to existing core tables for multi-tenant isolation
    
    # Add station_id to customers table
    op.add_column('customers', sa.Column('station_id', postgresql.UUID(as_uuid=True), nullable=True), schema='core')
    
    # Add station_id to bookings table
    op.add_column('bookings', sa.Column('station_id', postgresql.UUID(as_uuid=True), nullable=True), schema='core')
    
    # Add station_id to message_threads table
    op.add_column('message_threads', sa.Column('station_id', postgresql.UUID(as_uuid=True), nullable=True), schema='core')
    
    # Create foreign key constraints for station relationships
    op.create_foreign_key('fk_customers_station', 'customers', 'stations', ['station_id'], ['id'], 
                         source_schema='core', referent_schema='identity', ondelete='RESTRICT')
    op.create_foreign_key('fk_bookings_station', 'bookings', 'stations', ['station_id'], ['id'],
                         source_schema='core', referent_schema='identity', ondelete='RESTRICT')
    op.create_foreign_key('fk_message_threads_station', 'message_threads', 'stations', ['station_id'], ['id'],
                         source_schema='core', referent_schema='identity', ondelete='RESTRICT')
    
    # Create station-aware indexes for core tables
    op.create_index('idx_customer_station_email', 'customers', ['station_id', 'email_encrypted'], 
                   unique=True, schema='core')
    op.create_index('idx_customer_station_created', 'customers', ['station_id', 'created_at'], schema='core')
    op.create_index('idx_booking_station_date', 'bookings', ['station_id', 'date', 'slot'], schema='core')
    op.create_index('idx_booking_station_customer', 'bookings', ['station_id', 'customer_id'], schema='core')
    # NOTE: message_threads table doesn't exist in current migrations, will be added in future migration
    # op.create_index('idx_thread_station_phone', 'message_threads', ['station_id', 'phone_number'], schema='core')
    # op.create_index('idx_thread_station_customer', 'message_threads', ['station_id', 'customer_id'], schema='core')
    
    # Drop existing unique constraint on customers.email_encrypted (now unique per station)
    op.execute('ALTER TABLE core.customers DROP CONSTRAINT IF EXISTS customers_email_encrypted_key CASCADE')
    
    # Create default station for existing data
    op.execute("""
        INSERT INTO identity.stations (id, name, code, display_name, status, created_at, updated_at)
        VALUES (gen_random_uuid(), 'Default Station', 'DEFAULT', 'My Hibachi - Default Location', 'active', NOW(), NOW())
    """)
    
    # Update existing records to use default station
    op.execute("""
        UPDATE core.customers 
        SET station_id = (SELECT id FROM identity.stations WHERE code = 'DEFAULT' LIMIT 1)
        WHERE station_id IS NULL
    """)
    
    op.execute("""
        UPDATE core.bookings 
        SET station_id = (SELECT id FROM identity.stations WHERE code = 'DEFAULT' LIMIT 1)
        WHERE station_id IS NULL
    """)
    
    op.execute("""
        UPDATE core.message_threads 
        SET station_id = (SELECT id FROM identity.stations WHERE code = 'DEFAULT' LIMIT 1)
        WHERE station_id IS NULL
    """)
    
    # Make station_id NOT NULL after updating existing data
    op.alter_column('customers', 'station_id', nullable=False, schema='core')
    op.alter_column('bookings', 'station_id', nullable=False, schema='core')
    op.alter_column('message_threads', 'station_id', nullable=False, schema='core')
    
    # Enable Row Level Security (RLS) for multi-tenant isolation
    op.execute("ALTER TABLE core.customers ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE core.bookings ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE core.message_threads ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE identity.station_audit_logs ENABLE ROW LEVEL SECURITY")
    
    # Create RLS policies for multi-tenant data isolation
    
    # Customers RLS policy
    op.execute("""
        CREATE POLICY customers_station_isolation ON core.customers
        USING (
            station_id IN (
                SELECT su.station_id 
                FROM identity.station_users su 
                WHERE su.user_id = current_setting('app.current_user_id')::uuid 
                AND su.is_active = true
            )
            OR 
            -- Super admins and admins can see across stations
            EXISTS (
                SELECT 1 FROM identity.station_users su 
                WHERE su.user_id = current_setting('app.current_user_id')::uuid 
                AND su.role IN ('super_admin', 'admin')
                AND su.is_active = true
            )
        )
    """)
    
    # Bookings RLS policy
    op.execute("""
        CREATE POLICY bookings_station_isolation ON core.bookings
        USING (
            station_id IN (
                SELECT su.station_id 
                FROM identity.station_users su 
                WHERE su.user_id = current_setting('app.current_user_id')::uuid 
                AND su.is_active = true
            )
            OR 
            -- Super admins and admins can see across stations
            EXISTS (
                SELECT 1 FROM identity.station_users su 
                WHERE su.user_id = current_setting('app.current_user_id')::uuid 
                AND su.role IN ('super_admin', 'admin')
                AND su.is_active = true
            )
        )
    """)
    
    # Message threads RLS policy
    op.execute("""
        CREATE POLICY message_threads_station_isolation ON core.message_threads
        USING (
            station_id IN (
                SELECT su.station_id 
                FROM identity.station_users su 
                WHERE su.user_id = current_setting('app.current_user_id')::uuid 
                AND su.is_active = true
            )
            OR 
            -- Super admins and admins can see across stations
            EXISTS (
                SELECT 1 FROM identity.station_users su 
                WHERE su.user_id = current_setting('app.current_user_id')::uuid 
                AND su.role IN ('super_admin', 'admin')
                AND su.is_active = true
            )
        )
    """)
    
    # Station audit logs RLS policy
    op.execute("""
        CREATE POLICY station_audit_logs_isolation ON identity.station_audit_logs
        USING (
            station_id IN (
                SELECT su.station_id 
                FROM identity.station_users su 
                WHERE su.user_id = current_setting('app.current_user_id')::uuid 
                AND su.is_active = true
            )
            OR 
            -- Super admins can see all audit logs
            EXISTS (
                SELECT 1 FROM identity.station_users su 
                WHERE su.user_id = current_setting('app.current_user_id')::uuid 
                AND su.role = 'super_admin'
                AND su.is_active = true
            )
        )
    """)


def downgrade() -> None:
    """Remove multi-tenant station architecture."""
    
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS customers_station_isolation ON core.customers")
    op.execute("DROP POLICY IF EXISTS bookings_station_isolation ON core.bookings")
    op.execute("DROP POLICY IF EXISTS message_threads_station_isolation ON core.message_threads")
    op.execute("DROP POLICY IF EXISTS station_audit_logs_isolation ON identity.station_audit_logs")
    
    # Disable RLS
    op.execute("ALTER TABLE core.customers DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE core.bookings DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE core.message_threads DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE identity.station_audit_logs DISABLE ROW LEVEL SECURITY")
    
    # Drop station-aware indexes
    op.drop_index('idx_customer_station_email', 'customers', schema='core')
    op.drop_index('idx_customer_station_created', 'customers', schema='core')
    op.drop_index('idx_booking_station_date', 'bookings', schema='core')
    op.drop_index('idx_booking_station_customer', 'bookings', schema='core')
    op.drop_index('idx_thread_station_phone', 'message_threads', schema='core')
    op.drop_index('idx_thread_station_customer', 'message_threads', schema='core')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_customers_station', 'customers', schema='core', type_='foreignkey')
    op.drop_constraint('fk_bookings_station', 'bookings', schema='core', type_='foreignkey')
    op.drop_constraint('fk_message_threads_station', 'message_threads', schema='core', type_='foreignkey')
    
    # Remove station_id columns from core tables
    op.drop_column('customers', 'station_id', schema='core')
    op.drop_column('bookings', 'station_id', schema='core')
    op.drop_column('message_threads', 'station_id', schema='core')
    
    # Recreate original unique constraint on customers.email_encrypted
    op.create_unique_constraint('customers_email_encrypted_key', 'customers', ['email_encrypted'], schema='core')
    
    # Drop station tables (in reverse order of creation)
    op.drop_table('station_access_tokens', schema='identity')
    op.drop_table('station_audit_logs', schema='identity')
    op.drop_table('station_users', schema='identity')
    op.drop_table('stations', schema='identity')