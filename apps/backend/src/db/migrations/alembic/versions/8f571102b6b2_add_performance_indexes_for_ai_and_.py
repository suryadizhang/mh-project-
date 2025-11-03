"""Add performance indexes for AI and reviews

Revision ID: 8f571102b6b2
Revises: 198b329960a9
Create Date: 2025-10-31 01:44:56.148668

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f571102b6b2'
down_revision = '198b329960a9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add performance indexes to optimize frequent queries
    - Customer reviews: status, created_at, rating
    """
    
    # Use raw SQL for better error handling
    connection = op.get_bind()
    
    # === Customer Review Blog Posts Indexes ===
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_review_blog_status ON customer_review_blog_posts(status);",
        "CREATE INDEX IF NOT EXISTS idx_review_blog_created_at ON customer_review_blog_posts(created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_review_blog_rating ON customer_review_blog_posts(rating);",
        "CREATE INDEX IF NOT EXISTS idx_review_blog_status_created ON customer_review_blog_posts(status, created_at DESC);",
        
        # Review approval log indexes
        "CREATE INDEX IF NOT EXISTS idx_approval_log_review_id ON review_approval_log(review_id);",
        "CREATE INDEX IF NOT EXISTS idx_approval_log_admin_id ON review_approval_log(admin_id);",
        "CREATE INDEX IF NOT EXISTS idx_approval_log_created_at ON review_approval_log(created_at DESC);",
    ]
    
    for index_sql in indexes:
        try:
            connection.execute(sa.text(index_sql))
        except Exception as e:
            print(f"Warning: Could not create index: {e}")


def downgrade() -> None:
    """Remove performance indexes"""
    connection = op.get_bind()
    
    indexes = [
        "DROP INDEX IF EXISTS idx_review_blog_status;",
        "DROP INDEX IF EXISTS idx_review_blog_created_at;",
        "DROP INDEX IF EXISTS idx_review_blog_rating;",
        "DROP INDEX IF EXISTS idx_review_blog_status_created;",
        "DROP INDEX IF EXISTS idx_approval_log_review_id;",
        "DROP INDEX IF EXISTS idx_approval_log_admin_id;",
        "DROP INDEX IF EXISTS idx_approval_log_created_at;",
    ]
    
    for index_sql in indexes:
        try:
            connection.execute(sa.text(index_sql))
        except Exception as e:
            print(f"Warning: Could not drop index: {e}")