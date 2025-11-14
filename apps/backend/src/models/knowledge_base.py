"""
Knowledge Base Models for AI System

7 tables supporting:
- Dynamic business rules and policies
- FAQ management
- AI training data
- Contextual upselling
- Seasonal promotions
- Availability tracking
- Customer tone preferences

Created: 2025-11-12
"""
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, Dict, List
from enum import Enum

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    Date,
    Time,
    Numeric,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import ARRAY, ENUM as PgEnum
from sqlalchemy.orm import relationship

from models.base import Base


# ============================================
# ENUM TYPES
# ============================================

class RuleCategory(str, Enum):
    """Business rule categories"""
    POLICY = "policy"
    PRICING = "pricing"
    MENU = "menu"
    TRAVEL = "travel"
    PAYMENT = "payment"
    CANCELLATION = "cancellation"
    TERMS = "terms"
    GUIDELINES = "guidelines"


class ToneType(str, Enum):
    """Customer communication tone types"""
    FORMAL = "formal"
    CASUAL = "casual"
    DIRECT = "direct"
    WARM = "warm"
    ANXIOUS = "anxious"


class UpsellTriggerType(str, Enum):
    """Upsell rule trigger types"""
    GUEST_COUNT = "guest_count"
    EVENT_TYPE = "event_type"
    DATE = "date"
    LOCATION = "location"
    BUDGET = "budget"


class OfferStatus(str, Enum):
    """Seasonal offer statuses"""
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    SCHEDULED = "scheduled"


class SyncSourceType(str, Enum):
    """Knowledge sync source types"""
    MENU = "menu"
    FAQS = "faqs"
    TERMS = "terms"


class SyncType(str, Enum):
    """Knowledge sync operation types"""
    AUTO = "auto"
    MANUAL = "manual"
    FORCE = "force"


