"""add_message_log_table

Revision ID: 25dc17ff6a26
Revises: 90164363b9b9
Create Date: 2025-11-13 21:16:32.243615

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '25dc17ff6a26'
down_revision = '90164363b9b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create message_log table for frequency limit enforcement
    # Note: Foreign keys to leads/customers are optional (nullable) since those tables may not exist yet
    op.create_table(
        'message_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contact', sa.String(255), nullable=False, index=True),  # Phone or email
        sa.Column('channel', sa.String(20), nullable=False, index=True),  # 'sms' or 'email'
        sa.Column('message_type', sa.String(50), nullable=False),  # 'welcome', 'nurture_touch_1', 'holiday', etc.
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('status', sa.String(20), nullable=False, default='sent'),  # 'sent', 'delivered', 'failed', 'bounced'
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    
    # Create composite index for frequency queries (contact + channel + sent_at)
    op.create_index('ix_message_log_frequency_check', 'message_log', ['contact', 'channel', 'sent_at'])


def downgrade() -> None:
    op.drop_index('ix_message_log_frequency_check', 'message_log')
    op.drop_table('message_log')