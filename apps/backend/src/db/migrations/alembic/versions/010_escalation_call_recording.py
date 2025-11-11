"""
Add escalation and call recording system

Revision ID: 010_escalation_call_recording
Revises: 009_payment_notifications
Create Date: 2025-11-10 00:00:00.000000

Tables:
- support.escalations: Customer support escalation tracking
- communications.call_recordings: RingCentral call recording metadata

Features:
- AI to human handoff workflow
- Phone/email/preferred escalation methods
- Priority levels (low, medium, high, urgent)
- Assignment and resolution tracking
- Call recording storage on VPS filesystem
- Retention policy and auto-deletion
- Access audit logging
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "010_escalation_call_recording"
down_revision = "009_payment_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create escalation and call recording tables"""

    # Create schemas if they don't exist
    op.execute("CREATE SCHEMA IF NOT EXISTS support")
    op.execute("CREATE SCHEMA IF NOT EXISTS communications")

    # Create ENUM types for escalations
    op.execute(
        """
        CREATE TYPE support.escalation_status AS ENUM (
            'pending',
            'assigned',
            'in_progress',
            'waiting_customer',
            'resolved',
            'closed',
            'error'
        )
    """
    )

    op.execute(
        """
        CREATE TYPE support.escalation_method AS ENUM (
            'phone',
            'email',
            'preferred_method'
        )
    """
    )

    op.execute(
        """
        CREATE TYPE support.escalation_priority AS ENUM (
            'low',
            'medium',
            'high',
            'urgent'
        )
    """
    )

    # Create ENUM types for call recordings
    op.execute(
        """
        CREATE TYPE communications.recording_status AS ENUM (
            'pending',
            'downloading',
            'available',
            'archived',
            'deleted',
            'error'
        )
    """
    )

    op.execute(
        """
        CREATE TYPE communications.recording_type AS ENUM (
            'inbound',
            'outbound',
            'internal'
        )
    """
    )

    # Create escalations table
    op.create_table(
        "escalations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", sa.String(255), nullable=False, index=True),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("customer_phone", sa.String(20), nullable=False, index=True),
        sa.Column("customer_email", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column(
            "priority",
            postgresql.ENUM(
                "low", "medium", "high", "urgent", name="escalation_priority", create_type=False
            ),
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "method",
            postgresql.ENUM(
                "phone", "email", "preferred_method", name="escalation_method", create_type=False
            ),
            nullable=False,
            server_default="phone",
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "assigned",
                "in_progress",
                "waiting_customer",
                "resolved",
                "closed",
                "error",
                name="escalation_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
            index=True,
        ),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text, nullable=True),
        sa.Column("resume_ai_chat", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("last_customer_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sms_sent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sms_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("call_initiated", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("call_initiated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("escalation_metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
        ),
        schema="support",
    )

    # Create call_recordings table
    op.create_table(
        "call_recordings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("escalation_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("rc_call_id", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("rc_recording_id", sa.String(255), nullable=False, unique=True),
        sa.Column("rc_recording_uri", sa.String(500), nullable=True),
        sa.Column(
            "recording_type",
            postgresql.ENUM(
                "inbound", "outbound", "internal", name="recording_type", create_type=False
            ),
            nullable=False,
            server_default="inbound",
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "downloading",
                "available",
                "archived",
                "deleted",
                "error",
                name="recording_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
            index=True,
        ),
        sa.Column("call_started_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=True),
        sa.Column("content_type", sa.String(50), nullable=True),
        sa.Column("s3_bucket", sa.String(255), nullable=True),
        sa.Column("s3_key", sa.String(500), nullable=True),
        sa.Column("s3_uri", sa.String(1000), nullable=True),
        sa.Column("retention_days", sa.Integer, nullable=False, server_default="90"),
        sa.Column("delete_after", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("download_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("accessed_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_accessed_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recording_metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
        ),
        schema="communications",
    )

    # Create foreign key constraints
    op.create_foreign_key(
        "fk_escalations_assigned_to",
        "escalations",
        "users",
        ["assigned_to_id"],
        ["id"],
        source_schema="support",
        referent_schema="public",
        ondelete="SET NULL",
    )

    op.create_foreign_key(
        "fk_call_recordings_escalation",
        "call_recordings",
        "escalations",
        ["escalation_id"],
        ["id"],
        source_schema="communications",
        referent_schema="support",
        ondelete="SET NULL",
    )

    op.create_foreign_key(
        "fk_call_recordings_accessed_by",
        "call_recordings",
        "users",
        ["last_accessed_by_id"],
        ["id"],
        source_schema="communications",
        referent_schema="public",
        ondelete="SET NULL",
    )

    # Create indexes for common queries
    op.create_index("idx_escalations_created_at", "escalations", ["created_at"], schema="support")

    op.create_index(
        "idx_escalations_status_priority", "escalations", ["status", "priority"], schema="support"
    )

    op.create_index(
        "idx_escalations_assigned_status",
        "escalations",
        ["assigned_to_id", "status"],
        schema="support",
    )

    op.create_index(
        "idx_call_recordings_escalation",
        "call_recordings",
        ["escalation_id"],
        schema="communications",
    )

    op.create_index(
        "idx_call_recordings_date_status",
        "call_recordings",
        ["call_started_at", "status"],
        schema="communications",
    )

    op.create_index(
        "idx_call_recordings_delete_after",
        "call_recordings",
        ["delete_after"],
        schema="communications",
        postgresql_where=sa.text("delete_after IS NOT NULL"),
    )

    # Create updated_at trigger functions
    op.execute(
        """
        CREATE OR REPLACE FUNCTION support.update_escalations_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER escalations_updated_at_trigger
        BEFORE UPDATE ON support.escalations
        FOR EACH ROW
        EXECUTE FUNCTION support.update_escalations_updated_at();
    """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION communications.update_call_recordings_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER call_recordings_updated_at_trigger
        BEFORE UPDATE ON communications.call_recordings
        FOR EACH ROW
        EXECUTE FUNCTION communications.update_call_recordings_updated_at();
    """
    )


def downgrade() -> None:
    """Drop escalation and call recording tables"""

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS escalations_updated_at_trigger ON support.escalations")
    op.execute("DROP FUNCTION IF EXISTS support.update_escalations_updated_at()")
    op.execute(
        "DROP TRIGGER IF EXISTS call_recordings_updated_at_trigger ON communications.call_recordings"
    )
    op.execute("DROP FUNCTION IF EXISTS communications.update_call_recordings_updated_at()")

    # Drop tables (foreign keys will be dropped automatically)
    op.drop_table("call_recordings", schema="communications")
    op.drop_table("escalations", schema="support")

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS support.escalation_status")
    op.execute("DROP TYPE IF EXISTS support.escalation_method")
    op.execute("DROP TYPE IF EXISTS support.escalation_priority")
    op.execute("DROP TYPE IF EXISTS communications.recording_status")
    op.execute("DROP TYPE IF EXISTS communications.recording_type")

    # Note: We don't drop schemas as they may contain other tables
