"""add_menu_items_table

Revision ID: 8ecb9a7d48f7
Revises: bd8856cf6aa0
Create Date: 2025-11-12 12:05:51.237899

Creates menu_items and pricing_tiers tables for dynamic menu management.
This allows AI to access real-time menu data and pricing.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '8ecb9a7d48f7'
down_revision = 'bd8856cf6aa0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create menu-related tables"""
    
    # Create ENUM types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE menu_category AS ENUM ('poultry', 'beef', 'seafood', 'specialty', 'sides', 'appetizers', 'desserts');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE pricing_tier_level AS ENUM ('basic', 'premium', 'luxury');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # 1. menu_items table
    op.create_table(
        'menu_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', postgresql.ENUM('poultry', 'beef', 'seafood', 'specialty', 'sides', 'appetizers', 'desserts', name='menu_category', create_type=False), nullable=False),
        sa.Column('base_price', sa.Numeric(10, 2), nullable=True),  # Price per person or unit
        sa.Column('is_premium', sa.Boolean, default=False),  # Premium protein (e.g., Filet Mignon, Lobster)
        sa.Column('is_available', sa.Boolean, default=True),
        sa.Column('dietary_info', postgresql.ARRAY(sa.String), nullable=True),  # ['vegetarian', 'gluten-free', etc.]
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('display_order', sa.Integer, default=0),  # For sorting
        sa.Column('station_id', sa.String(36), nullable=True),  # Multi-location support
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), onupdate=sa.text('NOW()'), nullable=False),
        schema='public'
    )
    
    # 2. pricing_tiers table
    op.create_table(
        'pricing_tiers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tier_level', postgresql.ENUM('basic', 'premium', 'luxury', name='pricing_tier_level', create_type=False), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),  # e.g., "Essential Hibachi"
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('price_per_person', sa.Numeric(10, 2), nullable=False),
        sa.Column('min_guests', sa.Integer, nullable=False),
        sa.Column('max_proteins', sa.Integer, default=2),  # Number of protein choices included
        sa.Column('includes_appetizers', sa.Boolean, default=False),
        sa.Column('includes_noodles', sa.Boolean, default=False),
        sa.Column('includes_extended_show', sa.Boolean, default=False),
        sa.Column('features', postgresql.ARRAY(sa.String), nullable=True),  # List of included features
        sa.Column('is_popular', sa.Boolean, default=False),  # Highlight this tier
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('display_order', sa.Integer, default=0),
        sa.Column('station_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), onupdate=sa.text('NOW()'), nullable=False),
        schema='public'
    )
    
    # Create indexes
    op.create_index('idx_menu_items_category', 'menu_items', ['category'], schema='public')
    op.create_index('idx_menu_items_available', 'menu_items', ['is_available'], schema='public')
    op.create_index('idx_menu_items_premium', 'menu_items', ['is_premium'], schema='public')
    op.create_index('idx_menu_items_station', 'menu_items', ['station_id'], schema='public')
    op.create_index('idx_menu_items_lookup', 'menu_items', ['category', 'is_available', 'display_order'], schema='public')
    
    op.create_index('idx_pricing_tiers_level', 'pricing_tiers', ['tier_level'], schema='public')
    op.create_index('idx_pricing_tiers_active', 'pricing_tiers', ['is_active'], schema='public')
    op.create_index('idx_pricing_tiers_station', 'pricing_tiers', ['station_id'], schema='public')
    op.create_index('idx_pricing_tiers_lookup', 'pricing_tiers', ['tier_level', 'is_active', 'display_order'], schema='public')


def downgrade() -> None:
    """Drop menu tables and ENUM types"""
    
    # Drop tables
    op.drop_table('pricing_tiers', schema='public')
    op.drop_table('menu_items', schema='public')
    
    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS pricing_tier_level')
    op.execute('DROP TYPE IF EXISTS menu_category')