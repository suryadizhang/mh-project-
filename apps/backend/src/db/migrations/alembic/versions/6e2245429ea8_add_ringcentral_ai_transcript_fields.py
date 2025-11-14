"""add_ringcentral_ai_transcript_fields

Revision ID: 6e2245429ea8
Revises: 9c41683cf436
Create Date: 2025-11-12 10:10:06.368015

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '6e2245429ea8'
down_revision = '9c41683cf436'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add RingCentral AI transcript and insights fields to call_recordings table"""
    
    # Check if table exists (it's in communications schema)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check if call_recordings table exists in communications schema
    tables = inspector.get_table_names(schema='communications')
    
    if 'call_recordings' not in tables:
        # Table doesn't exist yet, skip this migration
        # It will be created by migration 010_escalation_call_recording.py
        # Re-run 'alembic upgrade head' after that migration completes
        print("⚠️  call_recordings table not found in communications schema")
        print("    This migration will be applied after 010_escalation_call_recording.py runs")
        print("    Run 'alembic upgrade head' again to complete this migration")
        return
    
    # Check if columns already exist (idempotent migration)
    columns = [col['name'] for col in inspector.get_columns('call_recordings', schema='communications')]
    
    if 'rc_transcript' in columns:
        print("✅ RingCentral AI transcript fields already exist, skipping")
        return
    
    print("📝 Adding RingCentral AI transcript fields to call_recordings table...")
    
    # Add transcript fields
    op.add_column(
        'call_recordings',
        sa.Column('rc_transcript', sa.Text(), nullable=True),
        schema='communications'
    )
    op.add_column(
        'call_recordings',
        sa.Column('rc_transcript_confidence', sa.Integer(), nullable=True),
        schema='communications'
    )
    op.add_column(
        'call_recordings',
        sa.Column('rc_transcript_fetched_at', sa.DateTime(timezone=True), nullable=True),
        schema='communications'
    )
    op.add_column(
        'call_recordings',
        sa.Column('rc_ai_insights', JSONB, nullable=False, server_default='{}'),
        schema='communications'
    )
    
    # Ensure pg_trgm extension exists for full-text search
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    
    # Create index for transcript search (requires pg_trgm extension)
    try:
        op.create_index(
            'idx_call_recordings_transcript_search',
            'call_recordings',
            ['rc_transcript'],
            schema='communications',
            postgresql_using='gin',
            postgresql_ops={'rc_transcript': 'gin_trgm_ops'}
        )
    except Exception as e:
        print(f"⚠️  Could not create GIN index (pg_trgm may not be available): {e}")
        print("    Full-text search will still work but may be slower")
    
    # Create index for fetched_at for monitoring
    op.create_index(
        'idx_call_recordings_transcript_fetched',
        'call_recordings',
        ['rc_transcript_fetched_at'],
        schema='communications'
    )
    
    print("✅ RingCentral AI transcript fields added successfully")


def downgrade() -> None:
    """Remove RingCentral AI transcript fields"""
    
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names(schema='communications')
    
    if 'call_recordings' not in tables:
        return
    
    # Drop indexes
    op.drop_index(
        'idx_call_recordings_transcript_fetched', 
        table_name='call_recordings', 
        schema='communications',
        if_exists=True
    )
    op.drop_index(
        'idx_call_recordings_transcript_search', 
        table_name='call_recordings', 
        schema='communications',
        if_exists=True
    )
    
    # Drop columns
    op.drop_column('call_recordings', 'rc_ai_insights', schema='communications')
    op.drop_column('call_recordings', 'rc_transcript_fetched_at', schema='communications')
    op.drop_column('call_recordings', 'rc_transcript_confidence', schema='communications')
    op.drop_column('call_recordings', 'rc_transcript', schema='communications')
