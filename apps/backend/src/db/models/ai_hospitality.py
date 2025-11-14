"""
AI Hospitality Training System - Database Models

SQLAlchemy ORM models for dynamic business knowledge and tone adaptation.
"""

from typing import Dict, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Date,
    Numeric,
    ARRAY,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

from models.base import Base


# ============================================================================
# Business Rules - Dynamic Policies
# ============================================================================


class BusinessRule(Base):
    """
    Dynamic business policies (cancellation, deposit, refund, etc.)
    Replaces hardcoded policies with database-driven content
    """

    __tablename__ = "business_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    value = Column(JSONB, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(String(100), nullable=True)

    __table_args__ = (
        Index("idx_business_rules_active", "rule_type", "is_active"),
        {"comment": "Dynamic business policies for AI (cancellation, deposit, refund, etc.)"},
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "rule_type": self.rule_type,
            "title": self.title,
            "content": self.content,
            "value": self.value,
            "is_active": self.is_active,
            "version": self.version,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


# ============================================================================
# FAQ Items - Searchable Knowledge Base
# ============================================================================


class FAQItem(Base):
    """
    FAQ database for AI to search and retrieve answers
    Tracks view count and helpfulness for analytics
    """

    __tablename__ = "faq_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    view_count = Column(Integer, nullable=False, default=0)
    helpful_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_faq_items_category_active", "category", "is_active"),
        {"comment": "FAQ database for AI to search and retrieve answers"},
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "category": self.category,
            "view_count": self.view_count,
            "helpful_count": self.helpful_count,
            "is_active": self.is_active,
        }


# ============================================================================
# Training Data - Tone-Matched Examples
# ============================================================================


class TrainingData(Base):
    """
    Training examples for tone-matched AI responses
    Used to train AI on hospitality communication patterns
    """

    __tablename__ = "training_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    customer_tone = Column(String(20), nullable=False, index=True)
    scenario = Column(String(100), nullable=False, index=True)
    tags = Column(ARRAY(String(50)), nullable=True)
    effectiveness_score = Column(Numeric(3, 2), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_used = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_training_data_tone_scenario", "customer_tone", "scenario", "is_active"),
        {"comment": "Training examples for tone-matched AI responses"},
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "customer_message": self.customer_message,
            "ai_response": self.ai_response,
            "customer_tone": self.customer_tone,
            "scenario": self.scenario,
            "tags": self.tags,
            "effectiveness_score": (
                float(self.effectiveness_score) if self.effectiveness_score else None
            ),
        }


# ============================================================================
# Upsell Rules - Contextual Suggestions
# ============================================================================


class UpsellRule(Base):
    """
    Rules for contextual upselling suggestions
    Tracks success rate for optimization
    """

    __tablename__ = "upsell_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trigger_condition = Column(String(255), nullable=False)
    upsell_item = Column(String(100), nullable=False)
    pitch_template = Column(Text, nullable=False)
    tone_adaptation = Column(JSONB, nullable=True)
    min_party_size = Column(Integer, nullable=True)
    max_party_size = Column(Integer, nullable=True)
    success_rate = Column(Numeric(5, 2), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = {"comment": "Rules for contextual upselling suggestions"}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "trigger_condition": self.trigger_condition,
            "upsell_item": self.upsell_item,
            "pitch_template": self.pitch_template,
            "tone_adaptation": self.tone_adaptation,
            "min_party_size": self.min_party_size,
            "max_party_size": self.max_party_size,
            "success_rate": float(self.success_rate) if self.success_rate else None,
            "is_active": self.is_active,
        }


# ============================================================================
# Seasonal Offers - Holiday Promotions
# ============================================================================


class SeasonalOffer(Base):
    """
    Seasonal offers and holiday promotions
    AI checks active offers and mentions them contextually
    """

    __tablename__ = "seasonal_offers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    discount_type = Column(String(50), nullable=False)
    discount_value = Column(Numeric(10, 2), nullable=False)
    valid_from = Column(Date, nullable=False, index=True)
    valid_to = Column(Date, nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_seasonal_offers_dates", "valid_from", "valid_to", "is_active"),
        {"comment": "Seasonal offers and holiday promotions"},
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "discount_type": self.discount_type,
            "discount_value": float(self.discount_value),
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "is_active": self.is_active,
        }


# ============================================================================
# Availability Calendar - Chef Availability
# ============================================================================


class AvailabilityCalendar(Base):
    """
    Chef availability tracking for AI booking suggestions
    Updated by booking system and manual blocks
    """

    __tablename__ = "availability_calendar"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    time_slot = Column(String(20), nullable=False, index=True)
    is_available = Column(Boolean, nullable=False, default=True)
    booking_id = Column(String(50), nullable=True)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_availability_date_time", "date", "time_slot", "is_available"),
        {"comment": "Chef availability tracking for AI booking suggestions"},
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "time_slot": self.time_slot,
            "is_available": self.is_available,
            "booking_id": self.booking_id,
            "reason": self.reason,
        }


