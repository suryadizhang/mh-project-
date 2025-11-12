"""Add AI Hospitality Training System tables

Revision ID: 010_ai_hospitality_training
Revises: 009_payment_notifications
Create Date: 2025-11-11 12:00:00.000000

This migration adds 7 new tables for the AI Hospitality Training System:
1. business_rules - Dynamic business policies (cancellation, deposit, refund)
2. faq_items - Searchable FAQ database
3. training_data - Tone-matched conversation examples
4. upsell_rules - Contextual upselling triggers
5. seasonal_offers - Holiday promotions and discounts
6. availability_calendar - Chef availability tracking
7. customer_tone_preferences - Remember customer communication style

Plus 4 tables for Automated Customer Service (Week 5):
8. automated_reminders - Scheduled reminder tracking
9. escalations - Human escalation queue
10. feedback - Customer ratings and reviews
11. customer_sentiment - Promoter scores and preferences
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = "010_ai_hospitality_training"
down_revision = "009_payment_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create AI Hospitality Training System tables"""

    # ========================================================================
    # Table 1: business_rules - Dynamic Business Policies
    # ========================================================================
    op.create_table(
        "business_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("rule_type", sa.String(50), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True, index=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column(
            "last_updated",
            sa.DateTime(),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.String(100), nullable=True),
        comment="Dynamic business policies for AI (cancellation, deposit, refund, etc.)",
    )

    # Create index for fast active policy queries
    op.create_index(
        "idx_business_rules_active", "business_rules", ["rule_type", "is_active"], unique=False
    )

    # ========================================================================
    # Table 2: faq_items - Searchable FAQ Database
    # ========================================================================
    op.create_table(
        "faq_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("view_count", sa.Integer(), nullable=False, default=0),
        sa.Column("helpful_count", sa.Integer(), nullable=False, default=0),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column(
            "last_updated",
            sa.DateTime(),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
            nullable=False,
        ),
        comment="FAQ database for AI to search and retrieve answers",
    )

    # Create index for category + active queries
    op.create_index(
        "idx_faq_items_category_active", "faq_items", ["category", "is_active"], unique=False
    )

    # ========================================================================
    # Table 3: training_data - Tone-Matched Conversation Examples
    # ========================================================================
    op.create_table(
        "training_data",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customer_message", sa.Text(), nullable=False),
        sa.Column("ai_response", sa.Text(), nullable=False),
        sa.Column("customer_tone", sa.String(20), nullable=False, index=True),
        sa.Column("scenario", sa.String(100), nullable=False, index=True),
        sa.Column("tags", postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column("effectiveness_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("last_used", sa.DateTime(), nullable=True),
        comment="Training examples for tone-matched AI responses",
    )

    # Create composite index for tone + scenario lookup
    op.create_index(
        "idx_training_data_tone_scenario",
        "training_data",
        ["customer_tone", "scenario", "is_active"],
        unique=False,
    )

    # ========================================================================
    # Table 4: upsell_rules - Contextual Upselling Triggers
    # ========================================================================
    op.create_table(
        "upsell_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("trigger_condition", sa.String(255), nullable=False),
        sa.Column("upsell_item", sa.String(100), nullable=False),
        sa.Column("pitch_template", sa.Text(), nullable=False),
        sa.Column("tone_adaptation", postgresql.JSONB(), nullable=True),
        sa.Column("min_party_size", sa.Integer(), nullable=True),
        sa.Column("max_party_size", sa.Integer(), nullable=True),
        sa.Column("success_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column(
            "last_updated",
            sa.DateTime(),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
            nullable=False,
        ),
        comment="Rules for contextual upselling suggestions",
    )

    # ========================================================================
    # Table 5: seasonal_offers - Holiday Promotions
    # ========================================================================
    op.create_table(
        "seasonal_offers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("discount_type", sa.String(50), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False, index=True),
        sa.Column("valid_to", sa.Date(), nullable=False, index=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        comment="Seasonal offers and holiday promotions",
    )

    # Create index for date range queries
    op.create_index(
        "idx_seasonal_offers_dates",
        "seasonal_offers",
        ["valid_from", "valid_to", "is_active"],
        unique=False,
    )

    # ========================================================================
    # Table 6: availability_calendar - Chef Availability
    # ========================================================================
    op.create_table(
        "availability_calendar",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("date", sa.Date(), nullable=False, index=True),
        sa.Column("time_slot", sa.String(20), nullable=False, index=True),
        sa.Column("is_available", sa.Boolean(), nullable=False, default=True),
        sa.Column("booking_id", sa.String(50), nullable=True),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column(
            "last_updated",
            sa.DateTime(),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
            nullable=False,
        ),
        comment="Chef availability tracking for AI booking suggestions",
    )

    # Create composite index for date + time lookups
    op.create_index(
        "idx_availability_date_time",
        "availability_calendar",
        ["date", "time_slot", "is_available"],
        unique=False,
    )

    # ========================================================================
    # Table 7: customer_tone_preferences - Remember Communication Style
    # ========================================================================
    op.create_table(
        "customer_tone_preferences",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("preferred_tone", sa.String(20), nullable=False),
        sa.Column("tone_confidence", sa.Numeric(3, 2), nullable=False),
        sa.Column("last_interaction", sa.DateTime(), nullable=False),
        sa.Column("interaction_count", sa.Integer(), nullable=False, default=1),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column(
            "last_updated",
            sa.DateTime(),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
            nullable=False,
        ),
        comment="Remember customer communication style for personalized responses",
    )

    # ========================================================================
    # Week 5: Automated Customer Service Tables
    # ========================================================================

    # Table 8: automated_reminders - Scheduled Reminder Tracking
    op.create_table(
        "automated_reminders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("booking_id", sa.String(50), nullable=False, index=True),
        sa.Column("reminder_type", sa.String(50), nullable=False, index=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="pending", index=True),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("message_content", sa.Text(), nullable=True),
        sa.Column("response_received", sa.Boolean(), nullable=False, default=False),
        sa.Column("customer_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        comment="Track automated reminder sends (7-day, 4-day, 24-hour, post-event)",
    )

    # Create index for pending reminders query
    op.create_index(
        "idx_automated_reminders_pending",
        "automated_reminders",
        ["status", "scheduled_at"],
        unique=False,
    )

    # Table 9: escalations - Human Escalation Queue
    op.create_table(
        "escalations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("booking_id", sa.String(50), nullable=False, index=True),
        sa.Column("priority", sa.String(20), nullable=False, index=True),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("customer_request", sa.Text(), nullable=True),
        sa.Column("action_required", sa.Text(), nullable=False),
        sa.Column("deadline", sa.DateTime(), nullable=True, index=True),
        sa.Column("assigned_to", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="open", index=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        comment="Human escalation queue for complex issues",
    )

    # Create composite index for open escalations by priority
    op.create_index(
        "idx_escalations_open_priority",
        "escalations",
        ["status", "priority", "deadline"],
        unique=False,
    )

    # Table 10: feedback - Customer Ratings and Reviews
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("booking_id", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("review_source", sa.String(50), nullable=True),
        sa.Column("escalated_to_human", sa.Boolean(), nullable=False, default=False),
        sa.Column("human_followup_completed", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column(
            "last_updated",
            sa.DateTime(),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
            nullable=False,
        ),
        comment="Customer feedback and review tracking",
    )

    # Create index for rating-based queries
    op.create_index(
        "idx_feedback_rating", "feedback", ["rating", "escalated_to_human"], unique=False
    )

    # Table 11: customer_sentiment - Promoter Scores and Preferences
    op.create_table(
        "customer_sentiment",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("sentiment_score", sa.Numeric(3, 2), nullable=False),
        sa.Column("last_rating", sa.Integer(), nullable=True),
        sa.Column("total_bookings", sa.Integer(), nullable=False, default=1),
        sa.Column("is_repeat_customer", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_referrer", sa.Boolean(), nullable=False, default=False),
        sa.Column("preferred_proteins", postgresql.JSONB(), nullable=True),
        sa.Column("favorite_addons", postgresql.JSONB(), nullable=True),
        sa.Column("last_booking_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column(
            "last_updated",
            sa.DateTime(),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
            nullable=False,
        ),
        comment="Customer sentiment tracking and preferences",
    )

    print("✅ Created 11 tables for AI Hospitality Training System + Automated Customer Service")


def downgrade() -> None:
    """Drop all AI Hospitality Training System tables"""

    op.drop_table("customer_sentiment")
    op.drop_table("feedback")
    op.drop_table("escalations")
    op.drop_table("automated_reminders")
    op.drop_table("customer_tone_preferences")
    op.drop_table("availability_calendar")
    op.drop_table("seasonal_offers")
    op.drop_table("upsell_rules")
    op.drop_table("training_data")
    op.drop_table("faq_items")
    op.drop_table("business_rules")

    print("✅ Dropped all AI Hospitality Training System tables")
