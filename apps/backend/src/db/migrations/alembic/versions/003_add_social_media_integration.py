"""Add social media integration schemas

Revision ID: 003_add_social_media_integration
Revises: 002
Create Date: 2025-09-23 14:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_social_media_integration'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add social media integration tables to existing schemas."""



    # Core schema additions

    # Social accounts - connected business pages/profiles
    op.create_table(
        'social_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('platform', sa.Enum('instagram', 'facebook', 'google_business', 'yelp', 'tiktok', 'twitter', name='social_platform'), nullable=False),
        sa.Column('page_id', sa.String(255), nullable=False, comment='Platform-specific page/business ID'),
        sa.Column('page_name', sa.String(255), nullable=False, comment='Display name of the business page'),
        sa.Column('handle', sa.String(100), nullable=True, comment='@username or handle if applicable'),
        sa.Column('profile_url', sa.Text, nullable=True),
        sa.Column('avatar_url', sa.Text, nullable=True),
        sa.Column('connected_by', postgresql.UUID(as_uuid=True), nullable=False, comment='User who connected this account'),
        sa.Column('connected_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('token_ref', sa.Text, nullable=True, comment='Encrypted reference to access tokens'),
        sa.Column('webhook_verified', sa.Boolean, default=False, nullable=False),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=True, comment='Platform-specific settings and capabilities'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        schema='core'
    )

    # Create unique constraint for active accounts
    op.create_index(
        'ix_social_accounts_platform_page_active',
        'social_accounts',
        ['platform', 'page_id'],
        unique=True,
        postgresql_where=sa.text('deleted_at IS NULL AND is_active = TRUE'),
        schema='core'
    )

    # Social identities - map social handles to known customers
    op.create_table(
        'social_identities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('platform', sa.Enum('instagram', 'facebook', 'google_business', 'yelp', 'tiktok', 'twitter', name='social_platform'), nullable=False),
        sa.Column('handle', sa.String(100), nullable=False, comment='Social handle without @ prefix'),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('profile_url', sa.Text, nullable=True),
        sa.Column('avatar_url', sa.Text, nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Link to known customer'),
        sa.Column('confidence_score', sa.Float, default=1.0, nullable=False, comment='Confidence in customer mapping'),
        sa.Column('verification_status', sa.String(50), default='unverified', nullable=False),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        schema='core'
    )

    # Unique constraint for platform + handle
    op.create_index(
        'ix_social_identities_platform_handle',
        'social_identities',
        ['platform', 'handle'],
        unique=True,
        schema='core'
    )

    # Social threads - conversation containers
    op.create_table(
        'social_threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('platform', sa.Enum('instagram', 'facebook', 'google_business', 'yelp', 'tiktok', 'twitter', name='social_platform'), nullable=False),
        sa.Column('thread_ref', sa.String(255), nullable=False, comment='Platform-specific thread/conversation ID'),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Our social account'),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Linked customer if known'),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Generated lead if applicable'),
        sa.Column('social_identity_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Other party social identity'),
        sa.Column('status', sa.Enum('open', 'pending', 'resolved', 'snoozed', 'escalated', name='social_thread_status', create_type=False), default='open', nullable=False),
        sa.Column('priority', sa.Integer, default=3, nullable=False, comment='1=urgent, 5=low'),
        sa.Column('subject', sa.String(255), nullable=True, comment='Thread subject or first message preview'),
        sa.Column('context_url', sa.Text, nullable=True, comment='Link to original post/content'),
        sa.Column('message_count', sa.Integer, default=0, nullable=False),
        sa.Column('unread_count', sa.Integer, default=0, nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True, comment='Assigned team member'),
        sa.Column('tags', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['core.social_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['core.customers.id'], ondelete='SET NULL'),
        # Note: Foreign key for lead_id will be added when leads table is created
        sa.ForeignKeyConstraint(['social_identity_id'], ['core.social_identities.id'], ondelete='SET NULL'),
        schema='core'
    )

    # Unique constraint for thread_ref per account
    op.create_index(
        'ix_social_threads_account_thread_ref',
        'social_threads',
        ['account_id', 'thread_ref'],
        unique=True,
        schema='core'
    )

    # Social messages - individual messages within threads
    op.create_table(
        'social_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_ref', sa.String(255), nullable=True, comment='Platform-specific message ID'),
        sa.Column('direction', sa.Enum('in', 'out', name='social_message_direction', create_type=False), nullable=False),
        sa.Column('kind', sa.Enum('dm', 'comment', 'review', 'reply', 'mention', 'story_reply', name='social_message_kind', create_type=False), nullable=False),
        sa.Column('author_handle', sa.String(100), nullable=True),
        sa.Column('author_name', sa.String(255), nullable=True),
        sa.Column('body', sa.Text, nullable=True),
        sa.Column('media', postgresql.JSONB, nullable=True, comment='Attachments, images, videos'),
        sa.Column('sentiment_score', sa.Float, nullable=True, comment='AI sentiment analysis -1 to 1'),
        sa.Column('intent_tags', postgresql.ARRAY(sa.String(50)), nullable=True, comment='Detected intents: booking, complaint, etc'),
        sa.Column('is_public', sa.Boolean, default=False, nullable=False, comment='Public comment vs private DM'),
        sa.Column('requires_approval', sa.Boolean, default=False, nullable=False, comment='AI response needs human approval'),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True, comment='Who approved the response'),
        sa.Column('ai_generated', sa.Boolean, default=False, nullable=False),
        sa.Column('parent_message_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Reply to this message'),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True, comment='When actually posted to platform'),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_details', sa.Text, nullable=True),
        sa.ForeignKeyConstraint(['thread_id'], ['core.social_threads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_message_id'], ['core.social_messages.id'], ondelete='CASCADE'),
        schema='core'
    )

    # Reviews - separate table for review-specific data
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('platform', sa.Enum('instagram', 'facebook', 'google_business', 'yelp', 'tiktok', 'twitter', name='social_platform'), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('review_ref', sa.String(255), nullable=False, comment='Platform-specific review ID'),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Associated thread if replies exist'),
        sa.Column('author_handle', sa.String(100), nullable=True),
        sa.Column('author_name', sa.String(255), nullable=True),
        sa.Column('rating', sa.Integer, nullable=True, comment='1-5 star rating where applicable'),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('body', sa.Text, nullable=True),
        sa.Column('review_url', sa.Text, nullable=True),
        sa.Column('status', sa.Enum('new', 'acknowledged', 'responded', 'escalated', 'closed', name='review_status', create_type=False), default='new', nullable=False),
        sa.Column('sentiment_score', sa.Float, nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('booking_ref', sa.String(50), nullable=True, comment='Reference to related booking if found'),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('escalation_reason', sa.String(255), nullable=True),
        sa.Column('response_due_at', sa.DateTime(timezone=True), nullable=True, comment='SLA deadline'),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['core.social_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['thread_id'], ['core.social_threads.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['customer_id'], ['core.customers.id'], ondelete='SET NULL'),
        schema='core'
    )

    # Unique constraint for review_ref per account
    op.create_index(
        'ix_reviews_account_review_ref',
        'reviews',
        ['account_id', 'review_ref'],
        unique=True,
        schema='core'
    )

    # Integration schema - webhook idempotency
    op.create_table(
        'social_inbox',
        sa.Column('signature', sa.String(255), primary_key=True, comment='Webhook signature for idempotency'),
        sa.Column('platform', sa.Enum('instagram', 'facebook', 'google_business', 'yelp', 'tiktok', 'twitter', name='social_platform'), nullable=False),
        sa.Column('webhook_type', sa.String(100), nullable=False, comment='Type of webhook event'),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payload_hash', sa.String(64), nullable=False, comment='SHA256 of payload for deduplication'),
        sa.Column('processed', sa.Boolean, default=False, nullable=False),
        sa.Column('processing_attempts', sa.Integer, default=0, nullable=False),
        sa.Column('last_error', sa.Text, nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        schema='integra'
    )

    # Read schema - materialized views for admin interface
    op.execute("""
        CREATE MATERIALIZED VIEW read.social_inbox_threads AS
        SELECT
            st.id as thread_id,
            st.platform,
            st.status,
            st.priority,
            st.subject,
            st.context_url,
            st.message_count,
            st.unread_count,
            st.last_message_at,
            st.last_response_at,
            st.assigned_to,
            st.tags,
            sa.page_name as account_name,
            sa.handle as account_handle,
            si.handle as other_party_handle,
            si.display_name as other_party_name,
            si.avatar_url as other_party_avatar,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            c.phone_encrypted as customer_phone,
            c.email_encrypted as customer_email,
            NULL as lead_status,
            NULL as interest_level,
            -- Latest message preview
            (
                SELECT sm.body
                FROM core.social_messages sm
                WHERE sm.thread_id = st.id
                ORDER BY sm.created_at DESC
                LIMIT 1
            ) as latest_message,
            -- Response time metrics
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - st.last_message_at))/3600 as hours_since_last_message,
            st.created_at,
            st.updated_at
        FROM core.social_threads st
        JOIN core.social_accounts sa ON st.account_id = sa.id
        LEFT JOIN core.social_identities si ON st.social_identity_id = si.id
        LEFT JOIN core.customers c ON st.customer_id = c.id
        -- Note: LEFT JOIN core.leads l ON st.lead_id = l.id (to be added when leads table exists)
        WHERE st.status IN ('open', 'pending', 'escalated')
        ORDER BY
            st.priority ASC,
            st.last_message_at DESC
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW read.reviews_board AS
        SELECT
            r.id as review_id,
            r.platform,
            r.status,
            r.rating,
            r.title,
            r.body,
            r.review_url,
            r.author_handle,
            r.author_name,
            r.sentiment_score,
            r.keywords,
            r.assigned_to,
            r.escalation_reason,
            r.response_due_at,
            r.responded_at,
            sa.page_name as account_name,
            sa.handle as account_handle,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            r.booking_ref,
            -- Time metrics
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - r.created_at))/3600 as age_hours,
            CASE
                WHEN r.response_due_at IS NOT NULL AND r.responded_at IS NULL
                THEN EXTRACT(EPOCH FROM (r.response_due_at - CURRENT_TIMESTAMP))/3600
                ELSE NULL
            END as hours_until_due,
            -- Urgency score based on rating and age
            CASE
                WHEN r.rating <= 2 THEN 1
                WHEN r.rating = 3 THEN 2
                ELSE 3
            END + CASE
                WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - r.created_at))/3600 > 24 THEN -1
                ELSE 0
            END as urgency_score,
            r.created_at,
            r.updated_at
        FROM core.reviews r
        JOIN core.social_accounts sa ON r.account_id = sa.id
        LEFT JOIN core.customers c ON r.customer_id = c.id
        WHERE r.status IN ('new', 'acknowledged', 'escalated')
        ORDER BY
            urgency_score ASC,
            r.created_at ASC
    """)

    # Create indexes for performance
    op.create_index('ix_social_accounts_platform', 'social_accounts', ['platform'], schema='core')
    op.create_index('ix_social_accounts_created_at', 'social_accounts', ['created_at'], schema='core')

    op.create_index('ix_social_identities_customer_id', 'social_identities', ['customer_id'], schema='core')
    op.create_index('ix_social_identities_last_active', 'social_identities', ['last_active_at'], schema='core')

    op.create_index('ix_social_threads_status', 'social_threads', ['status'], schema='core')
    op.create_index('ix_social_threads_customer_id', 'social_threads', ['customer_id'], schema='core')
    op.create_index('ix_social_threads_lead_id', 'social_threads', ['lead_id'], schema='core')
    op.create_index('ix_social_threads_last_message_at', 'social_threads', ['last_message_at'], schema='core')
    op.create_index('ix_social_threads_assigned_to', 'social_threads', ['assigned_to'], schema='core')

    op.create_index('ix_social_messages_thread_id', 'social_messages', ['thread_id'], schema='core')
    op.create_index('ix_social_messages_created_at', 'social_messages', ['created_at'], schema='core')
    op.create_index('ix_social_messages_direction_kind', 'social_messages', ['direction', 'kind'], schema='core')
    op.create_index('ix_social_messages_requires_approval', 'social_messages', ['requires_approval'], postgresql_where=sa.text('requires_approval = TRUE'), schema='core')

    op.create_index('ix_reviews_platform_status', 'reviews', ['platform', 'status'], schema='core')
    op.create_index('ix_reviews_rating', 'reviews', ['rating'], schema='core')
    op.create_index('ix_reviews_created_at', 'reviews', ['created_at'], schema='core')
    op.create_index('ix_reviews_customer_id', 'reviews', ['customer_id'], schema='core')
    op.create_index('ix_reviews_assigned_to', 'reviews', ['assigned_to'], schema='core')
    op.create_index('ix_reviews_response_due_at', 'reviews', ['response_due_at'], postgresql_where=sa.text('response_due_at IS NOT NULL AND responded_at IS NULL'), schema='core')

    op.create_index('ix_social_inbox_platform_received', 'social_inbox', ['platform', 'received_at'], schema='integra')
    op.create_index('ix_social_inbox_processed', 'social_inbox', ['processed'], schema='integra')

    # Create unique indexes on materialized views
    op.create_index('ix_social_inbox_threads_thread_id', 'social_inbox_threads', ['thread_id'], unique=True, schema='read')
    op.create_index('ix_reviews_board_review_id', 'reviews_board', ['review_id'], unique=True, schema='read')

    # Add check constraints
    op.execute("ALTER TABLE core.social_messages ADD CONSTRAINT ck_social_messages_sentiment_range CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0)")
    op.execute("ALTER TABLE core.reviews ADD CONSTRAINT ck_reviews_rating_range CHECK (rating >= 1 AND rating <= 5)")
    op.execute("ALTER TABLE core.social_threads ADD CONSTRAINT ck_social_threads_priority_range CHECK (priority >= 1 AND priority <= 5)")
    op.execute("ALTER TABLE core.reviews ADD CONSTRAINT ck_reviews_sentiment_range CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0)")


def downgrade() -> None:
    """Remove social media integration tables."""

    # Drop materialized views
    op.execute("DROP MATERIALIZED VIEW IF EXISTS read.reviews_board")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS read.social_inbox_threads")

    # Drop tables in correct order (respecting foreign keys)
    op.drop_table('social_inbox', schema='integra')
    op.drop_table('reviews', schema='core')
    op.drop_table('social_messages', schema='core')
    op.drop_table('social_threads', schema='core')
    op.drop_table('social_identities', schema='core')
    op.drop_table('social_accounts', schema='core')

    # Drop custom types
    op.execute("DROP TYPE IF EXISTS review_status")
    op.execute("DROP TYPE IF EXISTS social_thread_status")
    op.execute("DROP TYPE IF EXISTS social_message_kind")
    op.execute("DROP TYPE IF EXISTS social_message_direction")
    op.execute("DROP TYPE IF EXISTS social_platform")
