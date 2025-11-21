"""merge_terms_system_with_main

Revision ID: 53bf4e839c3c
Revises: 015_add_terms_acknowledgment, e1814ce1d0e9, f5a8b9c2d3e4
Create Date: 2025-11-14 23:30:38.949510

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "53bf4e839c3c"
down_revision = ("015_add_terms_acknowledgment", "e1814ce1d0e9", "f5a8b9c2d3e4")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
