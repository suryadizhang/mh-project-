"""Social media-related enumerations."""

import enum


class SocialPlatform(str, enum.Enum):
    """Social media platforms."""

    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    GOOGLE_BUSINESS = "google_business"
    YELP = "yelp"
    SMS = "sms"
    PHONE = "phone"
    STRIPE = "stripe"
    PLAID = "plaid"


class ThreadStatus(str, enum.Enum):
    """Social conversation thread status."""

    OPEN = "open"
    WAITING_CUSTOMER = "waiting_customer"
    WAITING_AGENT = "waiting_agent"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ReviewSource(str, enum.Enum):
    """Review source platforms."""

    GOOGLE = "google"
    YELP = "yelp"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    DIRECT = "direct"


class ReviewStatus(str, enum.Enum):
    """Review status for tracking."""

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESPONDED = "responded"
    ESCALATED = "escalated"
    CLOSED = "closed"


class MessageDirection(str, enum.Enum):
    """Direction of message (inbound or outbound)."""

    IN = "in"
    OUT = "out"


class MessageKind(str, enum.Enum):
    """Type of social media message."""

    DM = "dm"  # Direct message
    COMMENT = "comment"  # Public comment
    REVIEW = "review"  # Review/rating
    REPLY = "reply"  # Reply to comment
    MENTION = "mention"  # Mention/tag
    STORY_REPLY = "story_reply"  # Reply to story
