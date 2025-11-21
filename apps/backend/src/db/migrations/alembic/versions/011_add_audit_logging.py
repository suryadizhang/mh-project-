"""
Database migration: Add audit logging tables
Tracks all database changes for security and compliance
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, ARRAY

# revision identifiers
revision = "011_add_audit_logging"
down_revision = "010_ai_hospitality_training"  # Previous migration
branch_labels = None
depends_on = None


def upgrade():
    """Create audit logging tables."""

    # Create audit_logs table for tracking all database changes
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("table_name", sa.String(100), nullable=False, index=True),
        sa.Column("record_id", UUID, nullable=True, index=True),
        sa.Column("action", sa.String(20), nullable=False, index=True),  # INSERT, UPDATE, DELETE
        sa.Column("old_values", JSONB, nullable=True),
        sa.Column("new_values", JSONB, nullable=True),
        sa.Column(
            "changed_fields", ARRAY(sa.Text), nullable=True
        ),  # Array of field names that changed
        sa.Column("user_id", UUID, nullable=True, index=True),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("ip_address", INET, nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column(
            "timestamp",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            index=True,
        ),
        # Foreign key to users table
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )

    # Create composite index for common queries
    op.create_index("idx_audit_table_record", "audit_logs", ["table_name", "record_id"])
    op.create_index("idx_audit_timestamp_desc", "audit_logs", [sa.text("timestamp DESC")])

    # Create security_audit_logs table for high-value security events
    op.create_table(
        "security_audit_logs",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "event_type", sa.String(50), nullable=False, index=True
        ),  # LOGIN, LOGOUT, PERMISSION_CHANGE, etc.
        sa.Column("user_id", UUID, nullable=True, index=True),
        sa.Column(
            "target_user_id", UUID, nullable=True
        ),  # For permission changes affecting another user
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("ip_address", INET, nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("success", sa.Boolean, default=True),  # Track failed attempts
        sa.Column("failure_reason", sa.Text, nullable=True),
        sa.Column(
            "timestamp",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            index=True,
        ),
        # Foreign keys
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="SET NULL"),
    )

    # Create index for security event queries
    op.create_index("idx_security_event_type", "security_audit_logs", ["event_type"])
    op.create_index("idx_security_user", "security_audit_logs", ["user_id"])
    op.create_index(
        "idx_security_timestamp_desc", "security_audit_logs", [sa.text("timestamp DESC")]
    )
    op.create_index(
        "idx_security_failed",
        "security_audit_logs",
        ["success"],
        postgresql_where=sa.text("success = false"),
    )


def downgrade():
    """Remove audit logging tables."""
    op.drop_table("security_audit_logs")
    op.drop_table("audit_logs")
