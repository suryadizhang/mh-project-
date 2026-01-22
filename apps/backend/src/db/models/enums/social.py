"""
Social Platform Enums (Shared)
==============================

Centralized social platform and thread status definitions.

Consolidates previously duplicated enums from:
- core.py (INSTAGRAM, FACEBOOK, TWITTER, TIKTOK, LINKEDIN)
- lead.py (INSTAGRAM, FACEBOOK, GOOGLE, YELP)
- crm.py (INSTAGRAM, FACEBOOK, GOOGLE, YELP)
- integra.py (INSTAGRAM, FACEBOOK, GOOGLE_BUSINESS, YELP, TIKTOK, TWITTER)

This merged version includes ALL platforms from all sources.
"""

from enum import Enum


class SocialPlatform(str, Enum):
    """
    Supported social media platforms.

    Merged from 4 model files to create single source of truth.

    Categories:
        Social Networks: INSTAGRAM, FACEBOOK, TWITTER, TIKTOK, LINKEDIN
        Review Platforms: GOOGLE, GOOGLE_BUSINESS, YELP
        Messaging: WHATSAPP
        Other: WEBSITE, EMAIL, PHONE

    Note:
        - GOOGLE: General Google account/reviews
        - GOOGLE_BUSINESS: Google Business Profile (Maps, GMB)
    """

    # Major Social Networks
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"

    # Review Platforms
    GOOGLE = "google"
    GOOGLE_BUSINESS = "google_business"
    YELP = "yelp"

    # Messaging Platforms
    WHATSAPP = "whatsapp"

    # Other Contact Methods (for lead tracking)
    WEBSITE = "website"
    EMAIL = "email"
    PHONE = "phone"
    OTHER = "other"


class SocialThreadStatus(str, Enum):
    """
    Social media thread/conversation status.

    Merged from 3 model files:
    - core.py: OPEN, PENDING, REPLIED, CLOSED
    - lead.py: OPEN, PENDING, RESOLVED
    - crm.py: OPEN, PENDING, RESOLVED

    All statuses included for backwards compatibility.

    Workflow:
        OPEN → PENDING → REPLIED → RESOLVED/CLOSED

    Values:
        OPEN: New thread, needs attention
        PENDING: Awaiting customer response
        REPLIED: Staff has replied, awaiting follow-up
        IN_PROGRESS: Being actively worked on
        RESOLVED: Issue resolved, thread complete
        CLOSED: Thread manually closed
        ARCHIVED: Old thread archived for records
    """

    OPEN = "open"
    PENDING = "pending"
    REPLIED = "replied"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ARCHIVED = "archived"
