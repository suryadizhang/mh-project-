"""add_crm_contacts_table

Revision ID: 55f201d7ea25
Revises: 2c5f01a6bf8c
Create Date: 2025-11-25 10:53:39.388123

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision = '55f201d7ea25'
down_revision = '2c5f01a6bf8c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create crm_contacts table for unified inbox contact management.
    This table supports the email inbox feature and future CRM functionality.
    """
    op.create_table(
        'crm_contacts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),

        # Basic information
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone_number', sa.String(20), nullable=True),

        # Social media handles
        sa.Column('facebook_handle', sa.String(100), nullable=True),
        sa.Column('instagram_handle', sa.String(100), nullable=True),
        sa.Column('twitter_handle', sa.String(100), nullable=True),

        # Contact metadata
        sa.Column('contact_source', sa.String(50), nullable=True),
        sa.Column('contact_notes', sa.Text, nullable=True),
        sa.Column('contact_metadata', JSON, nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean, nullable=False, server_default='false'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_contacted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for performance
    op.create_index('idx_crm_contacts_email', 'crm_contacts', ['email'])
    op.create_index('idx_crm_contacts_phone', 'crm_contacts', ['phone_number'])
    op.create_index('idx_crm_contacts_active', 'crm_contacts', ['is_active'])
    op.create_index('idx_crm_contacts_created', 'crm_contacts', ['created_at'])


def downgrade() -> None:
    """Drop crm_contacts table and indexes"""
    op.drop_index('idx_crm_contacts_created', 'crm_contacts')
    op.drop_index('idx_crm_contacts_active', 'crm_contacts')
    op.drop_index('idx_crm_contacts_phone', 'crm_contacts')
    op.drop_index('idx_crm_contacts_email', 'crm_contacts')
    op.drop_table('crm_contacts')
