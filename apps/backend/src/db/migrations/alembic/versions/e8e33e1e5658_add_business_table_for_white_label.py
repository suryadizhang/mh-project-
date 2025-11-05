"""add_business_table_for_white_label

White-Label Multi-Tenancy Foundation:
- Creates businesses table for supporting multiple restaurant brands
- Currently: My Hibachi Chef (self-hosted, $0/month)
- Future: Other catering businesses can white-label the platform ($500-3000/month)

Revision ID: e8e33e1e5658
Revises: e636a2d56d82
Create Date: 2025-11-04 20:17:13.774133

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "e8e33e1e5658"
down_revision = "e636a2d56d82"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create businesses table
    op.create_table(
        "businesses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "name", sa.String(255), nullable=False, comment='Brand name (e.g., "My Hibachi Chef")'
        ),
        sa.Column(
            "slug",
            sa.String(100),
            nullable=False,
            unique=True,
            index=True,
            comment='URL-safe identifier (e.g., "my-hibachi-chef")',
        ),
        sa.Column(
            "domain",
            sa.String(255),
            nullable=True,
            unique=True,
            comment='Custom domain (e.g., "myhibachichef.com")',
        ),
        # Branding
        sa.Column("logo_url", sa.String(500), nullable=True, comment="Logo image URL"),
        sa.Column(
            "primary_color",
            sa.String(7),
            nullable=True,
            server_default="#FF6B6B",
            comment="Brand primary color (hex)",
        ),
        sa.Column(
            "secondary_color",
            sa.String(7),
            nullable=True,
            server_default="#4ECDC4",
            comment="Brand secondary color (hex)",
        ),
        # Contact Information
        sa.Column("phone", sa.String(20), nullable=True, comment="Business phone number"),
        sa.Column("email", sa.String(255), nullable=True, comment="Business contact email"),
        sa.Column("address", sa.Text(), nullable=True, comment="Business physical address"),
        # Business Settings
        sa.Column(
            "timezone",
            sa.String(50),
            nullable=False,
            server_default="America/Los_Angeles",
            comment="Business timezone",
        ),
        sa.Column(
            "currency",
            sa.String(3),
            nullable=False,
            server_default="USD",
            comment="Business currency code",
        ),
        sa.Column(
            "settings",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
            comment="Additional business-specific settings",
        ),
        # Subscription (White-Label Revenue Model)
        sa.Column(
            "subscription_tier",
            sa.String(50),
            nullable=False,
            server_default="self_hosted",
            comment="Subscription tier: self_hosted, basic, pro, enterprise",
        ),
        sa.Column(
            "subscription_status",
            sa.String(20),
            nullable=False,
            server_default="active",
            comment="Subscription status: active, trial, suspended, canceled",
        ),
        sa.Column(
            "monthly_fee",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0.00",
            comment="Monthly subscription fee in USD",
        ),
        # Metadata
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="Whether business is active",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            comment="Business creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            comment="Business last update timestamp",
        ),
        comment="Businesses table for white-label multi-tenancy support",
    )

    # Create indexes for performance
    op.create_index("ix_businesses_slug", "businesses", ["slug"], unique=True)
    op.create_index("ix_businesses_domain", "businesses", ["domain"], unique=True)
    op.create_index("ix_businesses_subscription_status", "businesses", ["subscription_status"])
    op.create_index("ix_businesses_is_active", "businesses", ["is_active"])

    # Insert My Hibachi Chef as the default business (self-hosted)
    op.execute(
        """
        INSERT INTO businesses (
            name, slug, domain, 
            logo_url, primary_color, secondary_color,
            phone, email, address,
            timezone, currency, settings,
            subscription_tier, subscription_status, monthly_fee,
            is_active
        ) VALUES (
            'My Hibachi Chef',
            'my-hibachi-chef',
            'myhibachichef.com',
            NULL,
            '#FF6B6B',
            '#4ECDC4',
            '555-0123',
            'info@myhibachichef.com',
            '123 Hibachi Lane, Los Angeles, CA 90001',
            'America/Los_Angeles',
            'USD',
            '{}'::jsonb,
            'self_hosted',
            'active',
            0.00,
            true
        )
        ON CONFLICT (slug) DO NOTHING;
    """
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_businesses_is_active", "businesses")
    op.drop_index("ix_businesses_subscription_status", "businesses")
    op.drop_index("ix_businesses_domain", "businesses")
    op.drop_index("ix_businesses_slug", "businesses")

    # Drop businesses table
    op.drop_table("businesses")
