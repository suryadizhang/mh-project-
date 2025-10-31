"""merge_payment_notifications

Revision ID: f069ddb440f7
Revises: 009_payment_notifications, cd22216ae9d3
Create Date: 2025-10-30 10:08:41.970154

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f069ddb440f7'
down_revision = ('009_payment_notifications', 'cd22216ae9d3')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass