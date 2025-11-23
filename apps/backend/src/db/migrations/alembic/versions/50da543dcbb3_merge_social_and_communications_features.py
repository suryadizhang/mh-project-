"""merge_social_and_communications_features

Revision ID: 50da543dcbb3
Revises: 010_escalation_call_recording, 017_fix_foreign_key_relationships
Create Date: 2025-11-22 00:41:28.987611

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '50da543dcbb3'
down_revision = ('010_escalation_call_recording', 'a7b8c9d0e1f2')  # Updated to use short hash
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass