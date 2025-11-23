"""
Models package - Export all database models
"""

from .base import BaseModel
# Import booking_reminder BEFORE booking to avoid circular dependency
from .booking_reminder import BookingReminder, ReminderType, ReminderStatus
from .booking import Booking, BookingStatus, Payment, PaymentStatus
from .customer import Customer, CustomerPreference, CustomerStatus
from .events import DomainEvent, OutboxEntry
from .notification import NotificationGroup, NotificationGroupMember, NotificationGroupEvent, NotificationEventType
from .review import CustomerReviewBlogPost, ReviewApprovalLog
from .knowledge_base import (
    BusinessRule,
    FAQItem,
    TrainingData,
    UpsellRule,
    SeasonalOffer,
    AvailabilityCalendar,
    CustomerTonePreference,
    MenuItem,
    PricingTier,
    RuleCategory,
    ToneType,
    UpsellTriggerType,
    OfferStatus,
    MenuCategory,
    PricingTierLevel,
)
# Lead management models
from .lead import Lead, LeadContact, LeadContext, LeadEvent
# Newsletter/Campaign models
from .newsletter import Campaign, CampaignEvent, SMSDeliveryEvent, Subscriber
# Social media & review models
from .social import (
    SocialAccount,
    SocialIdentity,
    SocialThread,
    SocialMessage,
    Review,
    CustomerReview,
    DiscountCoupon,
)
# RingCentral call recording and communications
from .call_recording import CallRecording, RecordingStatus, CallStatus, CallDirection, RecordingType
# Business/Multi-tenancy models
from .business import Business
# Customer support escalations
from .escalation import Escalation, EscalationStatus, EscalationMethod, EscalationPriority
# Payment notifications (Stripe, Venmo, Zelle, etc.)
from .payment_notification import PaymentNotification, PaymentProvider, PaymentNotificationStatus
# RBAC (Role-Based Access Control)
from .role import Role, Permission, RoleType, PermissionType
# System events and audit trail
from .system_event import SystemEvent
# Terms & Conditions acknowledgment
from .terms_acknowledgment import TermsAcknowledgment, AcknowledgmentChannel

__all__ = [
    "BaseModel",
    "Booking",
    "BookingReminder",
    "BookingStatus",
    "Customer",
    "CustomerPreference",
    "CustomerReviewBlogPost",
    "CustomerStatus",
    "DomainEvent",
    "OutboxEntry",
    "NotificationGroup",
    "NotificationGroupMember",
    "NotificationGroupEvent",
    "NotificationEventType",
    "Payment",
    "PaymentStatus",
    "ReviewApprovalLog",
    # Knowledge Base Models
    "BusinessRule",
    "FAQItem",
    "TrainingData",
    "UpsellRule",
    "SeasonalOffer",
    "AvailabilityCalendar",
    "CustomerTonePreference",
    "MenuItem",
    "PricingTier",
    # Lead Management Models
    "Lead",
    "LeadContact",
    "LeadContext",
    "LeadEvent",
    # Newsletter/Campaign Models
    "Campaign",
    "CampaignEvent",
    "SMSDeliveryEvent",
    "Subscriber",
    # Social Media & Review Models
    "SocialAccount",
    "SocialIdentity",
    "SocialThread",
    "SocialMessage",
    "Review",
    "CustomerReview",
    "DiscountCoupon",
    # RingCentral Communications
    "CallRecording",
    "RecordingStatus",
    "CallStatus",
    "CallDirection",
    "RecordingType",
    # Business/Multi-tenancy
    "Business",
    # Customer Support Escalations
    "Escalation",
    "EscalationStatus",
    "EscalationMethod",
    "EscalationPriority",
    # Payment Notifications
    "PaymentNotification",
    "PaymentProvider",
    "PaymentNotificationStatus",
    # RBAC
    "Role",
    "Permission",
    "RoleType",
    "PermissionType",
    # System Events
    "SystemEvent",
    # Terms & Conditions
    "TermsAcknowledgment",
    "AcknowledgmentChannel",
    # Enums
    "ReminderType",
    "ReminderStatus",
    "RuleCategory",
    "ToneType",
    "UpsellTriggerType",
    "OfferStatus",
    "MenuCategory",
    "PricingTierLevel",
]

