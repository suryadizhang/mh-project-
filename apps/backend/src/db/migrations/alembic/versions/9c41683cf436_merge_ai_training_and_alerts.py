"""merge_ai_training_and_alerts

Revision ID: 9c41683cf436
Revises: 010_ai_hospitality_training, 573ac0543ebb
Create Date: 2025-11-11 18:49:20.247052

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9c41683cf436"
down_revision = ("010_ai_hospitality_training", "573ac0543ebb")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
