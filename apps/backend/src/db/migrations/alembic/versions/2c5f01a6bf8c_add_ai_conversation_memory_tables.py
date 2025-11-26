"""add_ai_conversation_memory_tables

Revision ID: 2c5f01a6bf8c
Revises: 1f01e3015618
Create Date: 2025-11-25 01:54:34.612183

Creates AI conversation memory tables for PostgreSQL memory backend:
- ai_conversations: Conversation metadata with emotion tracking
- ai_messages: Individual messages with token tracking
- Indexes for performance optimization
- GIN indexes for JSONB fields

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '2c5f01a6bf8c'
down_revision = '1f01e3015618'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ai_conversations table
    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=True),
        sa.Column('channel', sa.String(20), nullable=False, server_default='web'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_message_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('context', JSONB, nullable=False, server_default='{}'),
        sa.Column('average_emotion_score', sa.Float(), nullable=True),
        sa.Column('emotion_trend', sa.String(20), nullable=True),
        sa.Column('escalated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('escalated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('closed_reason', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for ai_conversations
    op.create_index('idx_ai_conversations_user_active', 'ai_conversations', ['user_id', 'is_active'])
    op.create_index('idx_ai_conversations_channel', 'ai_conversations', ['channel'])
    op.create_index('idx_ai_conversations_escalated', 'ai_conversations', ['escalated', 'escalated_at'])
    op.create_index('idx_ai_conversations_last_message', 'ai_conversations', ['last_message_at'])
    op.create_index('idx_ai_conversations_context', 'ai_conversations', ['context'], postgresql_using='gin')
    op.create_index('ix_ai_conversations_user_id', 'ai_conversations', ['user_id'])
    op.create_index('ix_ai_conversations_is_active', 'ai_conversations', ['is_active'])

    # Create ai_messages table
    op.create_table(
        'ai_messages',
        sa.Column('id', sa.String(100), nullable=False),
        sa.Column('conversation_id', sa.String(100), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('message_metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('channel', sa.String(20), nullable=False, server_default='web'),
        sa.Column('emotion_score', sa.Float(), nullable=True),
        sa.Column('emotion_label', sa.String(20), nullable=True),
        sa.Column('detected_emotions', JSONB, nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('tool_calls', JSONB, nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['ai_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for ai_messages
    op.create_index('ix_ai_messages_conversation_id', 'ai_messages', ['conversation_id'])
    op.create_index('ix_ai_messages_timestamp', 'ai_messages', ['timestamp'])


def downgrade() -> None:
    # Drop ai_messages table (will cascade due to foreign key)
    op.drop_index('ix_ai_messages_timestamp', table_name='ai_messages')
    op.drop_index('ix_ai_messages_conversation_id', table_name='ai_messages')
    op.drop_table('ai_messages')

    # Drop ai_conversations table
    op.drop_index('ix_ai_conversations_is_active', table_name='ai_conversations')
    op.drop_index('ix_ai_conversations_user_id', table_name='ai_conversations')
    op.drop_index('idx_ai_conversations_context', table_name='ai_conversations')
    op.drop_index('idx_ai_conversations_last_message', table_name='ai_conversations')
    op.drop_index('idx_ai_conversations_escalated', table_name='ai_conversations')
    op.drop_index('idx_ai_conversations_channel', table_name='ai_conversations')
    op.drop_index('idx_ai_conversations_user_active', table_name='ai_conversations')
    op.drop_table('ai_conversations')
