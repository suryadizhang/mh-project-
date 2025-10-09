"""
Unified Database Models for MyHibachi Backend
Combines business models, AI chat system, and core CRM functionality
"""

# Import the base database configuration
from core.database import Base

# Core business models
from .domain.core import Customer, Booking, Payment, MessageThread, Message, Event
from .domain.booking import (
    AddonItem, Booking as BookingModel, BookingAddon, BookingAvailability,
    BookingMenuItem, BookingStatus, MenuItem, PreferredCommunication,
    TimeSlotConfiguration, TimeSlotEnum, User, UserRole
)
from .domain.stripe import (
    Customer as StripeCustomer, Dispute, Invoice, Payment as StripePayment,
    Price, Product, Refund, WebhookEvent
)
from .domain.leads import (
    Lead, LeadContact, LeadContext, LeadEvent, SocialThread,
    Subscriber, Campaign, CampaignEvent,
    LeadSource, LeadStatus, LeadQuality, ContactChannel, SocialPlatform,
    CampaignChannel, CampaignStatus, CampaignEventType
)

# AI Chat system models
from .domain.ai_chat import (
    Conversation, Message as AIMessage, KnowledgeBaseChunk,
    EscalationRule, ConversationAnalytics, TrainingData,
    ChannelType, ConversationStatus, MessageRole
)

__all__ = [
    # Base
    "Base",
    
    # Core CRM models
    "Customer",
    "Booking",
    "Payment", 
    "MessageThread",
    "Message",
    "Event",
    
    # Booking system models
    "BookingModel",
    "User",
    "UserRole",
    "BookingStatus",
    "TimeSlotEnum",
    "PreferredCommunication",
    "TimeSlotConfiguration",
    "MenuItem",
    "AddonItem",
    "BookingMenuItem",
    "BookingAddon",
    "BookingAvailability",
    
    # Stripe payment models
    "StripeCustomer",
    "StripePayment",
    "Invoice",
    "Product",
    "Price",
    "WebhookEvent",
    "Refund",
    "Dispute",
    
    # Lead and Newsletter models
    "Lead",
    "LeadContact",
    "LeadContext",
    "LeadEvent",
    "SocialThread",
    "Subscriber",
    "Campaign",
    "CampaignEvent",
    
    # Enums for Leads
    "LeadSource",
    "LeadStatus",
    "LeadQuality",
    "ContactChannel",
    "SocialPlatform",
    "CampaignChannel",
    "CampaignStatus",
    "CampaignEventType",
    
    # AI Chat models
    "Conversation",
    "AIMessage",
    "KnowledgeBaseChunk",
    "EscalationRule",
    "ConversationAnalytics",
    "TrainingData",
    
    # AI Chat enums
    "ChannelType",
    "ConversationStatus",
    "MessageRole",
]