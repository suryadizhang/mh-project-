"""Add social_accounts and social_identities tables

Revision ID: 011
Revises: 010
Create Date: 2025-11-21 (Nuclear Refactor - Social Models Completion)

Adds two critical tables for Social Media Admin Panel:
1. social_accounts - Connected business pages (Instagram, Facebook, etc.)
2. social_identities - Customer social media handles mapping

These tables enable:
- Social media account management
- Customer identity linking
- CQRS social command/query handlers
- Social admin panel features
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '016_add_social_account_identity'
down_revision = '0e81266c9503'  # create_booking_reminders_table (current HEAD)
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add social_accounts and social_identities tables."""
    
    # ========================================================================
    # 1. CREATE social_accounts TABLE
    # ========================================================================
    op.create_table(
        'social_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('platform', sa.String(50), nullable=False, comment='Social media platform (instagram, facebook, etc.)'),
        sa.Column('page_id', sa.String(255), nullable=False, comment='Platform-specific page/business ID'),
        sa.Column('page_name', sa.String(255), nullable=False, comment='Display name of the business page'),
        sa.Column('handle', sa.String(100), nullable=True, comment='@username or handle if applicable'),
        
        # Profile information
        sa.Column('profile_url', sa.Text, nullable=True),
        sa.Column('avatar_url', sa.Text, nullable=True),
        
        # Connection metadata
        sa.Column('connected_by', postgresql.UUID(as_uuid=True), nullable=False, comment='User ID who connected this account'),
        sa.Column('connected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Security & authentication
        sa.Column('token_ref', sa.Text, nullable=True, comment='Encrypted reference to access tokens (do not store plaintext tokens)'),
        sa.Column('webhook_verified', sa.Boolean, nullable=False, default=False, comment='Whether webhook subscription is verified'),
        
        # Sync tracking
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True, comment='Last successful sync with platform API'),
        
        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, default=True, comment='Whether account is currently active'),
        
        # Platform-specific configuration
        sa.Column('platform_metadata', postgresql.JSONB, nullable=True, comment='Platform-specific settings, capabilities, and metadata'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Soft delete timestamp'),
        
        schema='lead'
    )
    
    # Create indexes for social_accounts
    op.create_index(
        'ix_social_accounts_platform_page_id',
        'social_accounts',
        ['platform', 'page_id'],
        unique=True,
        schema='lead'
    )
    op.create_index(
        'ix_social_accounts_platform',
        'social_accounts',
        ['platform'],
        schema='lead'
    )
    op.create_index(
        'ix_social_accounts_is_active',
        'social_accounts',
        ['is_active'],
        schema='lead'
    )
    
    # ========================================================================
    # 2. CREATE social_identities TABLE
    # ========================================================================
    op.create_table(
        'social_identities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('handle', sa.String(100), nullable=False, comment='Social handle without @ prefix'),
        sa.Column('display_name', sa.String(255), nullable=True),
        
        # Profile information
        sa.Column('profile_url', sa.Text, nullable=True),
        sa.Column('avatar_url', sa.Text, nullable=True),
        
        # Customer mapping
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Link to known customer (soft reference)'),
        sa.Column('confidence_score', sa.Float, nullable=False, default=1.0, comment='Confidence in customer mapping (0.0 to 1.0)'),
        sa.Column('verification_status', sa.String(50), nullable=False, default='unverified', comment='Verification status: unverified, pending, verified, rejected'),
        
        # Activity tracking
        sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), comment='When this identity was first detected'),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True, comment='Last interaction timestamp'),
        
        # Platform-specific data
        sa.Column('platform_metadata', postgresql.JSONB, nullable=True, comment='Platform-specific profile data'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        
        schema='lead'
    )
    
    # Create indexes for social_identities
    op.create_index(
        'ix_social_identities_platform_handle',
        'social_identities',
        ['platform', 'handle'],
        unique=True,
        schema='lead'
    )
    op.create_index(
        'ix_social_identities_platform',
        'social_identities',
        ['platform'],
        schema='lead'
    )
    op.create_index(
        'ix_social_identities_customer_id',
        'social_identities',
        ['customer_id'],
        schema='lead'
    )
    
    # ========================================================================
    # 3. ADD FOREIGN KEYS TO EXISTING social_threads TABLE
    # ========================================================================
    
    # Add account_id foreign key (check if exists first)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    social_threads_cols = [col['name'] for col in inspector.get_columns('social_threads', schema='lead')]
    
    if 'account_id' not in social_threads_cols:
        op.add_column(
            'social_threads',
            sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Connected social account'),
            schema='lead'
        )
        op.create_foreign_key(
            'fk_social_threads_account_id',
            'social_threads', 'social_accounts',
            ['account_id'], ['id'],
            source_schema='lead', referent_schema='lead',
            ondelete='CASCADE'
        )
        op.create_index(
            'ix_social_threads_account_id',
            'social_threads',
            ['account_id'],
            schema='lead'
        )
    
    # Add social_identity_id foreign key
    if 'social_identity_id' not in social_threads_cols:
        op.add_column(
            'social_threads',
            sa.Column('social_identity_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Social identity of the person messaging us'),
            schema='lead'
        )
        op.create_foreign_key(
            'fk_social_threads_social_identity_id',
            'social_threads', 'social_identities',
            ['social_identity_id'], ['id'],
            source_schema='lead', referent_schema='lead',
            ondelete='SET NULL'
        )
        op.create_index(
            'ix_social_threads_social_identity_id',
            'social_threads',
            ['social_identity_id'],
            schema='lead'
        )
    
    # Add missing columns to social_threads for CQRS compatibility
    if 'assigned_to' not in social_threads_cols:
        op.add_column('social_threads', sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True, comment='Assigned team member'), schema='lead')
    if 'priority' not in social_threads_cols:
        op.add_column('social_threads', sa.Column('priority', sa.Integer, nullable=False, server_default='3', comment='1=urgent, 5=low'), schema='lead')
    if 'subject' not in social_threads_cols:
        op.add_column('social_threads', sa.Column('subject', sa.String(255), nullable=True, comment='Thread subject or first message preview'), schema='lead')
    if 'context_url' not in social_threads_cols:
        op.add_column('social_threads', sa.Column('context_url', sa.Text, nullable=True, comment='Link to original post/content'), schema='lead')
    if 'message_count' not in social_threads_cols:
        op.add_column('social_threads', sa.Column('message_count', sa.Integer, nullable=False, server_default='0'), schema='lead')
    if 'last_response_at' not in social_threads_cols:
        op.add_column('social_threads', sa.Column('last_response_at', sa.DateTime(timezone=True), nullable=True, comment='Last time we responded'), schema='lead')
    if 'resolved_at' not in social_threads_cols:
        op.add_column('social_threads', sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True), schema='lead')
    if 'tags' not in social_threads_cols:
        op.add_column('social_threads', sa.Column('tags', postgresql.ARRAY(sa.String(50)), nullable=True, comment='Categorization tags'), schema='lead')
    
    # Add indexes for new columns
    op.create_index('ix_social_threads_assigned_to', 'social_threads', ['assigned_to'], schema='lead')
    op.create_index('ix_social_threads_status', 'social_threads', ['status'], schema='lead')
    
    # ========================================================================
    # 4. UPDATE social_messages TABLE FOR CQRS COMPATIBILITY
    # ========================================================================
    # Check if table exists first
    if inspector.has_table('social_messages', schema='lead'):
        social_messages_cols = [col['name'] for col in inspector.get_columns('social_messages', schema='lead')]
        
        if 'message_ref' not in social_messages_cols:
            op.add_column('social_messages', sa.Column('message_ref', sa.String(255), nullable=True, comment='Alternative message reference'), schema='lead')
        if 'direction' not in social_messages_cols:
            op.add_column('social_messages', sa.Column('direction', sa.String(10), nullable=True, comment='IN (from customer) or OUT (from business)'), schema='lead')
        if 'kind' not in social_messages_cols:
            op.add_column('social_messages', sa.Column('kind', sa.String(20), nullable=True, comment='Type of message: DM, comment, review, etc.'), schema='lead')
        if 'author_handle' not in social_messages_cols:
            op.add_column('social_messages', sa.Column('author_handle', sa.String(100), nullable=True, comment='Alternative author field'), schema='lead')
        if 'author_name' not in social_messages_cols:
            op.add_column('social_messages', sa.Column('author_name', sa.String(255), nullable=True), schema='lead')
        if 'media' not in social_messages_cols:
            op.add_column('social_messages', sa.Column('media', postgresql.JSONB, nullable=True, comment='Attachments, images, videos'), schema='lead')
        if 'sentiment_score' not in social_messages_cols:
            op.add_column('social_messages', sa.Column('sentiment_score', sa.Float, nullable=True, comment='AI sentiment analysis -1 (negative) to 1 (positive)'), schema='lead')
        if 'intent_tags' not in social_messages_cols:
            op.add_column('social_messages', sa.Column('intent_tags', postgresql.ARRAY(sa.String(50)), nullable=True, comment='Detected intents'), schema='lead')
        if 'read_at' not in social_messages_cols:
            op.add_column('social_messages', sa.Column('read_at', sa.DateTime(timezone=True), nullable=True), schema='lead')
        if 'created_at' not in social_messages_cols:
            op.add_column('social_messages', sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')), schema='lead')
        
        # Add indexes (check if they exist first)
        try:
            op.create_index('ix_social_messages_thread_id', 'social_messages', ['thread_id'], schema='lead')
        except:
            pass
        try:
            op.create_index('ix_social_messages_sent_at', 'social_messages', ['sent_at'], schema='lead')
        except:
            pass
    
    # ========================================================================
    # 5. UPDATE reviews TABLE FOR SOCIAL ACCOUNT LINKING
    # ========================================================================
    # Check if table exists first
    if inspector.has_table('reviews', schema='public'):
        reviews_cols = [col['name'] for col in inspector.get_columns('reviews', schema='public')]
        
        if 'account_id' not in reviews_cols:
            op.add_column(
                'reviews',
                sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Social account where review was posted'),
                schema='public'
            )
            op.create_foreign_key(
                'fk_reviews_account_id',
                'reviews', 'social_accounts',
                ['account_id'], ['id'],
                source_schema='public', referent_schema='lead',
                ondelete='SET NULL'
            )
        if 'status' not in reviews_cols:
            op.add_column('reviews', sa.Column('status', sa.String(50), nullable=True, comment='Review status'), schema='public')
        if 'acknowledged_at' not in reviews_cols:
            op.add_column('reviews', sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True), schema='public')
        if 'responded_at' not in reviews_cols:
            op.add_column('reviews', sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True), schema='public')
        if 'platform_metadata' not in reviews_cols:
            op.add_column('reviews', sa.Column('platform_metadata', postgresql.JSONB, nullable=True, comment='Platform-specific review data'), schema='public')
        
        # Add indexes (check if they exist)
        try:
            op.create_index('ix_reviews_source', 'reviews', ['source'], schema='public')
        except:
            pass
        try:
            op.create_index('ix_reviews_rating', 'reviews', ['rating'], schema='public')
        except:
            pass
        try:
            op.create_index('ix_reviews_customer_id', 'reviews', ['customer_id'], schema='public')
        except:
            pass