class SyncStatus(str, Enum):
    """Knowledge sync operation statuses"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class MenuCategory(str, Enum):
    """Menu item categories"""
    POULTRY = "poultry"
    BEEF = "beef"
    SEAFOOD = "seafood"
    SPECIALTY = "specialty"
    SIDES = "sides"
    APPETIZERS = "appetizers"
    DESSERTS = "desserts"


class PricingTierLevel(str, Enum):
    """Pricing tier levels"""
    BASIC = "basic"
    PREMIUM = "premium"
    LUXURY = "luxury"


# ============================================
# MODELS
# ============================================

class BusinessRule(Base):
    """
    Business rules, policies, and guidelines
    
    Examples:
    - Cancellation policy
    - Travel fee structure
    - Menu customization rules
    - Payment terms
    """
    __tablename__ = "business_rules"
    __table_args__ = (
        Index('idx_business_rules_category', 'category'),
        Index('idx_business_rules_active', 'is_active'),
        Index('idx_business_rules_station', 'station_id'),
        Index('idx_business_rules_keywords', 'keywords', postgresql_using='gin'),
        Index('idx_business_rules_effective', 'effective_from', 'effective_until'),
        Index('idx_business_rules_lookup', 'category', 'is_active', 'station_id'),
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = Column(String(36), primary_key=True)
    category = Column(
        PgEnum(RuleCategory, name='rule_category', create_type=False),
        nullable=False
    )
    rule_name = Column(String(200), nullable=False)
    rule_content = Column(Text, nullable=False)
    rule_summary = Column(String(500), nullable=True)
    keywords = Column(ARRAY(String), nullable=True)
    priority = Column(Integer, default=0)
    station_id = Column(String(36), nullable=True)
    is_active = Column(Boolean, default=True)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "category": self.category.value if isinstance(self.category, Enum) else self.category,
            "rule_name": self.rule_name,
            "rule_content": self.rule_content,
            "rule_summary": self.rule_summary,
            "keywords": self.keywords,
            "priority": self.priority,
            "station_id": self.station_id,
            "is_active": self.is_active,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "effective_until": self.effective_until.isoformat() if self.effective_until else None,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class FAQItem(Base):
    """
    Frequently Asked Questions
    
    Dynamic FAQ system with search, tagging, and popularity tracking
    """
    __tablename__ = "faq_items"
    __table_args__ = (
        Index('idx_faq_category', 'category'),
        Index('idx_faq_active', 'is_active'),
        Index('idx_faq_station', 'station_id'),
        Index('idx_faq_keywords', 'keywords', postgresql_using='gin'),
        Index('idx_faq_tags', 'tags', postgresql_using='gin'),
        Index('idx_faq_priority', 'priority'),
        Index('idx_faq_lookup', 'category', 'is_active', 'priority'),
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = Column(String(36), primary_key=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    short_answer = Column(String(500), nullable=True)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=True)
    keywords = Column(ARRAY(String), nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    priority = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    station_id = Column(String(36), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "short_answer": self.short_answer,
            "category": self.category,
            "subcategory": self.subcategory,
            "keywords": self.keywords,
            "tags": self.tags,
            "priority": self.priority,
            "view_count": self.view_count,
            "helpful_count": self.helpful_count,
            "station_id": self.station_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TrainingData(Base):
    """
    AI training examples for hospitality scenarios
    
    Stores example conversations with different tones and contexts
    """
    __tablename__ = "training_data"
    __table_args__ = (
        Index('idx_training_tone', 'tone'),
        Index('idx_training_type', 'example_type'),
        Index('idx_training_active', 'is_active'),
        Index('idx_training_station', 'station_id'),
        Index('idx_training_quality', 'quality_score'),
        Index('idx_training_lookup', 'tone', 'example_type', 'is_active'),
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = Column(String(36), primary_key=True)
    example_type = Column(String(100), nullable=False)
    tone = Column(
        PgEnum(ToneType, name='tone_type', create_type=False),
        nullable=False
    )
    customer_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    scenario = Column(String(200), nullable=True)
    quality_score = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0)
    station_id = Column(String(36), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "example_type": self.example_type,
            "tone": self.tone.value if isinstance(self.tone, Enum) else self.tone,
            "customer_message": self.customer_message,
            "ai_response": self.ai_response,
            "context": self.context,
            "scenario": self.scenario,
            "quality_score": self.quality_score,
            "used_count": self.used_count,
            "station_id": self.station_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UpsellRule(Base):
    """
    Contextual upselling rules
    
    Defines when and how to suggest premium items/services
    """
    __tablename__ = "upsell_rules"
    __table_args__ = (
        Index('idx_upsell_trigger', 'trigger_type'),
        Index('idx_upsell_active', 'is_active'),
        Index('idx_upsell_station', 'station_id'),
        Index('idx_upsell_priority', 'priority'),
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = Column(String(36), primary_key=True)
    rule_name = Column(String(200), nullable=False)
    trigger_type = Column(
        PgEnum(UpsellTriggerType, name='upsell_trigger_type', create_type=False),
        nullable=False
    )
    trigger_condition = Column(JSON, nullable=False)
    upsell_item = Column(String(200), nullable=False)
    upsell_description = Column(Text, nullable=False)
    upsell_price = Column(Numeric(10, 2), nullable=True)
    success_rate = Column(Numeric(5, 2), nullable=True)
    priority = Column(Integer, default=0)
    station_id = Column(String(36), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "trigger_type": self.trigger_type.value if isinstance(self.trigger_type, Enum) else self.trigger_type,
            "trigger_condition": self.trigger_condition,
            "upsell_item": self.upsell_item,
            "upsell_description": self.upsell_description,
            "upsell_price": str(self.upsell_price) if self.upsell_price else None,
            "success_rate": str(self.success_rate) if self.success_rate else None,
            "priority": self.priority,
            "station_id": self.station_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SeasonalOffer(Base):
    """
    Time-limited promotions and special offers
    
    Examples:
    - Holiday discounts
    - Graduation season specials
    - Weekday promotions
    """
    __tablename__ = "seasonal_offers"
    __table_args__ = (
        Index('idx_offers_status', 'status'),
        Index('idx_offers_dates', 'valid_from', 'valid_until'),
        Index('idx_offers_station', 'station_id'),
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = Column(String(36), primary_key=True)
    offer_name = Column(String(200), nullable=False)
    offer_description = Column(Text, nullable=False)
    offer_type = Column(String(100), nullable=False)
    discount_amount = Column(Numeric(10, 2), nullable=True)
    discount_percentage = Column(Numeric(5, 2), nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)
    conditions = Column(JSON, nullable=True)
    status = Column(
        PgEnum(OfferStatus, name='offer_status', create_type=False),
        default=OfferStatus.DRAFT
    )
    usage_count = Column(Integer, default=0)
    station_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "offer_name": self.offer_name,
            "offer_description": self.offer_description,
            "offer_type": self.offer_type,
            "discount_amount": str(self.discount_amount) if self.discount_amount else None,
            "discount_percentage": str(self.discount_percentage) if self.discount_percentage else None,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "conditions": self.conditions,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "usage_count": self.usage_count,
            "station_id": self.station_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AvailabilityCalendar(Base):
    """
    Real-time booking availability tracking
    
    Tracks capacity for each date/time slot
    """
    __tablename__ = "availability_calendar"
    __table_args__ = (
        Index('idx_calendar_date', 'date'),
        Index('idx_calendar_datetime', 'date', 'time_slot'),
        Index('idx_calendar_available', 'is_available'),
        Index('idx_calendar_station', 'station_id'),
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = Column(String(36), primary_key=True)
    date = Column(Date, nullable=False)
    time_slot = Column(Time, nullable=False)
    max_capacity = Column(Integer, nullable=False, default=50)
    booked_capacity = Column(Integer, nullable=False, default=0)
    is_available = Column(Boolean, default=True)
    blackout_reason = Column(String(500), nullable=True)
    station_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "time_slot": self.time_slot.isoformat() if self.time_slot else None,
            "max_capacity": self.max_capacity,
            "booked_capacity": self.booked_capacity,
            "available_capacity": self.max_capacity - self.booked_capacity,
            "is_available": self.is_available,
            "blackout_reason": self.blackout_reason,
            "station_id": self.station_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CustomerTonePreference(Base):
    """
    Customer tone history and preferences
    
    Learns customer communication style over time
    """
    __tablename__ = "customer_tone_preferences"
    __table_args__ = (
        Index('idx_tone_customer', 'customer_id'),
        Index('idx_tone_detected', 'detected_tone'),
        Index('idx_tone_channel', 'interaction_channel'),
        Index('idx_tone_date', 'interaction_date'),
        Index('idx_tone_history', 'customer_id', 'interaction_date'),
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey('public.customers.id', ondelete='CASCADE'), nullable=False)
    detected_tone = Column(
        PgEnum(ToneType, name='tone_type', create_type=False),
        nullable=False
    )
    confidence_score = Column(Numeric(5, 2), nullable=True)
    interaction_channel = Column(String(50), nullable=False)
    message_sample = Column(Text, nullable=True)
    interaction_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationship
    customer = relationship("Customer", back_populates="tone_preferences")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "detected_tone": self.detected_tone.value if isinstance(self.detected_tone, Enum) else self.detected_tone,
            "confidence_score": str(self.confidence_score) if self.confidence_score else None,
            "interaction_channel": self.interaction_channel,
            "message_sample": self.message_sample,
            "interaction_date": self.interaction_date.isoformat() if self.interaction_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MenuItem(Base):
    """
    Menu items (proteins, sides, appetizers, etc.)
    
    Allows dynamic menu management without code deployment
    """
    __tablename__ = "menu_items"
    __table_args__ = (
        Index('idx_menu_items_category', 'category'),
        Index('idx_menu_items_available', 'is_available'),
        Index('idx_menu_items_premium', 'is_premium'),
        Index('idx_menu_items_station', 'station_id'),
        Index('idx_menu_items_lookup', 'category', 'is_available', 'display_order'),
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(
        PgEnum(MenuCategory, name='menu_category', create_type=False),
        nullable=False
    )
    base_price = Column(Numeric(10, 2), nullable=True)
    is_premium = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    dietary_info = Column(ARRAY(String), nullable=True)
    image_url = Column(String(500), nullable=True)
    display_order = Column(Integer, default=0)
    station_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value if isinstance(self.category, Enum) else self.category,
            "base_price": str(self.base_price) if self.base_price else None,
            "is_premium": self.is_premium,
            "is_available": self.is_available,
            "dietary_info": self.dietary_info,
            "image_url": self.image_url,
            "display_order": self.display_order,
            "station_id": self.station_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PricingTier(Base):
    """
    Pricing tiers/packages
    
    Examples: Essential Hibachi, Signature Experience, Ultimate Hibachi
    """
    __tablename__ = "pricing_tiers"
    __table_args__ = (
        Index('idx_pricing_tiers_level', 'tier_level'),
        Index('idx_pricing_tiers_active', 'is_active'),
        Index('idx_pricing_tiers_station', 'station_id'),
        Index('idx_pricing_tiers_lookup', 'tier_level', 'is_active', 'display_order'),
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = Column(String(36), primary_key=True)
    tier_level = Column(
        PgEnum(PricingTierLevel, name='pricing_tier_level', create_type=False),
        nullable=False
    )
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price_per_person = Column(Numeric(10, 2), nullable=False)
    min_guests = Column(Integer, nullable=False)
    max_proteins = Column(Integer, default=2)
    includes_appetizers = Column(Boolean, default=False)
    includes_noodles = Column(Boolean, default=False)
    includes_extended_show = Column(Boolean, default=False)
    features = Column(ARRAY(String), nullable=True)
    is_popular = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    station_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "tier_level": self.tier_level.value if isinstance(self.tier_level, Enum) else self.tier_level,
            "name": self.name,
            "description": self.description,
            "price_per_person": str(self.price_per_person),
            "min_guests": self.min_guests,
            "max_proteins": self.max_proteins,
            "includes_appetizers": self.includes_appetizers,
            "includes_noodles": self.includes_noodles,
            "includes_extended_show": self.includes_extended_show,
            "features": self.features,
            "is_popular": self.is_popular,
            "is_active": self.is_active,
            "display_order": self.display_order,
            "station_id": self.station_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================
# SYNC HISTORY MODEL
# ============================================

class SyncHistory(Base):
    """
    Audit trail for knowledge base synchronization operations
    Tracks all sync attempts, changes applied, and conflicts detected
    """
    __tablename__ = 'sync_history'
    __table_args__ = (
        Index('idx_sync_history_source', 'source_type', 'last_sync_time'),
        Index('idx_sync_history_status', 'sync_status', 'created_at'),
        Index('idx_sync_history_user', 'synced_by', 'created_at'),
        Index('idx_sync_history_created', 'created_at'),
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Source identification
    source_type = Column(
        PgEnum(SyncSourceType, name='sync_source_type', create_type=True),
        nullable=False
    )
    source_file_path = Column(Text, nullable=False)
    
    # Sync tracking
    file_hash = Column(String(64), nullable=False)
    last_sync_time = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Change statistics
    changes_applied = Column(Integer, default=0)
    items_added = Column(Integer, default=0)
    items_modified = Column(Integer, default=0)
    items_deleted = Column(Integer, default=0)
    conflicts_detected = Column(Integer, default=0)
    
    # Sync metadata
    synced_by = Column(String(100), nullable=True)
    sync_type = Column(
        PgEnum(SyncType, name='sync_type', create_type=True),
        default=SyncType.AUTO
    )
    sync_status = Column(
        PgEnum(SyncStatus, name='sync_status', create_type=True),
        default=SyncStatus.SUCCESS
    )
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "source_type": self.source_type.value if isinstance(self.source_type, Enum) else self.source_type,
            "source_file_path": self.source_file_path,
            "file_hash": self.file_hash,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "changes_applied": self.changes_applied,
            "items_added": self.items_added,
            "items_modified": self.items_modified,
            "items_deleted": self.items_deleted,
            "conflicts_detected": self.conflicts_detected,
            "synced_by": self.synced_by,
            "sync_type": self.sync_type.value if isinstance(self.sync_type, Enum) else self.sync_type,
            "sync_status": self.sync_status.value if isinstance(self.sync_status, Enum) else self.sync_status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