# ============================================================================
# Customer Tone Preferences - Remember Communication Style
# ============================================================================


class CustomerTonePreference(Base):
    """
    Remember customer communication style for personalized responses
    Updated after each interaction to refine tone detection
    """

    __tablename__ = "customer_tone_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), nullable=False, unique=True, index=True)
    preferred_tone = Column(String(20), nullable=False)
    tone_confidence = Column(Numeric(3, 2), nullable=False)
    last_interaction = Column(DateTime, nullable=False)
    interaction_count = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = {"comment": "Remember customer communication style for personalized responses"}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "preferred_tone": self.preferred_tone,
            "tone_confidence": float(self.tone_confidence) if self.tone_confidence else None,
            "last_interaction": (
                self.last_interaction.isoformat() if self.last_interaction else None
            ),
            "interaction_count": self.interaction_count,
        }


# ============================================================================
# Week 5: Automated Customer Service Models
# ============================================================================


class AutomatedReminder(Base):
    """
    Track automated reminder sends (7-day, 4-day, 24-hour, post-event)
    Scheduler checks this table every hour
    """

    __tablename__ = "automated_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(String(50), nullable=False, index=True)
    reminder_type = Column(String(50), nullable=False, index=True)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    channel = Column(String(20), nullable=False)
    message_content = Column(Text, nullable=True)
    response_received = Column(Boolean, nullable=False, default=False)
    customer_response = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_automated_reminders_pending", "status", "scheduled_at"),
        {"comment": "Track automated reminder sends (7-day, 4-day, 24-hour, post-event)"},
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "reminder_type": self.reminder_type,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status,
            "channel": self.channel,
            "response_received": self.response_received,
        }


class Escalation(Base):
    """
    Human escalation queue for complex issues
    AI creates escalation records, humans resolve them
    """

    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(String(50), nullable=False, index=True)
    priority = Column(String(20), nullable=False, index=True)
    reason = Column(String(255), nullable=False)
    customer_request = Column(Text, nullable=True)
    action_required = Column(Text, nullable=False)
    deadline = Column(DateTime, nullable=True, index=True)
    assigned_to = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="open", index=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_escalations_open_priority", "status", "priority", "deadline"),
        {"comment": "Human escalation queue for complex issues"},
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "priority": self.priority,
            "reason": self.reason,
            "customer_request": self.customer_request,
            "action_required": self.action_required,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "assigned_to": self.assigned_to,
            "status": self.status,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class Feedback(Base):
    """
    Customer feedback and review tracking
    Integrated with smart review routing system
    """

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(String(50), nullable=False, unique=True, index=True)
    rating = Column(Integer, nullable=False)
    feedback_text = Column(Text, nullable=True)
    review_source = Column(String(50), nullable=True)
    escalated_to_human = Column(Boolean, nullable=False, default=False)
    human_followup_completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_feedback_rating", "rating", "escalated_to_human"),
        {"comment": "Customer feedback and review tracking"},
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "rating": self.rating,
            "feedback_text": self.feedback_text,
            "review_source": self.review_source,
            "escalated_to_human": self.escalated_to_human,
            "human_followup_completed": self.human_followup_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CustomerSentiment(Base):
    """
    Customer sentiment tracking and preferences
    Promoter scores, repeat customer detection, favorite proteins
    """

    __tablename__ = "customer_sentiment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), nullable=False, unique=True, index=True)
    sentiment_score = Column(Numeric(3, 2), nullable=False)
    last_rating = Column(Integer, nullable=True)
    total_bookings = Column(Integer, nullable=False, default=1)
    is_repeat_customer = Column(Boolean, nullable=False, default=False)
    is_referrer = Column(Boolean, nullable=False, default=False)
    preferred_proteins = Column(JSONB, nullable=True)
    favorite_addons = Column(JSONB, nullable=True)
    last_booking_date = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = {"comment": "Customer sentiment tracking and preferences"}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "sentiment_score": float(self.sentiment_score) if self.sentiment_score else None,
            "last_rating": self.last_rating,
            "total_bookings": self.total_bookings,
            "is_repeat_customer": self.is_repeat_customer,
            "is_referrer": self.is_referrer,
            "preferred_proteins": self.preferred_proteins,
            "favorite_addons": self.favorite_addons,
            "last_booking_date": (
                self.last_booking_date.isoformat() if self.last_booking_date else None
            ),
        }