def downgrade() -> None:
    """Remove social_accounts and social_identities tables."""
    
    # Drop indexes and columns from reviews
    op.drop_constraint('fk_reviews_account_id', 'reviews', schema='public', type_='foreignkey')
    op.drop_column('reviews', 'account_id', schema='public')
    op.drop_column('reviews', 'status', schema='public')
    op.drop_column('reviews', 'acknowledged_at', schema='public')
    op.drop_column('reviews', 'responded_at', schema='public')
    op.drop_column('reviews', 'platform_metadata', schema='public')
    op.drop_index('ix_reviews_source', 'reviews', schema='public')
    op.drop_index('ix_reviews_rating', 'reviews', schema='public')
    op.drop_index('ix_reviews_customer_id', 'reviews', schema='public')
    
    # Drop columns from social_messages
    op.drop_index('ix_social_messages_thread_id', 'social_messages', schema='lead')
    op.drop_index('ix_social_messages_sent_at', 'social_messages', schema='lead')
    op.drop_column('social_messages', 'message_ref', schema='lead')
    op.drop_column('social_messages', 'direction', schema='lead')
    op.drop_column('social_messages', 'kind', schema='lead')
    op.drop_column('social_messages', 'author_handle', schema='lead')
    op.drop_column('social_messages', 'author_name', schema='lead')
    op.drop_column('social_messages', 'media', schema='lead')
    op.drop_column('social_messages', 'sentiment_score', schema='lead')
    op.drop_column('social_messages', 'intent_tags', schema='lead')
    op.drop_column('social_messages', 'read_at', schema='lead')
    op.drop_column('social_messages', 'created_at', schema='lead')
    
    # Drop foreign keys and columns from social_threads
    op.drop_constraint('fk_social_threads_account_id', 'social_threads', schema='lead', type_='foreignkey')
    op.drop_constraint('fk_social_threads_social_identity_id', 'social_threads', schema='lead', type_='foreignkey')
    op.drop_index('ix_social_threads_account_id', 'social_threads', schema='lead')
    op.drop_index('ix_social_threads_social_identity_id', 'social_threads', schema='lead')
    op.drop_index('ix_social_threads_assigned_to', 'social_threads', schema='lead')
    op.drop_index('ix_social_threads_status', 'social_threads', schema='lead')
    op.drop_column('social_threads', 'account_id', schema='lead')
    op.drop_column('social_threads', 'social_identity_id', schema='lead')
    op.drop_column('social_threads', 'assigned_to', schema='lead')
    op.drop_column('social_threads', 'priority', schema='lead')
    op.drop_column('social_threads', 'subject', schema='lead')
    op.drop_column('social_threads', 'context_url', schema='lead')
    op.drop_column('social_threads', 'message_count', schema='lead')
    op.drop_column('social_threads', 'last_response_at', schema='lead')
    op.drop_column('social_threads', 'resolved_at', schema='lead')
    op.drop_column('social_threads', 'tags', schema='lead')
    
    # Drop social_identities table
    op.drop_index('ix_social_identities_platform_handle', 'social_identities', schema='lead')
    op.drop_index('ix_social_identities_platform', 'social_identities', schema='lead')
    op.drop_index('ix_social_identities_customer_id', 'social_identities', schema='lead')
    op.drop_table('social_identities', schema='lead')
    
    # Drop social_accounts table
    op.drop_index('ix_social_accounts_platform_page_id', 'social_accounts', schema='lead')
    op.drop_index('ix_social_accounts_platform', 'social_accounts', schema='lead')
    op.drop_index('ix_social_accounts_is_active', 'social_accounts', schema='lead')
    op.drop_table('social_accounts', schema='lead')
