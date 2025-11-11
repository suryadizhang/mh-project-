"""merge_escalation_and_business_migrations

Revision ID: 73b5896f4fd5
Revises: 010_escalation_call_recording, e8e33e1e5658
Create Date: 2025-11-10 16:23:18.270103

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73b5896f4fd5'
down_revision = ('010_escalation_call_recording', 'e8e33e1e5658')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass