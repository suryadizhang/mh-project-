"""create_multi_schemas

Revision ID: cfeccbfaa133
Revises: fe61eb9d1264
Create Date: 2025-11-25 23:10:56.329409

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cfeccbfaa133"
down_revision = "fe61eb9d1264"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create multi-domain schemas for Phase 1B
    op.execute("CREATE SCHEMA IF NOT EXISTS ai")
    op.execute("CREATE SCHEMA IF NOT EXISTS crm")
    op.execute("CREATE SCHEMA IF NOT EXISTS ops")
    op.execute("CREATE SCHEMA IF NOT EXISTS marketing")
    op.execute("CREATE SCHEMA IF NOT EXISTS analytics")


def downgrade() -> None:
    # Drop schemas in reverse order
    op.execute("DROP SCHEMA IF EXISTS analytics CASCADE")
    op.execute("DROP SCHEMA IF EXISTS marketing CASCADE")
    op.execute("DROP SCHEMA IF EXISTS ops CASCADE")
    op.execute("DROP SCHEMA IF EXISTS crm CASCADE")
    op.execute("DROP SCHEMA IF EXISTS ai CASCADE")
