"""merge roles migrations

Revision ID: cd22216ae9d3
Revises: 006_add_roles_permissions, 06fc7e9891b1
Create Date: 2025-10-29 00:22:14.701006

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cd22216ae9d3'
down_revision = ('006_add_roles_permissions', '06fc7e9891b1')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass