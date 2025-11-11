"""Add escalation and call recording tables

Revision ID: add_escalation_call_recording
Revises: previous_migration
Create Date: 2025-11-10 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_escalation_call_recording"
down_revision = "previous_migration"  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create support schema if it doesn't exist
    op.execute("CREATE SCHEMA IF NOT EXISTS support")
    op.execute("CREATE SCHEMA IF NOT EXISTS communications")

    # Create escalation status enum
    escalation_status_enum = postgresql.ENUM(
        "pending",
        "assigned",
        "in_progress",
        "waiting_customer",
        "resolved",
        "closed",
        "error",
        name="escalationstatus",
        schema="support",
    )
    escalation_status_enum.create(op.get_bind(), checkfirst=True)

    # Create escalation method enum
    escalation_method_enum = postgresql.ENUM(
        "sms", "call", "email", name="escalationmethod", schema="support"
    )
    escalation_method_enum.create(op.get_bind(), checkfirst=True)

    # Create escalation priority enum
    escalation_priority_enum = postgresql.ENUM(
        "low", "medium", "high", "urgent", name="escalationpriority", schema="support"
    )
    escalation_priority_enum.create(op.get_bind(), checkfirst=True)

    # Create recording status enum
    recording_status_enum = postgresql.ENUM(
        "pending",
        "downloading",
        "available",
        "archived",
        "deleted",
        "error",
        name="recordingstatus",
        schema="communications",
    )
    recording_status_enum.create(op.get_bind(), checkfirst=True)

    # Create recording type enum
    recording_type_enum = postgresql.ENUM(
        "inbound", "outbound", "internal", name="recordingtype", schema="communications"
    )
    recording_type_enum.create(op.get_bind(), checkfirst=True)

    # Create escalations table
    op.create_table(
        "escalations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("phone", sa.String(20), nullable=False, index=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("preferred_method", escalation_method_enum, nullable=False, server_default="sms"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "priority",
            escalation_priority_enum,
            nullable=False,
            server_default="medium",
            index=True,
        ),
        sa.Column(
            "status", escalation_status_enum, nullable=False, server_default="pending", index=True
        ),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("sms_sent", sa.DateTime(timezone=True), nullable=True),
        sa.Column("call_initiated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_contact_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.String(10), nullable=False, server_default="0"),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column(
            "tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("customer_consent", sa.String(10), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["customer_id"], ["bookings.customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["identity.users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resolved_by_id"], ["identity.users.id"], ondelete="SET NULL"),
        schema="support",
    )

    # Create call_recordings table
    op.create_table(
        "call_recordings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rc_call_id", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("rc_recording_id", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("rc_recording_uri", sa.Text(), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("escalation_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column(
            "call_type", recording_type_enum, nullable=False, server_default="inbound", index=True
        ),
        sa.Column("from_phone", sa.String(20), nullable=False, index=True),
        sa.Column("to_phone", sa.String(20), nullable=False, index=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("call_started_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("call_ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status", recording_status_enum, nullable=False, server_default="pending", index=True
        ),
        sa.Column("s3_bucket", sa.String(255), nullable=True),
        sa.Column("s3_key", sa.String(500), nullable=True),
        sa.Column("s3_uri", sa.Text(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(100), nullable=True),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column(
            "tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"
        ),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("delete_after", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column("accessed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_accessed_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("download_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.bookings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["bookings.customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["escalation_id"], ["support.escalations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["agent_id"], ["identity.users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["last_accessed_by_id"], ["identity.users.id"], ondelete="SET NULL"
        ),
        schema="communications",
    )

    # Create indexes for performance
    op.create_index(
        "idx_escalations_status_created", "escalations", ["status", "created_at"], schema="support"
    )
    op.create_index(
        "idx_escalations_assigned_to", "escalations", ["assigned_to_id", "status"], schema="support"
    )
    op.create_index(
        "idx_call_recordings_customer",
        "call_recordings",
        ["customer_id", "created_at"],
        schema="communications",
    )
    op.create_index(
        "idx_call_recordings_booking",
        "call_recordings",
        ["booking_id", "created_at"],
        schema="communications",
    )
    op.create_index(
        "idx_call_recordings_delete_after",
        "call_recordings",
        ["delete_after"],
        schema="communications",
        postgresql_where=sa.text("delete_after IS NOT NULL"),
    )
    op.create_index(
        "idx_call_recordings_status_created",
        "call_recordings",
        ["status", "created_at"],
        schema="communications",
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        "idx_call_recordings_status_created", table_name="call_recordings", schema="communications"
    )
    op.drop_index(
        "idx_call_recordings_delete_after", table_name="call_recordings", schema="communications"
    )
    op.drop_index(
        "idx_call_recordings_booking", table_name="call_recordings", schema="communications"
    )
    op.drop_index(
        "idx_call_recordings_customer", table_name="call_recordings", schema="communications"
    )
    op.drop_index("idx_escalations_assigned_to", table_name="escalations", schema="support")
    op.drop_index("idx_escalations_status_created", table_name="escalations", schema="support")

    # Drop tables
    op.drop_table("call_recordings", schema="communications")
    op.drop_table("escalations", schema="support")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS communications.recordingtype")
    op.execute("DROP TYPE IF EXISTS communications.recordingstatus")
    op.execute("DROP TYPE IF EXISTS support.escalationpriority")
    op.execute("DROP TYPE IF EXISTS support.escalationmethod")
    op.execute("DROP TYPE IF EXISTS support.escalationstatus")
