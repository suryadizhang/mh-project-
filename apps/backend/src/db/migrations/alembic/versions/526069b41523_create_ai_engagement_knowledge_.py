"""create_ai_engagement_knowledge_analytics_shadow_tables

Creates remaining AI tables in ai schema:
1. customer_engagement_followups - Scheduled follow-up automation
2. kb_chunks - Knowledge base (RAG) with vector embeddings
3. escalation_rules - Auto-escalation rules
4. conversation_analytics - Quality metrics and resolution tracking
5. ai_usage - Token usage and cost tracking
6. training_data - Self-learning AI dataset
7. ai_tutor_pairs - Shadow learning (teacher-student comparison)
8. ai_rlhf_scores - Human feedback scores
9. ai_export_jobs - Training data export jobs

This completes the unified AI models package migration.

Revision ID: 526069b41523
Revises: caf902c5e081
Create Date: 2025-11-25 13:25:52.649834

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '526069b41523'
down_revision = 'caf902c5e081'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create all remaining AI tables in ai schema.
    """

    # ===================================================================
    # 1. CREATE customer_engagement_followups TABLE
    # ===================================================================

    op.create_table(
        'customer_engagement_followups',

        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('conversation_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('customer_id', sa.String(100), nullable=True),

        # Trigger information
        sa.Column('trigger_type', sa.String(50), nullable=False),
        sa.Column('trigger_data', postgresql.JSONB, nullable=False, server_default='{}'),

        # Scheduling
        sa.Column('scheduled_at', sa.DateTime, nullable=False),
        sa.Column('execution_started_at', sa.DateTime, nullable=True),
        sa.Column('executed_at', sa.DateTime, nullable=True),
        sa.Column('cancelled_at', sa.DateTime, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),

        # Message content
        sa.Column('template_id', sa.String(50), nullable=True),
        sa.Column('message_content', sa.Text, nullable=True),

        # Error handling
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_retry_at', sa.DateTime, nullable=True),
        sa.Column('execution_duration_ms', sa.Integer, nullable=True),

        # Metadata
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('created_by_admin_id', sa.String(255), nullable=True),

        sa.ForeignKeyConstraint(['customer_id'], ['public.customers.id']),

        schema='ai'
    )

    # Indexes for scheduler optimization
    op.create_index('idx_followups_status_scheduled', 'customer_engagement_followups',
                    ['status', 'scheduled_at'], schema='ai')
    op.create_index('idx_followups_user_status', 'customer_engagement_followups',
                    ['user_id', 'status'], schema='ai')
    op.create_index('idx_followups_trigger_type', 'customer_engagement_followups',
                    ['trigger_type', 'status'], schema='ai')
    op.create_index('idx_followups_duplicate_check', 'customer_engagement_followups',
                    ['user_id', 'trigger_type', 'status', 'scheduled_at'], schema='ai')
    op.create_index('idx_followups_customer_pending', 'customer_engagement_followups',
                    ['customer_id', 'status'], schema='ai')

    # ===================================================================
    # 2. CREATE kb_chunks TABLE (Knowledge Base with pgvector)
    # ===================================================================

    # Note: Requires pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'kb_chunks',

        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float), nullable=True),  # Will be vector type
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_reference', sa.String(255), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('tags', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('quality_score', sa.Float, nullable=True),
        sa.Column('usage_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('success_rate', sa.Float, nullable=True),

        schema='ai'
    )

    # Indexes
    op.create_index('ix_kb_chunks_source_type', 'kb_chunks', ['source_type'], schema='ai')
    op.create_index('ix_kb_chunks_is_active', 'kb_chunks', ['is_active'], schema='ai')
    op.create_index('idx_kb_chunks_metadata', 'kb_chunks', ['metadata'],
                    schema='ai', postgresql_using='gin')

    # ===================================================================
    # 3. CREATE escalation_rules TABLE
    # ===================================================================

    op.create_table(
        'escalation_rules',

        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('rule_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('confidence_threshold', sa.Float, nullable=True),
        sa.Column('emotion_threshold', sa.Float, nullable=True),
        sa.Column('priority', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),

        schema='ai'
    )

    op.create_index('idx_escalation_rules_active_priority', 'escalation_rules',
                    ['is_active', 'priority'], schema='ai')

    # ===================================================================
    # 4. CREATE conversation_analytics TABLE
    # ===================================================================

    op.create_table(
        'conversation_analytics',

        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('conversation_id', sa.String(100), nullable=False, unique=True),
        sa.Column('resolution_status', sa.String(50), nullable=True),
        sa.Column('resolution_time_seconds', sa.Integer, nullable=True),
        sa.Column('customer_satisfaction', sa.Integer, nullable=True),
        sa.Column('first_response_time_seconds', sa.Integer, nullable=True),
        sa.Column('avg_response_time_seconds', sa.Integer, nullable=True),
        sa.Column('total_messages', sa.Integer, nullable=False, server_default='0'),
        sa.Column('user_messages', sa.Integer, nullable=False, server_default='0'),
        sa.Column('ai_messages', sa.Integer, nullable=False, server_default='0'),
        sa.Column('human_messages', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_cost_usd', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('escalated_to_human', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),

        sa.ForeignKeyConstraint(['conversation_id'], ['ai.conversations.id'], ondelete='CASCADE'),

        schema='ai'
    )

    op.create_index('ix_analytics_conversation_id', 'conversation_analytics',
                    ['conversation_id'], schema='ai')
    op.create_index('idx_analytics_resolution_status', 'conversation_analytics',
                    ['resolution_status'], schema='ai')
    op.create_index('idx_analytics_customer_satisfaction', 'conversation_analytics',
                    ['customer_satisfaction'], schema='ai')

    # ===================================================================
    # 5. CREATE ai_usage TABLE
    # ===================================================================

    op.create_table(
        'ai_usage',

        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('conversation_id', sa.String(100), nullable=False),
        sa.Column('model_name', sa.String(50), nullable=False),
        sa.Column('input_tokens', sa.Integer, nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer, nullable=False, server_default='0'),
        sa.Column('cost_usd', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('request_metadata', postgresql.JSONB, nullable=False, server_default='{}'),

        sa.ForeignKeyConstraint(['conversation_id'], ['ai.conversations.id'], ondelete='CASCADE'),

        schema='ai'
    )

    op.create_index('ix_usage_conversation_id', 'ai_usage', ['conversation_id'], schema='ai')
    op.create_index('ix_usage_model_name', 'ai_usage', ['model_name'], schema='ai')
    op.create_index('ix_usage_timestamp', 'ai_usage', ['timestamp'], schema='ai')
    op.create_index('idx_usage_model_timestamp', 'ai_usage',
                    ['model_name', 'timestamp'], schema='ai')

    # ===================================================================
    # 6. CREATE training_data TABLE
    # ===================================================================

    op.create_table(
        'training_data',

        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('conversation_id', sa.String(100), nullable=False),
        sa.Column('message_id', sa.String(100), nullable=True),
        sa.Column('prompt', sa.Text, nullable=False),
        sa.Column('completion', sa.Text, nullable=False),
        sa.Column('quality_score', sa.Float, nullable=True),
        sa.Column('human_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('human_correction', sa.Text, nullable=True),
        sa.Column('training_metadata', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('exported_at', sa.DateTime, nullable=True),

        sa.ForeignKeyConstraint(['conversation_id'], ['ai.conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['ai.messages.id'], ondelete='SET NULL'),

        schema='ai'
    )

    op.create_index('ix_training_data_conversation_id', 'training_data',
                    ['conversation_id'], schema='ai')
    op.create_index('idx_training_data_verified', 'training_data',
                    ['human_verified', 'exported_at'], schema='ai')
    op.create_index('idx_training_data_quality', 'training_data',
                    ['quality_score'], schema='ai')

    # ===================================================================
    # 7. CREATE ai_tutor_pairs TABLE (Shadow Learning)
    # ===================================================================

    op.create_table(
        'ai_tutor_pairs',

        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('conversation_id', sa.String(100), nullable=False),
        sa.Column('prompt', sa.Text, nullable=False),
        sa.Column('teacher_response', sa.Text, nullable=False),
        sa.Column('student_response', sa.Text, nullable=False),
        sa.Column('teacher_model', sa.String(50), nullable=False),
        sa.Column('student_model', sa.String(50), nullable=False),
        sa.Column('similarity_score', sa.Float, nullable=True),
        sa.Column('chosen_response', sa.String(20), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),

        sa.ForeignKeyConstraint(['conversation_id'], ['ai.conversations.id'], ondelete='CASCADE'),

        schema='ai'
    )

    op.create_index('ix_tutor_pairs_conversation_id', 'ai_tutor_pairs',
                    ['conversation_id'], schema='ai')
    op.create_index('idx_tutor_pairs_similarity', 'ai_tutor_pairs',
                    ['similarity_score'], schema='ai')
    op.create_index('idx_tutor_pairs_chosen', 'ai_tutor_pairs',
                    ['chosen_response', 'similarity_score'], schema='ai')

    # ===================================================================
    # 8. CREATE ai_rlhf_scores TABLE (Human Feedback)
    # ===================================================================

    op.create_table(
        'ai_rlhf_scores',

        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('tutor_pair_id', sa.String(255), nullable=False),
        sa.Column('message_id', sa.String(100), nullable=True),
        sa.Column('accuracy_score', sa.Integer, nullable=True),
        sa.Column('helpfulness_score', sa.Integer, nullable=True),
        sa.Column('tone_score', sa.Integer, nullable=True),
        sa.Column('completeness_score', sa.Integer, nullable=True),
        sa.Column('overall_score', sa.Float, nullable=True),
        sa.Column('feedback_notes', sa.Text, nullable=True),
        sa.Column('is_production_ready', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('reviewer_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),

        sa.ForeignKeyConstraint(['tutor_pair_id'], ['ai.ai_tutor_pairs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['ai.messages.id'], ondelete='SET NULL'),

        schema='ai'
    )

    op.create_index('ix_rlhf_scores_tutor_pair_id', 'ai_rlhf_scores',
                    ['tutor_pair_id'], schema='ai')
    op.create_index('idx_rlhf_production_ready', 'ai_rlhf_scores',
                    ['is_production_ready', 'overall_score'], schema='ai')

    # ===================================================================
    # 9. CREATE ai_export_jobs TABLE
    # ===================================================================

    op.create_table(
        'ai_export_jobs',

        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('job_name', sa.String(100), nullable=False),
        sa.Column('export_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('failed_at', sa.DateTime, nullable=True),
        sa.Column('records_exported', sa.Integer, nullable=False, server_default='0'),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('filters', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('created_by_admin_id', sa.String(255), nullable=True),

        schema='ai'
    )

    op.create_index('ix_export_jobs_status', 'ai_export_jobs', ['status'], schema='ai')
    op.create_index('idx_export_jobs_type_status', 'ai_export_jobs',
                    ['export_type', 'status'], schema='ai')


def downgrade() -> None:
    """
    Drop all AI tables created in this migration.
    """

    op.drop_table('ai_export_jobs', schema='ai')
    op.drop_table('ai_rlhf_scores', schema='ai')
    op.drop_table('ai_tutor_pairs', schema='ai')
    op.drop_table('training_data', schema='ai')
    op.drop_table('ai_usage', schema='ai')
    op.drop_table('conversation_analytics', schema='ai')
    op.drop_table('escalation_rules', schema='ai')
    op.drop_table('kb_chunks', schema='ai')
    op.drop_table('customer_engagement_followups', schema='ai')
