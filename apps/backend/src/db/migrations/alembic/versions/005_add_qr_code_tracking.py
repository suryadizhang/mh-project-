"""add qr code tracking

Revision ID: 005_add_qr_code_tracking
Revises: 004_add_customer_review_system
Create Date: 2025-10-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_add_qr_code_tracking'
down_revision: Union[str, None] = '004_add_customer_review_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add QR code tracking system for business cards and marketing materials.
    Tracks scans, locations, devices, and conversion metrics.
    """
    
    # Create marketing schema for tracking
    op.execute("CREATE SCHEMA IF NOT EXISTS marketing")
    
    # Enum will be created automatically by SQLAlchemy when table is created
    
    # Create qr_codes table - defines QR codes
    op.create_table(
        'qr_codes',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False, unique=True, comment='Unique QR code identifier (e.g., BC001, FLYER023)'),
        sa.Column('type', postgresql.ENUM('business_card', 'flyer', 'menu', 'vehicle', 'banner', 'other', name='qr_code_type', schema='marketing'), nullable=False),
        sa.Column('destination_url', sa.String(500), nullable=False, comment='Where the QR code redirects to'),
        sa.Column('description', sa.Text(), nullable=True, comment='Description of where this QR code is used'),
        sa.Column('campaign_name', sa.String(100), nullable=True, comment='Marketing campaign name'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, comment='Additional metadata (print date, quantity, etc.)'),
        sa.PrimaryKeyConstraint('id'),
        # Foreign key to users table - commented out if users table doesn't exist yet
        # sa.ForeignKeyConstraint(['created_by'], ['core.users.id'], ondelete='SET NULL'),
        schema='marketing',
        comment='Defines QR codes for tracking scans'
    )
    
    # Create qr_scans table - tracks each scan
    op.create_table(
        'qr_scans',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('qr_code_id', sa.UUID(), nullable=False),
        sa.Column('scanned_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True, comment='IPv4 or IPv6 address'),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True, comment='mobile, tablet, desktop'),
        sa.Column('os', sa.String(50), nullable=True, comment='iOS, Android, Windows, etc.'),
        sa.Column('browser', sa.String(50), nullable=True),
        sa.Column('city', sa.String(100), nullable=True, comment='Derived from IP geolocation'),
        sa.Column('region', sa.String(100), nullable=True, comment='State/Province'),
        sa.Column('country', sa.String(2), nullable=True, comment='ISO country code'),
        sa.Column('latitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('longitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('referrer', sa.String(500), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True, comment='Track user journey'),
        sa.Column('converted_to_lead', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('converted_to_booking', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('conversion_value', sa.Numeric(10, 2), nullable=True, comment='Booking value if converted'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, comment='Additional tracking data'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['qr_code_id'], ['marketing.qr_codes.id'], ondelete='CASCADE'),
        schema='marketing',
        comment='Tracks each QR code scan with device and location data'
    )
    
    # Create indexes for performance
    op.create_index('idx_qr_codes_code', 'qr_codes', ['code'], unique=True, schema='marketing')
    op.create_index('idx_qr_codes_type', 'qr_codes', ['type'], schema='marketing')
    op.create_index('idx_qr_codes_is_active', 'qr_codes', ['is_active'], schema='marketing')
    
    op.create_index('idx_qr_scans_qr_code_id', 'qr_scans', ['qr_code_id'], schema='marketing')
    op.create_index('idx_qr_scans_scanned_at', 'qr_scans', ['scanned_at'], schema='marketing')
    op.create_index('idx_qr_scans_session_id', 'qr_scans', ['session_id'], schema='marketing')
    op.create_index('idx_qr_scans_converted', 'qr_scans', ['converted_to_lead', 'converted_to_booking'], schema='marketing')
    op.create_index('idx_qr_scans_location', 'qr_scans', ['city', 'region', 'country'], schema='marketing')
    
    # Create analytics view
    op.execute("""
        CREATE OR REPLACE VIEW marketing.qr_analytics AS
        SELECT
            qc.id AS qr_code_id,
            qc.code,
            qc.type,
            qc.campaign_name,
            qc.destination_url,
            COUNT(qs.id) AS total_scans,
            COUNT(DISTINCT qs.ip_address) AS unique_scans,
            COUNT(DISTINCT qs.session_id) AS unique_sessions,
            SUM(CASE WHEN qs.converted_to_lead THEN 1 ELSE 0 END) AS leads_generated,
            SUM(CASE WHEN qs.converted_to_booking THEN 1 ELSE 0 END) AS bookings_generated,
            SUM(qs.conversion_value) AS total_revenue,
            ROUND(
                (SUM(CASE WHEN qs.converted_to_booking THEN 1 ELSE 0 END)::numeric / 
                NULLIF(COUNT(DISTINCT qs.session_id), 0) * 100), 2
            ) AS conversion_rate,
            COUNT(CASE WHEN qs.device_type = 'mobile' THEN 1 END) AS mobile_scans,
            COUNT(CASE WHEN qs.device_type = 'tablet' THEN 1 END) AS tablet_scans,
            COUNT(CASE WHEN qs.device_type = 'desktop' THEN 1 END) AS desktop_scans,
            MAX(qs.scanned_at) AS last_scan_at,
            DATE_TRUNC('day', MIN(qs.scanned_at)) AS first_scan_at
        FROM marketing.qr_codes qc
        LEFT JOIN marketing.qr_scans qs ON qc.id = qs.qr_code_id
        WHERE qc.is_active = true
        GROUP BY qc.id, qc.code, qc.type, qc.campaign_name, qc.destination_url
    """)
    
    # Insert default business card QR code
    op.execute("""
        INSERT INTO marketing.qr_codes (code, type, destination_url, description, campaign_name, metadata)
        VALUES (
            'BC001',
            'business_card',
            '/contact',
            'Primary business card QR code - directs to contact page',
            'Business Cards 2025',
            '{"batch": "initial", "quantity": 500, "print_date": "2025-10-25"}'::jsonb
        )
    """)


def downgrade() -> None:
    """Drop QR code tracking system"""
    
    # Drop view
    op.execute("DROP VIEW IF EXISTS marketing.qr_analytics")
    
    # Drop indexes
    op.drop_index('idx_qr_scans_location', table_name='qr_scans', schema='marketing')
    op.drop_index('idx_qr_scans_converted', table_name='qr_scans', schema='marketing')
    op.drop_index('idx_qr_scans_session_id', table_name='qr_scans', schema='marketing')
    op.drop_index('idx_qr_scans_scanned_at', table_name='qr_scans', schema='marketing')
    op.drop_index('idx_qr_scans_qr_code_id', table_name='qr_scans', schema='marketing')
    
    op.drop_index('idx_qr_codes_is_active', table_name='qr_codes', schema='marketing')
    op.drop_index('idx_qr_codes_type', table_name='qr_codes', schema='marketing')
    op.drop_index('idx_qr_codes_code', table_name='qr_codes', schema='marketing')
    
    # Drop tables
    op.drop_table('qr_scans', schema='marketing')
    op.drop_table('qr_codes', schema='marketing')
    
    # Drop enum
    op.execute("DROP TYPE IF EXISTS marketing.qr_code_type")
    
    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS marketing CASCADE")
