"""create_ai_schema

Creates the dedicated 'ai' schema for all AI/ML-related database tables.

This migration follows industry best practices from:
- Stripe: Dedicated schemas per domain (billing, identity, fraud)
- Shopify: Separate schemas for different business units
- Twilio: Isolated schemas for messaging, voice, video
- Intercom: Schema separation for conversations, customers, articles

Benefits of separate ai schema:
1. Isolation: Independent backup/restore for AI features
2. Permissions: Dedicated service account access control
3. Performance: Dedicated connection pools for AI workloads
4. Clarity: Explicit namespace (ai.conversations vs conversations)
5. Scalability: Can move ai schema to separate database/server later

Schema Organization:
Database
├── public (core business: bookings, customers, events)
├── identity (authentication, users, RBAC) ✅ COMPLETE
├── ai (conversations, engagement, analytics) ⏳ THIS MIGRATION
├── lead (marketing, newsletter)
└── payment (Stripe transactions)

Revision ID: 6fd48d0caced
Revises: 55f201d7ea25
Create Date: 2025-11-25 13:24:20.231384

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6fd48d0caced'
down_revision = '55f201d7ea25'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create the ai schema and set up proper permissions.
    """
    # Create ai schema
    op.execute("CREATE SCHEMA IF NOT EXISTS ai")

    # Note: Permissions are granted automatically to the database owner
    # If you need specific user permissions, uncomment and adjust these:
    #
    # op.execute("GRANT USAGE ON SCHEMA ai TO backend_user")
    # op.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ai TO backend_user")
    # op.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ai TO backend_user")
    # op.execute("""
    #     ALTER DEFAULT PRIVILEGES IN SCHEMA ai
    #     GRANT ALL ON TABLES TO backend_user
    # """)
    # op.execute("""
    #     ALTER DEFAULT PRIVILEGES IN SCHEMA ai
    #     GRANT ALL ON SEQUENCES TO backend_user
    # """)

    # Add comment to schema for documentation
    op.execute("""
        COMMENT ON SCHEMA ai IS
        'AI/ML features: conversations, engagement, analytics, shadow learning.
         Isolated for independent scaling and backup/restore operations.'
    """)


def downgrade() -> None:
    """
    Drop the ai schema.

    WARNING: This will CASCADE delete all tables in the ai schema!
    Use with extreme caution in production environments.
    """
    # Drop schema (CASCADE will drop all tables)
    op.execute("DROP SCHEMA IF EXISTS ai CASCADE")
