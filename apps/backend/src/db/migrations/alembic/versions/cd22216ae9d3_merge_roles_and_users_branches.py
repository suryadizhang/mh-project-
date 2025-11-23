"""merge roles and users branches

Revision ID: cd22216ae9d3
Revises: 006_add_roles_permissions, 008_add_user_roles
Create Date: 2025-11-22 01:15:00.000000

This merge brings together two critical branches:
- Branch A: 008_add_user_roles (public.users with roles)
- Branch B: 006_add_roles_permissions (identity schema with permissions)

This ensures identity.users exists before migrations reference it.

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cd22216ae9d3'
down_revision = ('006_add_roles_permissions', '008_add_user_roles')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
