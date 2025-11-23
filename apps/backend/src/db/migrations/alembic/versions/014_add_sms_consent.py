"""Add SMS consent fields for TCPA compliance

Revision ID: 014_add_sms_consent
Revises: 013_add_deposit_deadline
Create Date: 2025-01-03

Adds SMS consent tracking fields to bookings table:
- sms_consent: Boolean flag indicating customer consent
- sms_consent_timestamp: When consent was given

This is required for TCPA compliance when sending SMS notifications.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "014_add_sms_consent"
down_revision: Union[str, None] = "013_add_deposit_deadline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add SMS consent fields to bookings table"""
    # Add sms_consent column (default False for existing records)
    op.add_column(
        "bookings", sa.Column("sms_consent", sa.Boolean(), nullable=False, server_default="false"), schema="core"
    )

    # Add sms_consent_timestamp column (nullable - only set when consent given)
    op.add_column(
        "bookings", sa.Column("sms_consent_timestamp", sa.DateTime(timezone=True), nullable=True), schema="core"
    )

    # Create index for consent queries (useful for compliance reports)
    op.create_index("ix_bookings_sms_consent", "bookings", ["sms_consent"], unique=False, schema="core")


def downgrade() -> None:
    """Remove SMS consent fields"""
    # Drop index first
    op.drop_index("ix_bookings_sms_consent", table_name="bookings", schema="core")

    # Drop columns
    op.drop_column("bookings", "sms_consent_timestamp", schema="core")
    op.drop_column("bookings", "sms_consent", schema="core")
