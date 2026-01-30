"""
Database Models Package - SQLAlchemy 2.0 ORM

This package contains all SQLAlchemy models organized by business domain (schema).

Usage:
    from db.models import User, Booking, Customer, Lead, Subscriber
    from db.models import Base  # SQLAlchemy declarative base

Organization:
    - base_class.py: SQLAlchemy Base class (in parent db/ directory)
    - core.py: Core business entities (bookings, customers, chefs, messaging, reviews)
    - identity.py: Authentication & authorization (users, roles, permissions, stations)
    - support_communications.py: Customer support (escalations, call recordings)
    - feedback_marketing.py: Reviews, coupons, QR codes
    - events.py: Event sourcing (domain events, inbox, outbox)
    - lead.py: Lead management & social media integration
    - newsletter.py: Email/SMS campaigns with RingCentral integration
    - integra.py: External integrations (payments, calls, social webhooks)

All models use SQLAlchemy 2.0 declarative mapping with full type hints.
"""

# Base class (required for all models) - import from parent db/ directory
from ..base_class import Base

# Address model (Enterprise address management - Smart Scheduling Phase 1)
from .address import Address

# Core schema (7 tables) - NOTE: Chef moved to ops schema
from .core import CoreMessage  # Renamed from Message to avoid conflicts
from .core import Booking, Customer, MessageThread, PricingTier, Review, SocialThread

# CRM schema (Contact, Lead, Campaign models)
from .crm import Contact  # Unified contact record for inbox and CRM
from .crm import (
    Lead,  # Lead tracking with scoring and qualification (moved from lead.py)
)

# Events schema (3 tables)
from .events import DomainEvent, Inbox, Outbox

# Feedback & Marketing schemas (5 tables)
from .feedback_marketing import (
    CustomerReview,
    DiscountCoupon,
    QRCode,
    QRScan,
    ReviewEscalation,
)

# Identity schema (9 tables) - Using modular identity/ package
from .identity import (
    OAuthAccount,
    Permission,
    Role,
    RolePermission,
    Station,
    StationAccessToken,
    StationAuditLog,
    StationUser,
    User,
    UserRole,
)

# Integra schema (4 tables)
from .integra import CallSession, PaymentEvent, PaymentMatch, SocialInbox

# Lead schema (6 tables - Lead moved to crm.py)
from .lead import (
    LeadSocialThread,  # Renamed class to avoid conflict with core.SocialThread
)
from .lead import (
    BusinessSocialAccount,
    LeadContact,
    LeadContext,
    LeadEvent,
    SocialIdentity,
)

# Newsletter schema (7 tables)
from .newsletter import (
    Campaign,
    CampaignEvent,
    CampaignSMSLimit,
    SMSDeliveryEvent,
    SMSSendQueue,
    SMSTemplate,
    Subscriber,
)

# Operations schema (Chef + operational models)
from .ops import Chef  # Moved from core to ops for operations management
from .ops import FoodIncentiveType  # Enum: none, free_noodles, free_appetizer
from .ops import NegotiationIncentive  # Smart Scheduling - food incentive tiers

# Slot Hold (1 table + enum) - Pre-booking slot reservation system
from .slot_hold import SlotHold, SlotHoldStatus

# Stripe schema (5 tables + enums) - Payment processing
from .stripe import (  # Enums
    Invoice,
    InvoiceStatus,
    PaymentStatus,
    Refund,
    RefundStatus,
    StripeCustomer,
    StripePayment,
    WebhookEvent,
    WebhookEventStatus,
)

# Support & Communications schemas (2 tables + enums)
from .support_communications import (  # Enums for Voice AI
    CallDirection,
    CallRecording,
    CallStatus,
    Escalation,
    EscalationMethod,
    EscalationPriority,
    EscalationStatus,
    RecordingStatus,
    RecordingType,
)

# Travel Cache (1 table) - Travel time API response caching
from .travel_cache import TravelCache

