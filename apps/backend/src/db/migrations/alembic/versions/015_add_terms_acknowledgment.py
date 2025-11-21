"""Add terms acknowledgment system

Revision ID: 015_add_terms_acknowledgment
Revises: 014_add_sms_consent
Create Date: 2025-01-03

Creates terms_acknowledgments table to track customer agreement
to terms & conditions across all booking channels (web, phone, SMS, AI).

This provides legal protection by recording:
- Who agreed (customer_id)
- What they agreed to (terms_version, terms_url)
- When they agreed (acknowledged_at)
- How they agreed (channel, method, acknowledgment_text)
- Where they agreed from (ip_address, user_agent)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET, UUID


# revision identifiers, used by Alembic.
revision: str = "015_add_terms_acknowledgment"
down_revision: Union[str, None] = "014_add_sms_consent"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create terms_acknowledgments table"""

    # Create terms_acknowledgments table in public schema
    op.create_table(
        "terms_acknowledgments",
        # Primary key
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
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
        # Who agreed - use INTEGER to match public.customers and public.bookings
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=True),
        # What they agreed to
        sa.Column("terms_version", sa.String(length=20), nullable=False, server_default="1.0"),
        sa.Column("terms_url", sa.String(length=500), nullable=False),
        sa.Column("terms_text_hash", sa.String(length=64), nullable=True),
        # When they agreed
        sa.Column(
            "acknowledged_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # How they agreed
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("acknowledgment_method", sa.String(length=50), nullable=False),
        sa.Column("acknowledgment_text", sa.Text(), nullable=True),
        # Legal proof for SMS/RingCentral
        sa.Column("sms_message_id", sa.String(length=100), nullable=True),
        sa.Column("sms_message_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sms_message_hash", sa.String(length=64), nullable=True),
        sa.Column("webhook_source_ip", INET(), nullable=True),
        # Where they agreed from
        sa.Column("ip_address", INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        # Staff context (for phone/in-person)
        sa.Column("staff_member_name", sa.String(length=255), nullable=True),
        sa.Column("staff_member_email", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # Verification
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        # Foreign keys to public schema tables
        sa.ForeignKeyConstraint(["customer_id"], ["public.customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["booking_id"], ["public.bookings.id"], ondelete="SET NULL"),
        schema="public",
    )

    # Create indexes for common queries
    op.create_index(
        "ix_terms_acknowledgments_customer_id",
        "terms_acknowledgments",
        ["customer_id"],
        schema="public",
    )
    op.create_index(
        "ix_terms_acknowledgments_booking_id",
        "terms_acknowledgments",
        ["booking_id"],
        schema="public",
    )
    op.create_index(
        "ix_terms_acknowledgments_acknowledged_at",
        "terms_acknowledgments",
        ["acknowledged_at"],
        schema="public",
    )
    op.create_index(
        "ix_terms_acknowledgments_channel", "terms_acknowledgments", ["channel"], schema="public"
    )

    # Composite index for finding customer's latest acknowledgment
    op.create_index(
        "ix_terms_acknowledgments_customer_latest",
        "terms_acknowledgments",
        ["customer_id", "acknowledged_at"],
        postgresql_ops={"acknowledged_at": "DESC"},
        schema="public",
    )


def downgrade() -> None:
    """Remove terms_acknowledgments table"""

    # Drop indexes
    op.drop_index(
        "ix_terms_acknowledgments_customer_latest",
        table_name="terms_acknowledgments",
        schema="public",
    )
    op.drop_index(
        "ix_terms_acknowledgments_channel", table_name="terms_acknowledgments", schema="public"
    )
    op.drop_index(
        "ix_terms_acknowledgments_acknowledged_at",
        table_name="terms_acknowledgments",
        schema="public",
    )
    op.drop_index(
        "ix_terms_acknowledgments_booking_id", table_name="terms_acknowledgments", schema="public"
    )
    op.drop_index(
        "ix_terms_acknowledgments_customer_id", table_name="terms_acknowledgments", schema="public"
    )

    # Drop table
    op.drop_table("terms_acknowledgments", schema="public")
