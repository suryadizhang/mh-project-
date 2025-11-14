"""add_consent_records_table

Revision ID: ba857522523f
Revises: 8ecb9a7d48f7
Create Date: 2025-11-13 21:15:05.150278

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'ba857522523f'
down_revision = '8ecb9a7d48f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create consent_records table for TCPA/CAN-SPAM compliance
    # Note: Foreign keys to leads/customers are optional (nullable) since those tables may not exist yet
    op.create_table(
        'consent_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('ip_address', sa.String(45), nullable=True),  # IPv6 max length
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('consent_source', sa.String(100), nullable=False),  # 'website_quote', 'exit_intent', etc.
        sa.Column('consent_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('consent_text', sa.Text, nullable=True),  # Actual consent text shown to user
        sa.Column('sms_consent', sa.Boolean, nullable=False, default=False),
        sa.Column('email_consent', sa.Boolean, nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create indexes for common queries
    op.create_index('ix_consent_records_consent_source', 'consent_records', ['consent_source'])
    op.create_index('ix_consent_records_consent_timestamp', 'consent_records', ['consent_timestamp'])
    op.create_index('ix_consent_records_sms_consent', 'consent_records', ['sms_consent'])
    op.create_index('ix_consent_records_email_consent', 'consent_records', ['email_consent'])


def downgrade() -> None:
    op.drop_index('ix_consent_records_email_consent', 'consent_records')
    op.drop_index('ix_consent_records_sms_consent', 'consent_records')
    op.drop_index('ix_consent_records_consent_timestamp', 'consent_records')
    op.drop_index('ix_consent_records_consent_source', 'consent_records')
    op.drop_table('consent_records')