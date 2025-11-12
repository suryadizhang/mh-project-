"""
SQLAlchemy models for AI Hospitality Training System

Week 1 implementation - 11 tables for:
- Business rules (pricing, policies, etc.)
- FAQ items
- Training data (tone-matched examples)
- Upsell rules
- Seasonal offers
- Customer tone preferences
- Knowledge cache
- Automated reminders
- Escalations
- Feedback
- Customer sentiment tracking
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from models.base import Base


class BusinessRule(Base):
    """Dynamic business policies and rules"""

    __tablename__ = "business_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_type = Column(
        String(50), nullable=False, index=True
    )  # pricing, deposit, cancellation, travel, etc.
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    value = Column(
        JSONB, nullable=True
    )  # Structured data (e.g., {"adult_base": 55, "currency": "USD"})
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    updated_by = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<BusinessRule(id={self.id}, type={self.rule_type}, title={self.title})>"


class FAQItem(Base):
    """Searchable FAQ database"""

    __tablename__ = "faq_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    tags = Column(JSONB, nullable=True)  # Array of searchable tags
    source_urls = Column(JSONB, nullable=True)  # Array of relevant URLs
    view_count = Column(Integer, nullable=False, default=0)
    helpful_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<FAQItem(id={self.id}, question={self.question[:50]}...)>"


class TrainingData(Base):
    """Tone-matched conversation examples for AI training"""

    __tablename__ = "training_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_message = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    customer_tone = Column(
        String(20), nullable=False, index=True
    )  # formal, casual, direct, warm, anxious
    agent_type = Column(
        String(50), nullable=False, index=True
    )  # lead_nurturing, customer_care, operations, knowledge
    booking_context = Column(JSONB, nullable=True)  # Event details, guest count, etc.
    tags = Column(JSONB, nullable=True)  # Searchable tags
    quality_score = Column(Float, nullable=True)  # AI-generated quality score
    is_approved = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<TrainingData(id={self.id}, tone={self.customer_tone}, agent={self.agent_type})>"


class UpsellRule(Base):
    """Contextual upselling triggers"""

    __tablename__ = "upsell_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trigger_context = Column(
        String(255), nullable=False
    )  # guest_count >= 20, event_type == 'corporate', etc.
    upsell_item = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    price_modifier = Column(Float, nullable=False)  # +5.00, +15.00, etc.
    suggested_tone = Column(String(20), nullable=True)  # Best tone for this upsell
    priority = Column(Integer, nullable=False, default=1, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<UpsellRule(id={self.id}, item={self.upsell_item}, price=+{self.price_modifier})>"


class SeasonalOffer(Base):
    """Holiday promotions and seasonal discounts"""

    __tablename__ = "seasonal_offers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    discount_type = Column(String(50), nullable=False)  # percentage, fixed, upgrade, free_item
    discount_value = Column(Float, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False, index=True)
    valid_to = Column(DateTime(timezone=True), nullable=False, index=True)
    applicable_to = Column(
        String(255), nullable=True
    )  # Conditions: "parties >= 30 guests", "wedding events", etc.
    usage_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<SeasonalOffer(id={self.id}, title={self.title})>"


class CustomerTonePreference(Base):
    """Remember customer communication style preferences"""

    __tablename__ = "customer_tone_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, nullable=True)  # Link to customers table
    customer_email = Column(String(255), nullable=True, index=True)
    customer_phone = Column(String(20), nullable=True, index=True)
    detected_tone = Column(String(20), nullable=False)  # formal, casual, direct, warm, anxious
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    interaction_count = Column(Integer, nullable=False, default=1)
    last_interaction = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<CustomerTonePreference(id={self.id}, tone={self.detected_tone}, confidence={self.confidence_score})>"


class KnowledgeCache(Base):
    """Cached knowledge base queries for fast retrieval"""

    __tablename__ = "knowledge_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_hash = Column(String(64), nullable=False, unique=True, index=True)  # MD5 hash of query
    query_text = Column(Text, nullable=False)
    cached_response = Column(Text, nullable=False)
    source_tables = Column(JSONB, nullable=True)  # Which tables were queried
    hit_count = Column(Integer, nullable=False, default=0)
    is_valid = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_accessed = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    expires_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<KnowledgeCache(id={self.id}, hash={self.query_hash}, hits={self.hit_count})>"


# =============================================================================
# Week 5: Automated Customer Service Tables
# =============================================================================


class AutomatedReminder(Base):
    """Scheduled reminder tracking (7-day, 4-day, 24-hour, post-event)"""

    __tablename__ = "automated_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, nullable=False, index=True)
    reminder_type = Column(
        String(50), nullable=False, index=True
    )  # 7_day, 4_day, 24_hour, post_event
    scheduled_for = Column(DateTime(timezone=True), nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    channel = Column(String(20), nullable=False)  # sms, email, whatsapp
    message_content = Column(Text, nullable=False)
    customer_tone = Column(String(20), nullable=True)  # Adapt message to customer's preferred tone
    status = Column(
        String(20), nullable=False, default="pending", index=True
    )  # pending, sent, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AutomatedReminder(id={self.id}, booking={self.booking_id}, type={self.reminder_type}, status={self.status})>"


class Escalation(Base):
    """Human escalation queue for complex issues"""

    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, nullable=True, index=True)
    customer_id = Column(Integer, nullable=True, index=True)
    trigger_reason = Column(
        String(100), nullable=False, index=True
    )  # no_menu_by_deadline, changes_within_24hrs, etc.
    priority = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    description = Column(Text, nullable=False)
    customer_message = Column(Text, nullable=True)
    ai_analysis = Column(JSONB, nullable=True)  # AI's assessment of the issue
    assigned_to = Column(String(100), nullable=True)
    status = Column(
        String(20), nullable=False, default="open", index=True
    )  # open, in_progress, resolved, closed
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Escalation(id={self.id}, reason={self.trigger_reason}, priority={self.priority}, status={self.status})>"


class Feedback(Base):
    """Customer ratings and reviews (internal + external routing)"""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, nullable=False, index=True)
    customer_id = Column(Integer, nullable=True, index=True)
    rating = Column(Integer, nullable=False, index=True)  # 1-5 stars
    review_text = Column(Text, nullable=True)
    review_platform = Column(String(20), nullable=False)  # internal, google, yelp
    platform_url = Column(String(500), nullable=True)  # URL where review was posted
    sentiment = Column(String(20), nullable=False, index=True)  # positive, neutral, negative
    ai_sentiment_score = Column(Float, nullable=True)  # 0.0 to 1.0
    requires_follow_up = Column(Boolean, nullable=False, default=False, index=True)
    follow_up_notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self):
        return f"<Feedback(id={self.id}, booking={self.booking_id}, rating={self.rating}, platform={self.review_platform})>"


class CustomerSentiment(Base):
    """Promoter scores and customer preferences tracking"""

    __tablename__ = "customer_sentiment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, nullable=False, unique=True, index=True)
    customer_email = Column(String(255), nullable=True)
    nps_score = Column(Integer, nullable=True)  # Net Promoter Score (0-10)
    sentiment_category = Column(
        String(20), nullable=True, index=True
    )  # promoter, passive, detractor
    lifetime_bookings = Column(Integer, nullable=False, default=0)
    total_spend = Column(Float, nullable=False, default=0.0)
    favorite_proteins = Column(JSONB, nullable=True)  # Array of preferred proteins
    dietary_preferences = Column(JSONB, nullable=True)  # Array of dietary restrictions
    preferred_contact_method = Column(String(20), nullable=True)  # sms, email, whatsapp
    preferred_tone = Column(String(20), nullable=True)  # formal, casual, direct, warm, anxious
    last_booking_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<CustomerSentiment(id={self.id}, customer={self.customer_id}, nps={self.nps_score}, category={self.sentiment_category})>"