# All models for easy iteration
__all__ = [
    # Base
    "Base",
    # CRM schema (1 model)
    "Contact",
    # Core schema (7 models - Chef moved to ops)
    "Address",  # Enterprise address management
    "Booking",
    "Customer",
    "CoreMessage",  # Renamed from Message to avoid conflicts
    "MessageThread",
    "PricingTier",
    "Review",
    "SocialThread",
    # Identity schema (10 models - added OAuthAccount)
    "OAuthAccount",
    "Permission",
    "Role",
    "RolePermission",
    "Station",
    "StationAccessToken",
    "StationAuditLog",
    "StationUser",
    "User",
    "UserRole",
    # Support & Communications (2 models + 7 enums)
    "CallRecording",
    "Escalation",
    # Voice AI Enums
    "CallStatus",
    "CallDirection",
    "EscalationPriority",
    "EscalationMethod",
    "EscalationStatus",
    "RecordingType",
    "RecordingStatus",
    # Feedback & Marketing (5 models)
    "CustomerReview",
    "DiscountCoupon",
    "QRCode",
    "QRScan",
    "ReviewEscalation",
    # Events (3 models)
    "DomainEvent",
    "Inbox",
    "Outbox",
    # Lead (7 models)
    "BusinessSocialAccount",
    "Lead",
    "LeadContact",
    "LeadContext",
    "LeadEvent",
    "LeadSocialThread",
    "SocialIdentity",
    # Newsletter (7 models)
    "Campaign",
    "CampaignEvent",
    "CampaignSMSLimit",
    "SMSDeliveryEvent",
    "SMSSendQueue",
    "SMSTemplate",
    "Subscriber",
    # Integra (4 models)
    "CallSession",
    "PaymentEvent",
    "PaymentMatch",
    "SocialInbox",
    # Stripe (5 models + 4 enums)
    "Invoice",
    "Refund",
    "StripeCustomer",
    "StripePayment",
    "WebhookEvent",
    # Stripe Enums
    "InvoiceStatus",
    "PaymentStatus",
    "RefundStatus",
    "WebhookEventStatus",
    # Travel Cache (1 model)
    "TravelCache",
    # Slot Hold (1 model + 1 enum)
    "SlotHold",
    "SlotHoldStatus",
]

# Model registry by schema (useful for reflection/introspection)
MODELS_BY_SCHEMA = {
    "crm": [
        Contact,  # Unified contact record (table: crm_contacts)
        Lead,  # Lead tracking (moved from lead schema to crm schema)
    ],
    "core": [
        Address,  # Enterprise address management (Smart Scheduling Phase 1)
        Booking,
        Customer,
        CoreMessage,  # Renamed from Message
        MessageThread,
        PricingTier,
        Review,
        SocialThread,
        SlotHold,  # Pre-booking slot reservation system
    ],
    "ops": [
        Chef,  # Moved from core to ops
        NegotiationIncentive,  # Smart Scheduling food incentives
        FoodIncentiveType,  # Enum: none, free_noodles, free_appetizer
    ],
    "identity": [
        OAuthAccount,
        Permission,
        Role,
        RolePermission,
        Station,
        StationAccessToken,
        StationAuditLog,
        StationUser,
        User,
        UserRole,
    ],
    "support": [Escalation],
    "communications": [CallRecording],
    "feedback": [
        CustomerReview,
        DiscountCoupon,
        ReviewEscalation,
    ],
    "marketing": [
        QRCode,
        QRScan,
    ],
    "events": [
        DomainEvent,
        Inbox,
        Outbox,
    ],
    "lead": [
        BusinessSocialAccount,
        LeadContact,
        LeadContext,
        LeadEvent,
        LeadSocialThread,
        SocialIdentity,
    ],
    "newsletter": [
        Campaign,
        CampaignEvent,
        CampaignSMSLimit,
        SMSDeliveryEvent,
        SMSSendQueue,
        SMSTemplate,
        Subscriber,
    ],
    "integra": [
        CallSession,
        PaymentEvent,
        PaymentMatch,
        SocialInbox,
    ],
    "stripe": [
        Invoice,
        Refund,
        StripeCustomer,
        StripePayment,
        WebhookEvent,
    ],
    "public": [
        TravelCache,  # Travel time API response caching (Smart Scheduling)
    ],
}

# Total model count (should match actual models created)
# Note: Renamed models to avoid conflicts:
# - OAuthAccount (identity.social_accounts) vs BusinessSocialAccount (lead.social_accounts)
# - LeadSocialThread (lead.social_threads) vs SocialThread (core.social_threads)
# Moved models to consolidate:
# - Lead: from db.models.lead → db.models.crm (schema: lead → crm)
# - Contact: added to db.models.crm (table: crm_contacts)
# Added models:
# - Stripe: Invoice, Refund, StripeCustomer, StripePayment, WebhookEvent (5 models)
# - Smart Scheduling Phase 1: Address, NegotiationIncentive (2 models)
# - Travel Cache: TravelCache (1 model) - API response caching
# - Slot Hold: SlotHold (1 model) - Pre-booking reservations
TOTAL_MODELS = sum(len(models) for models in MODELS_BY_SCHEMA.values())
assert TOTAL_MODELS == 57, f"Expected 57 models, found {TOTAL_MODELS}"
