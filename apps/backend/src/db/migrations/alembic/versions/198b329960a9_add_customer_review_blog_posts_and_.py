"""Add customer review blog posts and approval logs tables MANUAL

Revision ID: 198b329960a9
Revises: 3907a0a8e118
Create Date: 2025-10-31 01:00:39.623468

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '198b329960a9'
down_revision = '3907a0a8e118'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create customer_review_blog_posts table
    # NOTE: Removed foreign key constraints due to type mismatch (customers.id is VARCHAR, not INTEGER)
    op.create_table(
        'customer_review_blog_posts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=True),  # Made nullable due to FK issue
        sa.Column('booking_id', sa.Integer(), nullable=True),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('customer_email', sa.String(length=255), nullable=True),
        sa.Column('customer_phone', sa.String(length=50), nullable=True),
        sa.Column('show_initials_only', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('images', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('reviewed_on_google', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('reviewed_on_yelp', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('google_review_link', sa.Text(), nullable=True),
        sa.Column('yelp_review_link', sa.Text(), nullable=True),
        sa.Column('slug', sa.String(length=255), nullable=True),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('likes_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('helpful_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default='false'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range'),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name='valid_status'),
        # ForeignKey constraints removed due to schema type mismatch
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_customer_review_blog_posts_customer_id', 'customer_review_blog_posts', ['customer_id'])
    op.create_index('ix_customer_review_blog_posts_status', 'customer_review_blog_posts', ['status'])
    op.create_index('ix_customer_review_blog_posts_slug', 'customer_review_blog_posts', ['slug'], unique=True)
    
    # Create review_approval_log table
    op.create_table(
        'review_approval_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('review_id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default='false'),
        sa.CheckConstraint("action IN ('pending_review', 'approved', 'rejected')", name='valid_action'),
        sa.ForeignKeyConstraint(['review_id'], ['customer_review_blog_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_review_approval_log_review_id', 'review_approval_log', ['review_id'])
    op.create_index('ix_review_approval_log_admin_id', 'review_approval_log', ['admin_id'])
    op.create_index('ix_review_approval_log_created_at', 'review_approval_log', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order (to handle foreign keys)
    op.drop_index('ix_review_approval_log_created_at', table_name='review_approval_log')
    op.drop_index('ix_review_approval_log_admin_id', table_name='review_approval_log')
    op.drop_index('ix_review_approval_log_review_id', table_name='review_approval_log')
    op.drop_table('review_approval_log')
    
    op.drop_index('ix_customer_review_blog_posts_slug', table_name='customer_review_blog_posts')
    op.drop_index('ix_customer_review_blog_posts_status', table_name='customer_review_blog_posts')
    op.drop_index('ix_customer_review_blog_posts_customer_id', table_name='customer_review_blog_posts')
    op.drop_table('customer_review_blog_posts')