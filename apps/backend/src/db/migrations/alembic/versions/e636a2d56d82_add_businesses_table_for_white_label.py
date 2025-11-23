"""add_businesses_table_for_white_label

Revision ID: e636a2d56d82
Revises: 8f571102b6b2
Create Date: 2025-11-04 19:25:06.145990

Purpose: Enable white-label multi-tenancy for future SaaS model.
Currently runs as "My Hibachi Chef" but prepared for multiple brands.

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = "e636a2d56d82"
down_revision = "8f571102b6b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create businesses table for multi-tenant support
    op.create_table(
        "businesses",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("name", sa.String(255), nullable=False),  # "My Hibachi Chef"
        sa.Column("slug", sa.String(100), unique=True, nullable=False),  # "my-hibachi-chef"
        sa.Column("domain", sa.String(255), unique=True, nullable=True),  # "myhibachichef.com"
        # Branding
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("primary_color", sa.String(7), nullable=True, server_default="#FF6B6B"),
        sa.Column("secondary_color", sa.String(7), nullable=True, server_default="#4ECDC4"),
        # Contact info
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        # Business settings
        sa.Column("timezone", sa.String(50), nullable=False, server_default="America/Los_Angeles"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("settings", JSONB, nullable=False, server_default="{}"),
        # Subscription (for white-label pricing model)
        sa.Column("subscription_tier", sa.String(50), nullable=False, server_default="self_hosted"),
        sa.Column("subscription_status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("monthly_fee", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        # Metadata
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Insert My Hibachi Chef as the first business
    op.execute(
        """
        INSERT INTO businesses (name, slug, domain, phone, email, subscription_tier, settings)
        VALUES (
            'My Hibachi Chef',
            'my-hibachi-chef',
            'myhibachichef.com',
            '(916) 740-8768',
            'contact@myhibachichef.com',
            'self_hosted',
            '{"pricing": {"base_adult": 55, "base_child": 30, "party_minimum": 550}}'::jsonb
        )
    """
    )

    # Add business_id to existing tables (with correct schemas)
    tables_with_schemas = [
        ("users", "identity"),
        ("bookings", "bookings"),
        ("leads", "lead"),
        ("reviews", "feedback"),
        ("newsletter_subscribers", "newsletter"),
    ]

    conn = op.get_bind()
    
    for table, schema in tables_with_schemas:
        # Check if table exists before adding column
        table_exists = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = '{schema}' 
                AND table_name = '{table}'
            )
        """)).scalar()
        
        if not table_exists:
            print(f"[SKIP] {schema}.{table} does not exist")
            continue
            
        # Check if business_id column already exists
        column_exists = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{schema}'
                AND table_name = '{table}'
                AND column_name = 'business_id'
            )
        """)).scalar()
        
        if column_exists:
            print(f"[SKIP] {schema}.{table}.business_id already exists")
            continue
        
        # Add business_id column (nullable first)
        op.add_column(table, sa.Column("business_id", UUID(as_uuid=True), nullable=True), schema=schema)

        # Set all existing records to My Hibachi Chef
        op.execute(
            f"""
            UPDATE {schema}.{table}
            SET business_id = (SELECT id FROM businesses WHERE slug = 'my-hibachi-chef')
        """
        )

        # Make business_id NOT NULL
        op.alter_column(table, "business_id", nullable=False, schema=schema)

        # Add foreign key
        op.create_foreign_key(
            f"fk_{table}_business", 
            table, 
            "businesses", 
            ["business_id"], 
            ["id"], 
            source_schema=schema,
            ondelete="CASCADE"
        )
        
        print(f"✅ Added business_id to {schema}.{table}")

        # Add index for performance
        op.create_index(f"idx_{table}_business_id", table, ["business_id"], schema=schema)


def downgrade() -> None:
    # Remove business_id from tables (with correct schemas)
    tables_with_schemas = [
        ("users", "identity"),
        ("bookings", "bookings"),
        ("leads", "lead"),
        ("reviews", "feedback"),
        ("newsletter_subscribers", "newsletter"),
    ]

    for table, schema in tables_with_schemas:
        try:
            op.drop_index(f"idx_{table}_business_id", table_name=table, schema=schema)
            op.drop_constraint(f"fk_{table}_business", table, schema=schema, type_="foreignkey")
            op.drop_column(table, "business_id", schema=schema)
        except Exception as e:
            print(f"[SKIP] Could not remove business_id from {schema}.{table}: {e}")

    # Drop businesses table
    op.drop_table("businesses")
