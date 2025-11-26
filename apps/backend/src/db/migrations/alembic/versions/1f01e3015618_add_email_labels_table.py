"""add_email_labels_table

Revision ID: 1f01e3015618
Revises: 2a1a11964b93
Create Date: 2025-11-25 00:43:17.714120

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1f01e3015618'
down_revision = '2a1a11964b93'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add email_labels table for custom email organization.

    Uses IF NOT EXISTS to handle cases where table already exists.
    """
    # Create email_labels table
    op.execute("""
        CREATE TABLE IF NOT EXISTS email_labels (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            slug VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            color VARCHAR(7) NOT NULL DEFAULT '#6B7280',
            icon VARCHAR(50),
            is_system BOOLEAN NOT NULL DEFAULT FALSE,
            is_archived BOOLEAN NOT NULL DEFAULT FALSE,
            email_count INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            is_deleted BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)

    # Create indexes (IF NOT EXISTS supported in PostgreSQL 9.5+)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_name_archived
        ON email_labels (name, is_archived)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sort_order
        ON email_labels (sort_order)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_email_labels_id
        ON email_labels (id)
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_email_labels_name
        ON email_labels (name)
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_email_labels_slug
        ON email_labels (slug)
    """)


def downgrade() -> None:
    """Remove email_labels table and indexes."""
    op.execute("DROP INDEX IF EXISTS ix_email_labels_slug")
    op.execute("DROP INDEX IF EXISTS ix_email_labels_name")
    op.execute("DROP INDEX IF EXISTS ix_email_labels_id")
    op.execute("DROP INDEX IF EXISTS idx_sort_order")
    op.execute("DROP INDEX IF EXISTS idx_name_archived")
    op.execute("DROP TABLE IF EXISTS email_labels")
