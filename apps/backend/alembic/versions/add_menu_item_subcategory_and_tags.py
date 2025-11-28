"""Add subcategory and tags to menu_items

Revision ID: add_menu_subcategory_tags
Revises: <previous_revision>
Create Date: 2025-11-27 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_menu_subcategory_tags"
down_revision = "6fed0b9d2bdd"  # Current head
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add subcategory and tags columns to menu_items table

    Category Hierarchy:
    - category: Main classification (protein, premium_protein, appetizer, add_on, sauce, side, base)
    - subcategory: Primary type (poultry, fish, shellfish, beef, pork, vegetarian, tofu)
    - tags: Multi-dimensional attributes (allergens, dietary info, cooking style)
    """
    # Add subcategory column
    op.add_column(
        "menu_items",
        sa.Column(
            "subcategory",
            sa.String(100),
            nullable=True,
            comment="Primary type: poultry, fish, shellfish, beef, pork, vegetarian, tofu",
        ),
    )

    # Add tags JSONB column with default empty array
    op.add_column(
        "menu_items",
        sa.Column(
            "tags",
            postgresql.JSONB,
            nullable=True,
            server_default="[]",
            comment="Multi-dimensional attributes: allergens, dietary info, cooking style",
        ),
    )

    # Create indexes for performance
    op.create_index("idx_menu_items_subcategory", "menu_items", ["subcategory"])
    op.create_index("idx_menu_items_tags", "menu_items", ["tags"], postgresql_using="gin")

    # Migrate existing data from dietary_info to tags (optional)
    # This preserves existing dietary information in the new tags system
    op.execute(
        """
        UPDATE menu_items
        SET tags = COALESCE(
            (
                SELECT jsonb_agg(elem)
                FROM unnest(dietary_info) AS elem
                WHERE dietary_info IS NOT NULL
            ),
            '[]'::jsonb
        )
        WHERE dietary_info IS NOT NULL AND array_length(dietary_info, 1) > 0;
    """
    )


def downgrade() -> None:
    """Remove subcategory and tags columns"""
    op.drop_index("idx_menu_items_tags", table_name="menu_items")
    op.drop_index("idx_menu_items_subcategory", table_name="menu_items")
    op.drop_column("menu_items", "tags")
    op.drop_column("menu_items", "subcategory")
