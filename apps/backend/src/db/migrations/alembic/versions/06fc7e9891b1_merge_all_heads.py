"""merge_all_heads

Revision ID: 06fc7e9891b1
Revises: 004_station_rbac, 008_add_user_roles, ea9069521d16
Create Date: 2025-10-28 16:21:10.643429

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '06fc7e9891b1'
down_revision = ('004_station_rbac', '008_add_user_roles', 'ea9069521d16')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass