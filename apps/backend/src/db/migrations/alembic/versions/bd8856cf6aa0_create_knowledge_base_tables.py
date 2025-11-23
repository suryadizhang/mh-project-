"""create_knowledge_base_tables

Revision ID: bd8856cf6aa0
Revises: 5034d1bfa5f0
Create Date: 2025-11-12 11:43:35.219378

Creates 7 tables for AI Knowledge Base & Adaptive Tone System:
1. business_rules - Policies, terms, guidelines
2. faq_items - Dynamic FAQs with tags
3. training_data - Hospitality examples for AI training
4. upsell_rules - Contextual upselling logic
5. seasonal_offers - Time-limited promotions
6. availability_calendar - Real-time booking slots
7. customer_tone_preferences - Learned tone history
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "bd8856cf6aa0"
down_revision = "5034d1bfa5f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create knowledge base tables with indexes"""

    # Create ENUM types (check existence manually)
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE rule_category AS ENUM ('policy', 'pricing', 'menu', 'travel', 'payment', 'cancellation', 'terms', 'guidelines');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE tone_type AS ENUM ('formal', 'casual', 'direct', 'warm', 'anxious');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE upsell_trigger_type AS ENUM ('guest_count', 'event_type', 'date', 'location', 'budget');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE offer_status AS ENUM ('draft', 'active', 'expired', 'scheduled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )

    # 1. business_rules table
    op.create_table(
        "business_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "category",
            postgresql.ENUM(
                "policy",
                "pricing",
                "menu",
                "travel",
                "payment",
                "cancellation",
                "terms",
                "guidelines",
                name="rule_category",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("rule_name", sa.String(200), nullable=False),
        sa.Column("rule_content", sa.Text, nullable=False),
        sa.Column("rule_summary", sa.String(500), nullable=True),  # Short version for quick lookup
        sa.Column("keywords", postgresql.ARRAY(sa.String), nullable=True),  # For search
        sa.Column("priority", sa.Integer, default=0),  # Higher = more important
        sa.Column("station_id", sa.String(36), nullable=True),  # Multi-location support
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer, default=1),  # For version history
        schema="public",
    )

    # 2. faq_items table
    op.create_table(
        "faq_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("short_answer", sa.String(500), nullable=True),  # Quick response version
        sa.Column("category", sa.String(100), nullable=False),  # pricing, menu, booking, etc.
        sa.Column("subcategory", sa.String(100), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("priority", sa.Integer, default=0),
        sa.Column("view_count", sa.Integer, default=0),  # Track popularity
        sa.Column("helpful_count", sa.Integer, default=0),  # User feedback
        sa.Column("station_id", sa.String(36), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
            nullable=False,
        ),
        schema="public",
    )

    # 3. training_data table
    op.create_table(
        "training_data",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "example_type", sa.String(100), nullable=False
        ),  # greeting, pricing, upsell, objection, etc.
        sa.Column(
            "tone",
            postgresql.ENUM(
                "formal", "casual", "direct", "warm", "anxious", name="tone_type", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("customer_message", sa.Text, nullable=False),
        sa.Column("ai_response", sa.Text, nullable=False),
        sa.Column("context", sa.JSON, nullable=True),  # Additional context like guest_count, date
        sa.Column("scenario", sa.String(200), nullable=True),  # Description of the scenario
        sa.Column("quality_score", sa.Integer, nullable=True),  # 1-5 rating
        sa.Column("used_count", sa.Integer, default=0),  # Track usage frequency
        sa.Column("station_id", sa.String(36), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
            nullable=False,
        ),
        schema="public",
    )

    # 4. upsell_rules table
    op.create_table(
        "upsell_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rule_name", sa.String(200), nullable=False),
        sa.Column(
            "trigger_type",
            postgresql.ENUM(
                "guest_count",
                "event_type",
                "date",
                "location",
                "budget",
                name="upsell_trigger_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "trigger_condition", sa.JSON, nullable=False
        ),  # e.g., {"guest_count": {"min": 10}}
        sa.Column("upsell_item", sa.String(200), nullable=False),  # e.g., "Filet Mignon"
        sa.Column("upsell_description", sa.Text, nullable=False),
        sa.Column("upsell_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("success_rate", sa.Numeric(5, 2), nullable=True),  # Track effectiveness (%)
        sa.Column("priority", sa.Integer, default=0),
        sa.Column("station_id", sa.String(36), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
            nullable=False,
        ),
        schema="public",
    )

    # 5. seasonal_offers table
    op.create_table(
        "seasonal_offers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("offer_name", sa.String(200), nullable=False),
        sa.Column("offer_description", sa.Text, nullable=False),
        sa.Column(
            "offer_type", sa.String(100), nullable=False
        ),  # discount, bundle, special_menu, etc.
        sa.Column("discount_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("discount_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "conditions", sa.JSON, nullable=True
        ),  # e.g., {"min_guests": 15, "days": ["friday", "saturday"]}
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft", "active", "expired", "scheduled", name="offer_status", create_type=False
            ),
            default="draft",
        ),
        sa.Column("usage_count", sa.Integer, default=0),
        sa.Column("station_id", sa.String(36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
            nullable=False,
        ),
        schema="public",
    )

    # 6. availability_calendar table
    op.create_table(
        "availability_calendar",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("time_slot", sa.Time, nullable=False),
        sa.Column("max_capacity", sa.Integer, nullable=False, default=50),  # Max guests per slot
        sa.Column("booked_capacity", sa.Integer, nullable=False, default=0),
        sa.Column("is_available", sa.Boolean, default=True),
        sa.Column("blackout_reason", sa.String(500), nullable=True),  # Holiday, maintenance, etc.
        sa.Column("station_id", sa.String(36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
            nullable=False,
        ),
        schema="public",
    )

    # 7. customer_tone_preferences table
    op.create_table(
        "customer_tone_preferences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_id", sa.String(36), nullable=False),
        sa.Column(
            "detected_tone",
            postgresql.ENUM(
                "formal", "casual", "direct", "warm", "anxious", name="tone_type", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=True),  # 0-100%
        sa.Column(
            "interaction_channel", sa.String(50), nullable=False
        ),  # email, sms, voice, instagram, etc.
        sa.Column("message_sample", sa.Text, nullable=True),  # Store sample for learning
        sa.Column("interaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        schema="public",
    )

    # ============================================
    # CREATE INDEXES FOR PERFORMANCE
    # ============================================

    # business_rules indexes
    op.create_index("idx_business_rules_category", "business_rules", ["category"], schema="public")
    op.create_index("idx_business_rules_active", "business_rules", ["is_active"], schema="public")
    op.create_index("idx_business_rules_station", "business_rules", ["station_id"], schema="public")
    op.create_index(
        "idx_business_rules_keywords",
        "business_rules",
        ["keywords"],
        postgresql_using="gin",
        schema="public",
    )
    op.create_index(
        "idx_business_rules_effective",
        "business_rules",
        ["effective_from", "effective_until"],
        schema="public",
    )

    # faq_items indexes
    op.create_index("idx_faq_category", "faq_items", ["category"], schema="public")
    op.create_index("idx_faq_active", "faq_items", ["is_active"], schema="public")
    op.create_index("idx_faq_station", "faq_items", ["station_id"], schema="public")
    op.create_index(
        "idx_faq_keywords", "faq_items", ["keywords"], postgresql_using="gin", schema="public"
    )
    op.create_index("idx_faq_tags", "faq_items", ["tags"], postgresql_using="gin", schema="public")
    op.create_index("idx_faq_priority", "faq_items", ["priority"], schema="public")

    # training_data indexes
    op.create_index("idx_training_tone", "training_data", ["tone"], schema="public")
    op.create_index("idx_training_type", "training_data", ["example_type"], schema="public")
    op.create_index("idx_training_active", "training_data", ["is_active"], schema="public")
    op.create_index("idx_training_station", "training_data", ["station_id"], schema="public")
    op.create_index("idx_training_quality", "training_data", ["quality_score"], schema="public")

    # upsell_rules indexes
    op.create_index("idx_upsell_trigger", "upsell_rules", ["trigger_type"], schema="public")
    op.create_index("idx_upsell_active", "upsell_rules", ["is_active"], schema="public")
    op.create_index("idx_upsell_station", "upsell_rules", ["station_id"], schema="public")
    op.create_index("idx_upsell_priority", "upsell_rules", ["priority"], schema="public")

    # seasonal_offers indexes
    op.create_index("idx_offers_status", "seasonal_offers", ["status"], schema="public")
    op.create_index(
        "idx_offers_dates", "seasonal_offers", ["valid_from", "valid_until"], schema="public"
    )
    op.create_index("idx_offers_station", "seasonal_offers", ["station_id"], schema="public")

    # availability_calendar indexes
    op.create_index("idx_calendar_date", "availability_calendar", ["date"], schema="public")
    op.create_index(
        "idx_calendar_datetime", "availability_calendar", ["date", "time_slot"], schema="public"
    )
    op.create_index(
        "idx_calendar_available", "availability_calendar", ["is_available"], schema="public"
    )
    op.create_index(
        "idx_calendar_station", "availability_calendar", ["station_id"], schema="public"
    )

    # customer_tone_preferences indexes
    op.create_index(
        "idx_tone_customer", "customer_tone_preferences", ["customer_id"], schema="public"
    )
    op.create_index(
        "idx_tone_detected", "customer_tone_preferences", ["detected_tone"], schema="public"
    )
    op.create_index(
        "idx_tone_channel", "customer_tone_preferences", ["interaction_channel"], schema="public"
    )
    op.create_index(
        "idx_tone_date", "customer_tone_preferences", ["interaction_date"], schema="public"
    )

    # Composite indexes for common queries
    op.create_index(
        "idx_business_rules_lookup",
        "business_rules",
        ["category", "is_active", "station_id"],
        schema="public",
    )
    op.create_index(
        "idx_faq_lookup", "faq_items", ["category", "is_active", "priority"], schema="public"
    )
    op.create_index(
        "idx_training_lookup",
        "training_data",
        ["tone", "example_type", "is_active"],
        schema="public",
    )
    op.create_index(
        "idx_tone_history",
        "customer_tone_preferences",
        ["customer_id", "interaction_date"],
        schema="public",
    )

    # Foreign key constraint (customer_tone_preferences -> customers)
    op.create_foreign_key(
        "fk_tone_customer",
        "customer_tone_preferences",
        "customers",
        ["customer_id"],
        ["id"],
        ondelete="CASCADE",
        source_schema="public",
        referent_schema="public",
    )


def downgrade() -> None:
    """Drop knowledge base tables and ENUM types"""

    # Drop tables (reverse order)
    op.drop_table("customer_tone_preferences", schema="public")
    op.drop_table("availability_calendar", schema="public")
    op.drop_table("seasonal_offers", schema="public")
    op.drop_table("upsell_rules", schema="public")
    op.drop_table("training_data", schema="public")
    op.drop_table("faq_items", schema="public")
    op.drop_table("business_rules", schema="public")

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS offer_status")
    op.execute("DROP TYPE IF EXISTS upsell_trigger_type")
    op.execute("DROP TYPE IF EXISTS tone_type")
    op.execute("DROP TYPE IF EXISTS rule_category")
