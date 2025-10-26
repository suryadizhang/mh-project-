"""Add Lead and Newsletter schemas for enterprise CRM

Revision ID: 003_add_lead_newsletter_schemas
Revises: 002
Create Date: 2025-10-06 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_lead_newsletter_schemas'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add Lead and Newsletter schemas to complement existing CRM structure."""

    # Create additional schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS lead")
    op.execute("CREATE SCHEMA IF NOT EXISTS newsletter")

    # Lead schema tables
    op.create_table(
        'leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source', sa.Enum('web_quote', 'chat', 'instagram', 'facebook', 'google', 'yelp', 'sms', 'phone', 'referral', 'event', name='lead_source'), nullable=False),
        sa.Column('status', sa.Enum('new', 'working', 'qualified', 'disqualified', 'converted', 'nurturing', name='lead_status'), nullable=False, default='new'),
        sa.Column('quality', sa.Enum('hot', 'warm', 'cold', name='lead_quality'), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('score', sa.Numeric(5,2), nullable=False, default=0),
        sa.Column('assigned_to', sa.String(100), nullable=True),
        sa.Column('last_contact_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('follow_up_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('conversion_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('lost_reason', sa.Text(), nullable=True),
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['core.customers.id'], ondelete='SET NULL'),
        sa.CheckConstraint('score >= 0 AND score <= 100', name='check_lead_score_range'),
        schema='lead'
    )

    op.create_table(
        'lead_contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel', sa.Enum('email', 'sms', 'instagram', 'facebook', 'google', 'yelp', 'web', name='contact_channel'), nullable=False),
        sa.Column('handle_or_address', sa.Text(), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['lead_id'], ['lead.leads.id'], ondelete='CASCADE'),
        schema='lead'
    )

    op.create_table(
        'lead_context',
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('party_size_adults', sa.Integer(), nullable=True),
        sa.Column('party_size_kids', sa.Integer(), nullable=True),
        sa.Column('estimated_budget_cents', sa.Integer(), nullable=True),
        sa.Column('event_date_pref', sa.Date(), nullable=True),
        sa.Column('event_date_range_start', sa.Date(), nullable=True),
        sa.Column('event_date_range_end', sa.Date(), nullable=True),
        sa.Column('zip_code', sa.String(10), nullable=True),
        sa.Column('service_type', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['lead_id'], ['lead.leads.id'], ondelete='CASCADE'),
        schema='lead'
    )

    op.create_table(
        'lead_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=True),
        sa.Column('occurred_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['lead_id'], ['lead.leads.id'], ondelete='CASCADE'),
        schema='lead'
    )

    op.create_table(
        'social_threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('platform', sa.Enum('instagram', 'facebook', 'google', 'yelp', name='social_platform'), nullable=False),
        sa.Column('account_id', sa.String(100), nullable=False),
        sa.Column('thread_ref', sa.String(255), nullable=False),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('open', 'pending', 'resolved', name='thread_status'), nullable=False, default='open'),
        sa.Column('last_message_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['lead_id'], ['lead.leads.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['customer_id'], ['core.customers.id'], ondelete='SET NULL'),
        schema='lead'
    )

    # Newsletter schema tables
    op.create_table(
        'subscribers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email_enc', sa.LargeBinary(), nullable=False),
        sa.Column('phone_enc', sa.LargeBinary(), nullable=True),
        sa.Column('subscribed', sa.Boolean(), nullable=False, default=True),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('sms_consent', sa.Boolean(), nullable=False, default=False),
        sa.Column('email_consent', sa.Boolean(), nullable=False, default=True),
        sa.Column('consent_updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('consent_ip_address', sa.String(45), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('engagement_score', sa.Integer(), nullable=False, default=0),
        sa.Column('total_emails_sent', sa.Integer(), nullable=False, default=0),
        sa.Column('total_emails_opened', sa.Integer(), nullable=False, default=0),
        sa.Column('total_clicks', sa.Integer(), nullable=False, default=0),
        sa.Column('last_email_sent_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('last_opened_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('unsubscribed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['core.customers.id'], ondelete='SET NULL'),
        sa.CheckConstraint('engagement_score >= 0 AND engagement_score <= 100', name='check_engagement_score_range'),
        schema='newsletter'
    )

    op.create_table(
        'campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('channel', sa.Enum('email', 'sms', 'both', name='campaign_channel'), nullable=False),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('content', postgresql.JSONB(), nullable=False),
        sa.Column('segment_filter', postgresql.JSONB(), nullable=True),
        sa.Column('scheduled_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('sent_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('draft', 'scheduled', 'sending', 'sent', 'cancelled', name='campaign_status'), nullable=False, default='draft'),
        sa.Column('total_recipients', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', sa.String(100), nullable=False),
        schema='newsletter'
    )

    op.create_table(
        'campaign_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscriber_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.Enum('sent', 'delivered', 'opened', 'clicked', 'replied', 'bounced', 'unsubscribed', 'complained', name='campaign_event_type'), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=True),
        sa.Column('occurred_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['campaign_id'], ['newsletter.campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subscriber_id'], ['newsletter.subscribers.id'], ondelete='CASCADE'),
        schema='newsletter'
    )

    # Create indexes for performance
    op.create_index('ix_lead_leads_status', 'leads', ['status'], schema='lead')
    op.create_index('ix_lead_leads_source', 'leads', ['source'], schema='lead')
    op.create_index('ix_lead_leads_score', 'leads', ['score'], schema='lead')
    op.create_index('ix_lead_leads_followup', 'leads', ['follow_up_date'], schema='lead')
    op.create_index('ix_lead_leads_customer', 'leads', ['customer_id'], schema='lead')

    op.create_index('ix_lead_contacts_lead', 'lead_contacts', ['lead_id'], schema='lead')
    op.create_index('ix_lead_contacts_channel', 'lead_contacts', ['channel', 'handle_or_address'], schema='lead')

    op.create_index('ix_lead_events_lead', 'lead_events', ['lead_id', 'occurred_at'], schema='lead')

    op.create_index('ix_social_threads_platform', 'social_threads', ['platform', 'thread_ref'], unique=True, schema='lead')
    op.create_index('ix_social_threads_lead', 'social_threads', ['lead_id'], schema='lead')
    op.create_index('ix_social_threads_customer', 'social_threads', ['customer_id'], schema='lead')

    op.create_index('ix_newsletter_subscribers_subscribed', 'subscribers', ['subscribed'], schema='newsletter')
    op.create_index('ix_newsletter_subscribers_customer', 'subscribers', ['customer_id'], schema='newsletter')
    op.create_index('ix_newsletter_subscribers_engagement', 'subscribers', ['engagement_score'], schema='newsletter')

    op.create_index('ix_newsletter_campaigns_status', 'campaigns', ['status'], schema='newsletter')
    op.create_index('ix_newsletter_campaigns_sent', 'campaigns', ['sent_at'], schema='newsletter')

    op.create_index('ix_newsletter_events_campaign', 'campaign_events', ['campaign_id', 'type'], schema='newsletter')
    op.create_index('ix_newsletter_events_subscriber', 'campaign_events', ['subscriber_id', 'occurred_at'], schema='newsletter')


def downgrade() -> None:
    """Drop Lead and Newsletter schemas."""

    # Drop tables in reverse dependency order
    op.drop_table('campaign_events', schema='newsletter')
    op.drop_table('campaigns', schema='newsletter')
    op.drop_table('subscribers', schema='newsletter')

    op.drop_table('social_threads', schema='lead')
    op.drop_table('lead_events', schema='lead')
    op.drop_table('lead_context', schema='lead')
    op.drop_table('lead_contacts', schema='lead')
    op.drop_table('leads', schema='lead')

    # Drop custom types
    op.execute("DROP TYPE IF EXISTS campaign_event_type")
    op.execute("DROP TYPE IF EXISTS campaign_status")
    op.execute("DROP TYPE IF EXISTS campaign_channel")
    op.execute("DROP TYPE IF EXISTS social_platform")
    op.execute("DROP TYPE IF EXISTS thread_status")
    op.execute("DROP TYPE IF EXISTS contact_channel")
    op.execute("DROP TYPE IF EXISTS lead_quality")
    op.execute("DROP TYPE IF EXISTS lead_status")
    op.execute("DROP TYPE IF EXISTS lead_source")

    # Drop schemas
    op.execute("DROP SCHEMA IF EXISTS newsletter CASCADE")
    op.execute("DROP SCHEMA IF EXISTS lead CASCADE")