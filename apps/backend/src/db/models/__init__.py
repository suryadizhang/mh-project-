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

# Core schema (10 tables)
from .core import (
    Booking,
    Chef,
    Customer,
    Message,
    MessageThread,
    PricingTier,
    Review,
    SocialThread,
)

# Identity schema (9 tables)
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

# Support & Communications schemas (2 tables)
from .support_communications import (
    CallRecording,
    Escalation,
)

# Feedback & Marketing schemas (5 tables)
from .feedback_marketing import (
    CustomerReview,
    DiscountCoupon,
    QRCode,
    QRScan,
    ReviewEscalation,
)

# Events schema (3 tables)
from .events import (
    DomainEvent,
    Inbox,
    Outbox,
)

# Lead schema (7 tables)
from .lead import (
    BusinessSocialAccount,
    Lead,
    LeadContact,
    LeadContext,
    LeadEvent,
    SocialIdentity,
    LeadSocialThread,  # Renamed class to avoid conflict with core.SocialThread
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

# Integra schema (4 tables)
from .integra import (
    CallSession,
    PaymentEvent,
    PaymentMatch,
    SocialInbox,
)

# All models for easy iteration
__all__ = [
    # Base
    "Base",

    # Core schema (10 models)
    "Booking",
    "Chef",
    "Customer",
    "Message",
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

    # Support & Communications (2 models)
    "CallRecording",
    "Escalation",

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
]

# Model registry by schema (useful for reflection/introspection)
MODELS_BY_SCHEMA = {
    "core": [
        Booking,
        Chef,
        Customer,
        Message,
        MessageThread,
        PricingTier,
        Review,
        SocialThread,
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
        Lead,
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
}

# Total model count (should match actual models created)
# Note: Renamed models to avoid conflicts:
# - OAuthAccount (identity.social_accounts) vs BusinessSocialAccount (lead.social_accounts)
# - LeadSocialThread (lead.social_threads) vs SocialThread (core.social_threads)
TOTAL_MODELS = sum(len(models) for models in MODELS_BY_SCHEMA.values())
assert TOTAL_MODELS == 46, f"Expected 46 models, found {TOTAL_MODELS}"
