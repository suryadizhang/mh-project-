"""add_referral_tables

Revision ID: 90164363b9b9
Revises: ba857522523f
Create Date: 2025-11-13 21:16:00.183107

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '90164363b9b9'
down_revision = 'ba857522523f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create referrals table
    # Note: Foreign key to customers is optional (nullable) since customers table may not exist yet
    op.create_table(
        'referrals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('referral_code', sa.String(20), nullable=False, unique=True, index=True),
        sa.Column('total_referrals', sa.Integer, nullable=False, default=0),
        sa.Column('total_conversions', sa.Integer, nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create referral_rewards table
    op.create_table(
        'referral_rewards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('referral_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('referrals.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('reward_type', sa.String(100), nullable=False),  # 'Free Cheesecake', 'Free Edamame', etc.
        sa.Column('reward_description', sa.Text, nullable=False),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('redeemed', sa.Boolean, nullable=False, default=False),
        sa.Column('redeemed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create indexes
    op.create_index('ix_referral_rewards_redeemed', 'referral_rewards', ['redeemed'])


def downgrade() -> None:
    op.drop_index('ix_referral_rewards_redeemed', 'referral_rewards')
    op.drop_table('referral_rewards')
    op.drop_table('referrals')