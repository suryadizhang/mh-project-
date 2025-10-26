"""merge migrations

Revision ID: 9fd62e8ed3b4
Revises: 001_initial_stripe_tables, 003_add_social_media_integration
Create Date: 2025-09-25 13:09:20.699072

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9fd62e8ed3b4'
down_revision = ('001_initial_stripe_tables', '003_add_social_media_integration')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass