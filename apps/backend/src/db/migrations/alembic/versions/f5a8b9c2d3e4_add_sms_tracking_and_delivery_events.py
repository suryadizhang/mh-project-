"""Add SMS tracking fields and SMS delivery event table

Revision ID: f5a8b9c2d3e4
Revises: f069ddb440f7
Create Date: 2025-11-14 10:00:00.000000

CRITICAL - US Compliance Requirements:
======================================
This migration adds SMS tracking for TCPA compliance:
1. SMS tracking fields on Subscriber model (total_sms_sent, delivery rates)
2. SMS delivery event tracking for audit trail
3. Cost tracking for budget compliance
4. Segment tracking for accurate pricing

Business Model Alignment:
========================
- SMS is PRIMARY newsletter channel (RingCentral)
- Email is for admin/transactional only
- Proper separation of email vs SMS metrics
- TCPA-compliant delivery tracking

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f5a8b9c2d3e4'
down_revision = 'f069ddb440f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add SMS tracking fields to subscribers table and create SMS delivery events table.
    """
    
    # Create SMS delivery status enum
    sa.Enum(
        'queued',
        'sending',
        'sent',
        'delivered',
        'failed',
        'undelivered',
        name='sms_delivery_status',
        schema='newsletter'
    ).create(op.get_bind(), checkfirst=True)
    
    # Add SMS tracking fields to subscribers table
    op.add_column(
        'subscribers',
        sa.Column('total_sms_sent', sa.Integer(), nullable=False, server_default='0'),
        schema='newsletter'
    )
    op.add_column(
        'subscribers',
        sa.Column('total_sms_delivered', sa.Integer(), nullable=False, server_default='0'),
        schema='newsletter'
    )
    op.add_column(
        'subscribers',
        sa.Column('total_sms_failed', sa.Integer(), nullable=False, server_default='0'),
        schema='newsletter'
    )
    op.add_column(
        'subscribers',
        sa.Column('last_sms_sent_date', sa.DateTime(timezone=True), nullable=True),
        schema='newsletter'
    )
    op.add_column(
        'subscribers',
        sa.Column('last_sms_delivered_date', sa.DateTime(timezone=True), nullable=True),
        schema='newsletter'
    )
    
    # Add denormalized performance metrics to campaigns table
    op.add_column(
        'campaigns',
        sa.Column('total_sent', sa.Integer(), nullable=False, server_default='0'),
        schema='newsletter'
    )
    op.add_column(
        'campaigns',
        sa.Column('total_delivered', sa.Integer(), nullable=False, server_default='0'),
        schema='newsletter'
    )
    op.add_column(
        'campaigns',
        sa.Column('total_opened', sa.Integer(), nullable=False, server_default='0'),
        schema='newsletter'
    )
    op.add_column(
        'campaigns',
        sa.Column('total_clicked', sa.Integer(), nullable=False, server_default='0'),
        schema='newsletter'
    )
    op.add_column(
        'campaigns',
        sa.Column('total_unsubscribed', sa.Integer(), nullable=False, server_default='0'),
        schema='newsletter'
    )
    op.add_column(
        'campaigns',
        sa.Column('total_failed', sa.Integer(), nullable=False, server_default='0'),
        schema='newsletter'
    )
    op.add_column(
        'campaigns',
        sa.Column('delivery_rate_cached', sa.Numeric(5, 2), nullable=True),
        schema='newsletter'
    )
    op.add_column(
        'campaigns',
        sa.Column('open_rate_cached', sa.Numeric(5, 2), nullable=True),
        schema='newsletter'
    )
    op.add_column(
        'campaigns',
        sa.Column('click_rate_cached', sa.Numeric(5, 2), nullable=True),
        schema='newsletter'
    )
    op.add_column(
        'campaigns',
        sa.Column('unsubscribe_rate_cached', sa.Numeric(5, 2), nullable=True),
        schema='newsletter'
    )
    op.add_column(
        'campaigns',
        sa.Column('last_metrics_updated', sa.DateTime(timezone=True), nullable=True),
        schema='newsletter'
    )
    
    # Create SMS delivery events table
    op.create_table(
        'sms_delivery_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'campaign_event_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('newsletter.campaign_events.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column('ringcentral_message_id', sa.String(255), nullable=False),
        sa.Column(
            'status',
            sa.Enum(
                'queued',
                'sending',
                'sent',
                'delivered',
                'failed',
                'undelivered',
                name='sms_delivery_status'
            ),
            nullable=False,
            server_default='queued'
        ),
        sa.Column('delivery_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('carrier_error_code', sa.String(50), nullable=True),
        sa.Column('segments_used', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('cost_cents', sa.Integer(), nullable=True),
        sa.Column('ringcentral_metadata', postgresql.JSONB(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('NOW()')
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('NOW()')
        ),
        schema='newsletter'
    )
    
    # Create indexes for SMS delivery events
    op.create_index(
        'ix_sms_delivery_ringcentral_msg_id',
        'sms_delivery_events',
        ['ringcentral_message_id'],
        unique=True,
        schema='newsletter'
    )
    op.create_index(
        'ix_sms_delivery_campaign_event',
        'sms_delivery_events',
        ['campaign_event_id'],
        schema='newsletter'
    )
    op.create_index(
        'ix_sms_delivery_status',
        'sms_delivery_events',
        ['status'],
        schema='newsletter'
    )
    op.create_index(
        'ix_sms_delivery_timestamp',
        'sms_delivery_events',
        ['delivery_timestamp'],
        schema='newsletter'
    )
    
    # Create indexes for new subscriber SMS fields (for analytics queries)
    op.create_index(
        'ix_subscribers_last_sms_sent_date',
        'subscribers',
        ['last_sms_sent_date'],
        schema='newsletter'
    )
    op.create_index(
        'ix_subscribers_sms_consent',
        'subscribers',
        ['sms_consent', 'subscribed'],
        schema='newsletter'
    )
    
    # Create indexes for campaign metrics (for dashboard queries)
    op.create_index(
        'ix_campaigns_last_metrics_updated',
        'campaigns',
        ['last_metrics_updated'],
        schema='newsletter'
    )


def downgrade() -> None:
    """
    Remove SMS tracking fields and SMS delivery events table.
    """
    
    # Drop indexes first
    op.drop_index('ix_campaigns_last_metrics_updated', table_name='campaigns', schema='newsletter')
    op.drop_index('ix_subscribers_sms_consent', table_name='subscribers', schema='newsletter')
    op.drop_index('ix_subscribers_last_sms_sent_date', table_name='subscribers', schema='newsletter')
    op.drop_index('ix_sms_delivery_timestamp', table_name='sms_delivery_events', schema='newsletter')
    op.drop_index('ix_sms_delivery_status', table_name='sms_delivery_events', schema='newsletter')
    op.drop_index('ix_sms_delivery_campaign_event', table_name='sms_delivery_events', schema='newsletter')
    op.drop_index('ix_sms_delivery_ringcentral_msg_id', table_name='sms_delivery_events', schema='newsletter')
    
    # Drop SMS delivery events table
    op.drop_table('sms_delivery_events', schema='newsletter')
    
    # Drop enum
    sa.Enum(name='sms_delivery_status', schema='newsletter').drop(op.get_bind(), checkfirst=True)
    
    # Remove campaign cached metrics columns
    op.drop_column('campaigns', 'last_metrics_updated', schema='newsletter')
    op.drop_column('campaigns', 'unsubscribe_rate_cached', schema='newsletter')
    op.drop_column('campaigns', 'click_rate_cached', schema='newsletter')
    op.drop_column('campaigns', 'open_rate_cached', schema='newsletter')
    op.drop_column('campaigns', 'delivery_rate_cached', schema='newsletter')
    op.drop_column('campaigns', 'total_failed', schema='newsletter')
    op.drop_column('campaigns', 'total_unsubscribed', schema='newsletter')
    op.drop_column('campaigns', 'total_clicked', schema='newsletter')
    op.drop_column('campaigns', 'total_opened', schema='newsletter')
    op.drop_column('campaigns', 'total_delivered', schema='newsletter')
    op.drop_column('campaigns', 'total_sent', schema='newsletter')
    
    # Remove subscriber SMS tracking columns
    op.drop_column('subscribers', 'last_sms_delivered_date', schema='newsletter')
    op.drop_column('subscribers', 'last_sms_sent_date', schema='newsletter')
    op.drop_column('subscribers', 'total_sms_failed', schema='newsletter')
    op.drop_column('subscribers', 'total_sms_delivered', schema='newsletter')
    op.drop_column('subscribers', 'total_sms_sent', schema='newsletter')
