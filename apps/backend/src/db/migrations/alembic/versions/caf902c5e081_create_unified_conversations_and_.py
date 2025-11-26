"""create_unified_conversations_and_messages

Creates unified conversation and message tables in ai schema.

This migration merges two separate conversation systems into one:
1. AIConversation/AIMessage (from memory backend) - emotion tracking
2. Conversation/Message (from endpoints) - multi-channel support

MERGED INTO:
- ai.conversations (UnifiedConversation) - ALL features combined
- ai.messages (UnifiedMessage) - ALL features combined

Key Features:
- Multi-channel support (web, SMS, voice, Facebook, Instagram, WhatsApp, email)
- Emotion tracking and trending
- Human escalation workflow
- Shadow learning (teacher-student AI routing)
- Tool usage tracking (function calling)
- Knowledge base integration
- Training data collection
- RLHF human feedback

Data Migration:
- Migrates existing data from public.ai_conversations → ai.conversations
- Migrates existing data from public.ai_messages → ai.messages
- Preserves all relationships and metadata
- Renames old tables to *_legacy for safety

Revision ID: caf902c5e081
Revises: 6fd48d0caced
Create Date: 2025-11-25 13:24:49.449994

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'caf902c5e081'
down_revision = '6fd48d0caced'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create unified conversations and messages tables.
    Migrate data from existing tables.
    """

    # ===================================================================
    # 1. CREATE ai.conversations TABLE (UnifiedConversation)
    # ===================================================================

    op.create_table(
        'conversations',

        # === Primary Key ===
        sa.Column('id', sa.String(100), primary_key=True),

        # === Channel Information ===
        sa.Column('channel', sa.String(20), nullable=False, server_default='web'),
        sa.Column('channel_metadata', postgresql.JSONB, nullable=False, server_default='{}'),

        # === User/Customer Information ===
        sa.Column('user_id', sa.String(255), nullable=True),
        sa.Column('customer_id', sa.String(100), nullable=True),
        sa.Column('thread_id', sa.String(255), nullable=False),

        # === Conversation Lifecycle ===
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('started_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('last_message_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('closed_at', sa.DateTime, nullable=True),
        sa.Column('closed_reason', sa.String(100), nullable=True),

        # === Message Counts ===
        sa.Column('message_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('user_message_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('ai_message_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('human_message_count', sa.Integer, nullable=False, server_default='0'),

        # === Emotion Tracking (from AIConversation) ===
        sa.Column('average_emotion_score', sa.Float, nullable=True),
        sa.Column('emotion_trend', sa.String(20), nullable=True),
        sa.Column('latest_detected_emotions', postgresql.JSONB, nullable=True),

        # === Escalation Management ===
        sa.Column('escalated', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('escalated_at', sa.DateTime, nullable=True),
        sa.Column('assigned_agent_id', sa.String(255), nullable=True),
        sa.Column('escalation_reason', sa.Text, nullable=True),

        # === Shadow Learning (from Conversation) ===
        sa.Column('confidence_score', sa.Float, nullable=True, server_default='1.0'),
        sa.Column('route_decision', sa.String(50), nullable=True, server_default='teacher'),
        sa.Column('student_response', sa.Text, nullable=True),
        sa.Column('teacher_response', sa.Text, nullable=True),
        sa.Column('reward_score', sa.Float, nullable=True),

        # === Context Storage (JSONB for flexibility) ===
        sa.Column('context', postgresql.JSONB, nullable=False, server_default='{}'),

        # === Foreign Keys ===
        sa.ForeignKeyConstraint(['customer_id'], ['public.customers.id'], name='fk_conversations_customer'),

        schema='ai'
    )

    # Create indexes for conversations table (15 total)
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'], schema='ai')
    op.create_index('ix_conversations_customer_id', 'conversations', ['customer_id'], schema='ai')
    op.create_index('ix_conversations_thread_id', 'conversations', ['thread_id'], schema='ai')
    op.create_index('ix_conversations_status', 'conversations', ['status'], schema='ai')
    op.create_index('ix_conversations_channel', 'conversations', ['channel'], schema='ai')
    op.create_index('ix_conversations_escalated', 'conversations', ['escalated'], schema='ai')
    op.create_index('ix_conversations_last_message_at', 'conversations', ['last_message_at'], schema='ai')

    # Composite indexes for common queries
    op.create_index('idx_conversations_user_active', 'conversations', ['user_id', 'status'], schema='ai')
    op.create_index('idx_conversations_user_channel', 'conversations', ['user_id', 'channel'], schema='ai')
    op.create_index('idx_conversations_channel_active', 'conversations', ['channel', 'status'], schema='ai')
    op.create_index('idx_conversations_escalated_at', 'conversations', ['escalated', 'escalated_at'], schema='ai')

    # GIN indexes for JSONB fields (fast JSON queries)
    op.create_index('idx_conversations_context', 'conversations', ['context'],
                    schema='ai', postgresql_using='gin')
    op.create_index('idx_conversations_channel_metadata', 'conversations', ['channel_metadata'],
                    schema='ai', postgresql_using='gin')
    op.create_index('idx_conversations_detected_emotions', 'conversations', ['latest_detected_emotions'],
                    schema='ai', postgresql_using='gin')

    # ===================================================================
    # 2. CREATE ai.messages TABLE (UnifiedMessage)
    # ===================================================================

    op.create_table(
        'messages',

        # === Primary Key ===
        sa.Column('id', sa.String(100), primary_key=True),

        # === Foreign Keys ===
        sa.Column('conversation_id', sa.String(100), nullable=False),

        # === Message Content ===
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),

        # === Channel Information ===
        sa.Column('channel', sa.String(20), nullable=False, server_default='web'),

        # === Message Metadata (JSONB) ===
        sa.Column('message_metadata', postgresql.JSONB, nullable=False, server_default='{}'),

        # === Emotion Tracking (from AIMessage) ===
        sa.Column('emotion_score', sa.Float, nullable=True),
        sa.Column('emotion_label', sa.String(20), nullable=True),
        sa.Column('detected_emotions', postgresql.JSONB, nullable=True),

        # === Token Tracking ===
        sa.Column('input_tokens', sa.Integer, nullable=True),
        sa.Column('output_tokens', sa.Integer, nullable=True),
        sa.Column('cost_usd', sa.Float, nullable=True),

        # === AI Model Information ===
        sa.Column('model_used', sa.String(50), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('processing_time_ms', sa.Integer, nullable=True),

        # === Tool Usage (from AIMessage) ===
        sa.Column('tool_calls', postgresql.JSONB, nullable=True),
        sa.Column('tool_results', postgresql.JSONB, nullable=True),

        # === Knowledge Base (from Message) ===
        sa.Column('kb_sources_used', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('intent_classification', sa.String(50), nullable=True),

        # === Training Data (from Message) ===
        sa.Column('is_training_data', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('human_feedback', sa.String(20), nullable=True),
        sa.Column('human_correction', sa.Text, nullable=True),

        # === Message Lifecycle ===
        sa.Column('edited_at', sa.DateTime, nullable=True),

        # === Foreign Keys ===
        sa.ForeignKeyConstraint(
            ['conversation_id'],
            ['ai.conversations.id'],
            name='fk_messages_conversation',
            ondelete='CASCADE'
        ),

        schema='ai'
    )

    # Create indexes for messages table (12 total)
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'], schema='ai')
    op.create_index('ix_messages_timestamp', 'messages', ['timestamp'], schema='ai')
    op.create_index('ix_messages_role', 'messages', ['role'], schema='ai')
    op.create_index('ix_messages_channel', 'messages', ['channel'], schema='ai')
    op.create_index('ix_messages_is_training_data', 'messages', ['is_training_data'], schema='ai')

    # Composite indexes for common queries
    op.create_index('idx_messages_conversation_timestamp', 'messages',
                    ['conversation_id', 'timestamp'], schema='ai')
    op.create_index('idx_messages_conversation_role', 'messages',
                    ['conversation_id', 'role'], schema='ai')
    op.create_index('idx_messages_training_data_timestamp', 'messages',
                    ['is_training_data', 'timestamp'], schema='ai')

    # GIN indexes for JSONB fields
    op.create_index('idx_messages_metadata', 'messages', ['message_metadata'],
                    schema='ai', postgresql_using='gin')
    op.create_index('idx_messages_detected_emotions', 'messages', ['detected_emotions'],
                    schema='ai', postgresql_using='gin')
    op.create_index('idx_messages_tool_calls', 'messages', ['tool_calls'],
                    schema='ai', postgresql_using='gin')
    op.create_index('idx_messages_kb_sources', 'messages', ['kb_sources_used'],
                    schema='ai', postgresql_using='gin')

    # ===================================================================
    # 3. MIGRATE DATA FROM EXISTING TABLES (IF THEY EXIST)
    # ===================================================================

    # Check if old tables exist before migrating
    connection = op.get_bind()

    # Migrate ai_conversations → ai.conversations
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'ai_conversations'
        )
    """))

    if result.scalar():
        print("✅ Migrating data from public.ai_conversations to ai.conversations...")
        op.execute("""
            INSERT INTO ai.conversations (
                id, user_id, channel, started_at, last_message_at,
                message_count, context, average_emotion_score, emotion_trend,
                escalated, escalated_at, status,
                closed_at, closed_reason, thread_id
            )
            SELECT
                id,
                user_id,
                COALESCE(channel, 'web') as channel,
                started_at,
                last_message_at,
                message_count,
                COALESCE(context, '{}'::jsonb) as context,
                average_emotion_score,
                emotion_trend,
                escalated,
                escalated_at,
                CASE
                    WHEN is_active = true THEN 'active'
                    WHEN escalated = true THEN 'escalated'
                    ELSE 'closed'
                END as status,
                closed_at,
                closed_reason,
                COALESCE(id, 'thread_' || id) as thread_id
            FROM public.ai_conversations
            ON CONFLICT (id) DO NOTHING
        """)

        # Rename old table for safety
        op.rename_table('ai_conversations', 'ai_conversations_legacy', schema='public')
        print("✅ Renamed public.ai_conversations → public.ai_conversations_legacy")

    # Migrate ai_messages → ai.messages
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'ai_messages'
        )
    """))

    if result.scalar():
        print("✅ Migrating data from public.ai_messages to ai.messages...")
        op.execute("""
            INSERT INTO ai.messages (
                id, conversation_id, role, content, timestamp,
                message_metadata, channel, emotion_score, emotion_label,
                detected_emotions, input_tokens, output_tokens, tool_calls
            )
            SELECT
                id,
                conversation_id,
                role,
                content,
                timestamp,
                COALESCE(message_metadata, '{}'::jsonb) as message_metadata,
                COALESCE(channel, 'web') as channel,
                emotion_score,
                emotion_label,
                detected_emotions,
                input_tokens,
                output_tokens,
                tool_calls
            FROM public.ai_messages
            WHERE conversation_id IN (SELECT id FROM ai.conversations)
            ON CONFLICT (id) DO NOTHING
        """)

        # Rename old table for safety
        op.rename_table('ai_messages', 'ai_messages_legacy', schema='public')
        print("✅ Renamed public.ai_messages → public.ai_messages_legacy")


def downgrade() -> None:
    """
    Rollback unified conversations and messages.

    WARNING: This will restore old tables and delete new unified tables!
    Use with caution in production.
    """

    # Restore old tables if they exist as *_legacy
    connection = op.get_bind()

    # Restore ai_conversations_legacy → ai_conversations
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'ai_conversations_legacy'
        )
    """))

    if result.scalar():
        op.rename_table('ai_conversations_legacy', 'ai_conversations', schema='public')
        print("✅ Restored public.ai_conversations_legacy → public.ai_conversations")

    # Restore ai_messages_legacy → ai_messages
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'ai_messages_legacy'
        )
    """))

    if result.scalar():
        op.rename_table('ai_messages_legacy', 'ai_messages', schema='public')
        print("✅ Restored public.ai_messages_legacy → public.ai_messages")

    # Drop new tables
    op.drop_table('messages', schema='ai')
    op.drop_table('conversations', schema='ai')

    print("✅ Dropped ai.conversations and ai.messages")
