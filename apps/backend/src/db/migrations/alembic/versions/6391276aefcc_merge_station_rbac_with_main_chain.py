"""merge_station_rbac_with_main_chain

Revision ID: 6391276aefcc
Revises: 004_station_rbac, cafcd735e7fe
Create Date: 2025-11-22 00:57:42.338366

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6391276aefcc'
down_revision = ('004_station_rbac', 'cafcd735e7fe')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass