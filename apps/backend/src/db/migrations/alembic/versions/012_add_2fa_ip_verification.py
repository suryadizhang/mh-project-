"""
Database migration: Add 2FA and IP verification fields
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, INET

# revision identifiers
revision = "012_add_2fa_ip_verification"
down_revision = "010_ai_hospitality_training"
branch_labels = None
depends_on = None


def upgrade():
    """Add 2FA and IP verification fields to users table."""

    # Add mfa_backup_codes column (array of hashed backup codes)
    op.add_column("users", sa.Column("mfa_backup_codes", JSONB, nullable=True), schema="identity")

    # Add trusted_ips column (array of trusted IP addresses)
    op.add_column("users", sa.Column("trusted_ips", ARRAY(INET), nullable=True), schema="identity")

    # Add ip_verification_enabled flag
    op.add_column(
        "users",
        sa.Column(
            "ip_verification_enabled",
            sa.Boolean,
            default=False,
            nullable=False,
            server_default="false",
        ),
        schema="identity",
    )

    # Add last_known_ip for comparison
    op.add_column("users", sa.Column("last_known_ip", INET, nullable=True), schema="identity")

    # Create index on ip_verification_enabled for filtering
    op.create_index(
        "idx_users_ip_verification", "users", ["ip_verification_enabled"], schema="identity"
    )


def downgrade():
    """Remove 2FA and IP verification fields."""
    op.drop_index("idx_users_ip_verification", table_name="users", schema="identity")
    op.drop_column("users", "last_known_ip", schema="identity")
    op.drop_column("users", "ip_verification_enabled", schema="identity")
    op.drop_column("users", "trusted_ips", schema="identity")
    op.drop_column("users", "mfa_backup_codes", schema="identity")
