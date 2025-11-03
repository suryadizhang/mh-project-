"""
Alembic migration: Add Shadow Learning tables

Revision ID: add_shadow_learning_tables
Creates: ai_tutor_pairs, ai_rlhf_scores, ai_export_jobs
Purpose: Enable Shadow Learning for local LLM training with OpenAI as teacher
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "add_shadow_learning_tables"
down_revision = "create_notification_groups"  # Update to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Create Shadow Learning tables"""

    # Create export status enum
    export_status_enum = postgresql.ENUM(
        "pending", "in_progress", "completed", "failed", name="exportstatus", create_type=True
    )
    export_status_enum.create(op.get_bind(), checkfirst=True)

    # 1. Create ai_tutor_pairs table
    op.create_table(
        "ai_tutor_pairs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        # Request context
        sa.Column("prompt", sa.Text(), nullable=False, comment="User's original prompt"),
        sa.Column("context", sa.Text(), nullable=True, comment="Conversation context/history"),
        sa.Column("agent_type", sa.String(50), nullable=True, comment="Which AI agent type"),
        # Teacher response (OpenAI)
        sa.Column(
            "teacher_model",
            sa.String(50),
            nullable=False,
            comment="Teacher model name (e.g., gpt-4)",
        ),
        sa.Column("teacher_response", sa.Text(), nullable=False, comment="Teacher's response"),
        sa.Column("teacher_tokens", sa.Integer(), nullable=True),
        sa.Column("teacher_cost_usd", sa.Float(), nullable=True),
        sa.Column("teacher_response_time_ms", sa.Integer(), nullable=True),
        # Student response (Local Llama-3)
        sa.Column(
            "student_model",
            sa.String(50),
            nullable=False,
            comment="Student model name (e.g., llama3)",
        ),
        sa.Column("student_response", sa.Text(), nullable=False, comment="Student's response"),
        sa.Column("student_tokens", sa.Integer(), nullable=True),
        sa.Column("student_response_time_ms", sa.Integer(), nullable=True),
        # Similarity metrics
        sa.Column(
            "similarity_score",
            sa.Float(),
            nullable=True,
            comment="Cosine similarity between embeddings (0-1)",
        ),
        sa.Column(
            "quality_score", sa.Float(), nullable=True, comment="Overall quality assessment (0-1)"
        ),
        # Customer impact tracking
        sa.Column(
            "used_in_production",
            sa.Boolean(),
            default=False,
            comment="Did we use student response in production?",
        ),
        sa.Column(
            "customer_feedback",
            sa.String(20),
            nullable=True,
            comment="Customer feedback: positive/negative/neutral",
        ),
        # Metadata
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    # Create indexes for ai_tutor_pairs
    op.create_index("ix_ai_tutor_pairs_id", "ai_tutor_pairs", ["id"])
    op.create_index("idx_tutor_created", "ai_tutor_pairs", ["created_at"])
    op.create_index("idx_tutor_similarity", "ai_tutor_pairs", ["similarity_score"])
    op.create_index("idx_tutor_agent", "ai_tutor_pairs", ["agent_type", "created_at"])
    op.create_index("idx_tutor_production", "ai_tutor_pairs", ["used_in_production", "created_at"])

    # 2. Create ai_rlhf_scores table
    op.create_table(
        "ai_rlhf_scores",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        # Reference to tutor pair
        sa.Column("tutor_pair_id", sa.Integer(), nullable=False),
        # Human feedback
        sa.Column("reviewer_id", sa.Integer(), nullable=True, comment="Admin user who reviewed"),
        # Scoring dimensions (1-5 scale)
        sa.Column(
            "accuracy_score",
            sa.Integer(),
            nullable=False,
            comment="How accurate is the response? (1-5)",
        ),
        sa.Column(
            "helpfulness_score",
            sa.Integer(),
            nullable=False,
            comment="How helpful is the response? (1-5)",
        ),
        sa.Column(
            "tone_score", sa.Integer(), nullable=False, comment="Appropriate tone for brand? (1-5)"
        ),
        sa.Column(
            "completeness_score",
            sa.Integer(),
            nullable=False,
            comment="Addresses all aspects of query? (1-5)",
        ),
        # Overall assessment
        sa.Column(
            "overall_score", sa.Float(), nullable=False, comment="Average of all scores (1-5)"
        ),
        sa.Column(
            "would_use_in_production",
            sa.Boolean(),
            nullable=False,
            comment="Would you use this response with customer?",
        ),
        # Comments
        sa.Column("feedback_notes", sa.Text(), nullable=True, comment="Reviewer comments"),
        # Metadata
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        # Foreign key
        sa.ForeignKeyConstraint(["tutor_pair_id"], ["ai_tutor_pairs.id"], ondelete="CASCADE"),
    )

    # Create indexes for ai_rlhf_scores
    op.create_index("ix_ai_rlhf_scores_id", "ai_rlhf_scores", ["id"])
    op.create_index("ix_ai_rlhf_scores_tutor_pair_id", "ai_rlhf_scores", ["tutor_pair_id"])
    op.create_index("ix_ai_rlhf_scores_created_at", "ai_rlhf_scores", ["created_at"])
    op.create_index("idx_rlhf_tutor", "ai_rlhf_scores", ["tutor_pair_id"])
    op.create_index("idx_rlhf_overall", "ai_rlhf_scores", ["overall_score", "created_at"])
    op.create_index(
        "idx_rlhf_production", "ai_rlhf_scores", ["would_use_in_production", "created_at"]
    )

    # 3. Create ai_export_jobs table
    op.create_table(
        "ai_export_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        # Job details
        sa.Column(
            "export_type", sa.String(50), nullable=False, comment="fine_tuning/evaluation/backup"
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "in_progress",
                "completed",
                "failed",
                name="exportstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        # Export criteria
        sa.Column(
            "min_similarity_score",
            sa.Float(),
            nullable=False,
            server_default="0.85",
            comment="Minimum similarity threshold",
        ),
        sa.Column(
            "min_rlhf_score", sa.Float(), nullable=True, comment="Minimum RLHF score if available"
        ),
        sa.Column("date_range_start", sa.DateTime(), nullable=True),
        sa.Column("date_range_end", sa.DateTime(), nullable=True),
        # Results
        sa.Column(
            "pairs_exported", sa.Integer(), server_default="0", comment="Number of pairs exported"
        ),
        sa.Column("output_file_path", sa.String(500), nullable=True, comment="Path to JSONL file"),
        sa.Column("output_file_size_mb", sa.Float(), nullable=True),
        # Error handling
        sa.Column("error_message", sa.Text(), nullable=True),
        # Metadata
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="Admin user who initiated"),
    )

    # Create indexes for ai_export_jobs
    op.create_index("ix_ai_export_jobs_id", "ai_export_jobs", ["id"])
    op.create_index("ix_ai_export_jobs_status", "ai_export_jobs", ["status"])
    op.create_index("ix_ai_export_jobs_created_at", "ai_export_jobs", ["created_at"])
    op.create_index("idx_export_status", "ai_export_jobs", ["status", "created_at"])
    op.create_index("idx_export_type", "ai_export_jobs", ["export_type", "status"])


def downgrade():
    """Drop Shadow Learning tables"""

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table("ai_export_jobs")
    op.drop_table("ai_rlhf_scores")
    op.drop_table("ai_tutor_pairs")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS exportstatus")
