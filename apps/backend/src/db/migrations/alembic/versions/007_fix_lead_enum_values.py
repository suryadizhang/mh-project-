"""Fix lead and newsletter enum values to match Python models

Revision ID: 007_fix_lead_enum_values
Revises: 006_add_roles_permissions
Create Date: 2025-11-14 00:45:00.000000

Adds missing enum values that exist in Python models but not in database:
- LeadSource: booking_failed, google_my_business, payment, financial, stripe, plaid
- LeadStatus: customer (for converted customers)
- ThreadStatus: closed, urgent (vs snoozed, escalated in database)

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_fix_lead_enum_values'
down_revision = '006_add_roles_permissions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing enum values to match Python models."""
    
    # Add missing values to lead_source enum
    # Database has: web_quote, chat, instagram, facebook, google, yelp, sms, phone, referral, event
    # Python needs: + booking_failed, google_my_business, payment, financial, stripe, plaid
    op.execute("ALTER TYPE lead_source ADD VALUE IF NOT EXISTS 'booking_failed'")
    op.execute("ALTER TYPE lead_source ADD VALUE IF NOT EXISTS 'google_my_business'")
    op.execute("ALTER TYPE lead_source ADD VALUE IF NOT EXISTS 'payment'")
    op.execute("ALTER TYPE lead_source ADD VALUE IF NOT EXISTS 'financial'")
    op.execute("ALTER TYPE lead_source ADD VALUE IF NOT EXISTS 'stripe'")
    op.execute("ALTER TYPE lead_source ADD VALUE IF NOT EXISTS 'plaid'")
    
    # Add missing value to lead_status enum
    # Database has: new, working, qualified, disqualified, converted, nurturing
    # Python needs: + customer
    op.execute("ALTER TYPE lead_status ADD VALUE IF NOT EXISTS 'customer'")
    
    # NOTE: ThreadStatus mismatch - database has 'snoozed', 'escalated'
    # Python model has 'closed', 'urgent'
    # This is intentional - keeping both sets for backward compatibility
    op.execute("ALTER TYPE thread_status ADD VALUE IF NOT EXISTS 'closed'")
    op.execute("ALTER TYPE thread_status ADD VALUE IF NOT EXISTS 'urgent'")


def downgrade() -> None:
    """
    Cannot remove enum values in PostgreSQL without recreating the type.
    This would require:
    1. Drop all columns using the enum
    2. Drop the enum type
    3. Recreate enum without the values
    4. Recreate all columns
    
    Not safe for production, so downgrade is not supported.
    """
    pass
