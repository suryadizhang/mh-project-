# Models package init

# Import all models for Alembic discovery
from .booking_models import (
    AddonItem,
    Booking,
    BookingAddon,
    BookingAvailability,
    BookingMenuItem,
    BookingStatus,
    MenuItem,
    PreferredCommunication,
    TimeSlotConfiguration,
    TimeSlotEnum,
    User,
    UserRole,
)
from .stripe_models import (
    Customer,
    Dispute,
    Invoice,
    Payment,
    Price,
    Product,
    Refund,
    WebhookEvent,
)
from .core import Customer as CoreCustomer, Booking as CoreBooking, MessageThread, Message
from .lead_newsletter import (
    Lead, LeadContact, LeadContext, LeadEvent, SocialThread,
    Subscriber, Campaign, CampaignEvent,
    LeadSource, LeadStatus, LeadQuality, ContactChannel, SocialPlatform,
    CampaignChannel, CampaignStatus, CampaignEventType
)

__all__ = [
    # Stripe models
    "Customer",
    "Payment",
    "Invoice",
    "Product",
    "Price",
    "WebhookEvent",
    "Refund",
    "Dispute",
    # Booking models
    "User",
    "UserRole",
    "BookingStatus",
    "TimeSlotEnum",
    "PreferredCommunication",
    "TimeSlotConfiguration",
    "Booking",
    "MenuItem",
    "AddonItem",
    "BookingMenuItem",
    "BookingAddon",
    "BookingAvailability",
    # Core CRM models
    "CoreCustomer",
    "CoreBooking",
    "MessageThread",
    "Message",
    # Lead and Newsletter models
    "Lead",
    "LeadContact",
    "LeadContext",
    "LeadEvent",
    "SocialThread",
    "Subscriber",
    "Campaign",
    "CampaignEvent",
    # Enums
    "LeadSource",
    "LeadStatus",
    "LeadQuality",
    "ContactChannel",
    "SocialPlatform",
    "CampaignChannel",
    "CampaignStatus",
    "CampaignEventType",
]
