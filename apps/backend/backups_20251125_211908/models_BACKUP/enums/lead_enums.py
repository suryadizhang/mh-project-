"""Lead-related enumerations."""

import enum


class LeadSource(str, enum.Enum):
    """Lead acquisition sources."""

    WEB_QUOTE = "web_quote"
    CHAT = "chat"
    BOOKING_FAILED = "booking_failed"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    GOOGLE_MY_BUSINESS = "google_my_business"
    YELP = "yelp"
    SMS = "sms"
    PHONE = "phone"
    REFERRAL = "referral"
    EVENT = "event"
    PAYMENT = "payment"
    FINANCIAL = "financial"
    STRIPE = "stripe"
    PLAID = "plaid"
    WEBSITE = "website"  # Added for compatibility


class LeadStatus(str, enum.Enum):
    """Lead lifecycle status."""

    NEW = "new"
    WORKING = "working"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    CONVERTED = "converted"
    NURTURING = "nurturing"
    CUSTOMER = "customer"


class LeadQuality(str, enum.Enum):
    """Lead quality scoring."""

    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class ContactChannel(str, enum.Enum):
    """Communication channels."""

    EMAIL = "email"
    SMS = "sms"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    YELP = "yelp"
    WEB = "web"
