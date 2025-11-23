"""merge_payment_notifications

Revision ID: f069ddb440f7
Revises: 009_payment_notifications
Create Date: 2025-10-30 10:08:41.970154

NOTE: Originally merged 009_payment_notifications with cd22216ae9d3 (deleted).
Now simplified to single parent since cd22216ae9d3 was redundant.

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f069ddb440f7'
down_revision = '009_payment_notifications'  # Fixed: removed reference to deleted cd22216ae9d3
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass