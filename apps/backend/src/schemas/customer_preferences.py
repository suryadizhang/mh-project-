"""
Customer Preferences Schemas
============================

Pydantic schemas for the unified customer preferences capture system.
Handles chef requests, allergens, and special instructions.

Related Tables:
- core.bookings (stores preferences per booking)
- core.common_allergens (reference table)

Related Services:
- services/customer_preferences_service.py
"""

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# =====================================================
# Common Allergens Reference
# =====================================================


class CommonAllergenInfo(BaseModel):
    """A common allergen from the reference table."""

    code: str = Field(
        ..., description="Allergen code: shellfish, fish, soy, gluten, etc."
    )
    display_name: str = Field(..., description="Human-readable name with examples")
    icon: Optional[str] = Field(None, description="Emoji icon for UI display")
    chef_action: Optional[str] = Field(
        None, description="Cooking instructions for chef"
    )
    display_order: int = Field(0, description="Order in UI list")


class CommonAllergensListResponse(BaseModel):
    """Response containing all available common allergens."""

    allergens: List[CommonAllergenInfo]
    total: int


# =====================================================
# Chef Request Types
# =====================================================

ChefRequestSource = Literal[
    "online_form",  # Customer selected on booking form
    "phone",  # Customer mentioned during phone call
    "text",  # Customer mentioned in text/SMS
    "ai_chat",  # AI detected chef name in conversation
    "email",  # Customer mentioned in email
    "returning_customer",  # System prompt for returning customer
    "walk_in",  # In-person at event or office
]

AllergenConfirmMethod = Literal[
    "online",  # Confirmed via online booking form
    "sms",  # Confirmed via SMS reply
    "phone",  # Confirmed during phone call
    "email",  # Confirmed via email
    "in_person",  # Confirmed in person
]


# =====================================================
# Customer Preferences (Combined DTO)
# =====================================================


class ChefRequestInfo(BaseModel):
    """Chef request details."""

    chef_was_requested: bool = Field(
        False, description="True if customer requested a specific chef"
    )
    requested_chef_id: Optional[UUID] = Field(
        None, description="UUID of requested chef"
    )
    requested_chef_name: Optional[str] = Field(
        None, description="Name of requested chef (for display)"
    )
    chef_request_source: Optional[ChefRequestSource] = Field(
        None, description="How request was captured"
    )


class AllergenInfo(BaseModel):
    """Allergen and dietary information."""

    common_allergens: List[str] = Field(
        default_factory=list,
        description="List of allergen codes: shellfish, soy, eggs, dairy, sesame, nuts, gluten, fish, msg",
    )
    allergen_disclosure: Optional[str] = Field(
        None, max_length=1000, description="Free text for other allergens/dietary needs"
    )
    allergen_confirmed: bool = Field(
        False, description="True if info was confirmed with customer"
    )
    allergen_confirmed_method: Optional[AllergenConfirmMethod] = Field(None)
    allergen_confirmed_at: Optional[datetime] = Field(None)
    allergen_confirmed_by_id: Optional[UUID] = Field(
        None, description="Staff who confirmed"
    )
    allergen_confirmed_by_name: Optional[str] = Field(
        None, description="Staff name (for display)"
    )


class CustomerPreferencesResponse(BaseModel):
    """Full customer preferences for a booking (read)."""

    booking_id: UUID

    # Chef Request
    chef_request: ChefRequestInfo

    # Allergens
    allergens: AllergenInfo

    # Special Instructions (existing field)
    special_requests: Optional[str] = Field(
        None, description="General special instructions"
    )

    # Metadata
    last_updated: Optional[datetime] = None


class CustomerPreferencesUpdate(BaseModel):
    """Update customer preferences for a booking."""

    # Chef Request (optional section)
    chef_was_requested: Optional[bool] = None
    requested_chef_id: Optional[UUID] = None
    chef_request_source: Optional[ChefRequestSource] = None

    # Allergens (optional section)
    common_allergens: Optional[List[str]] = None
    allergen_disclosure: Optional[str] = Field(None, max_length=1000)
    allergen_confirmed: Optional[bool] = None
    allergen_confirmed_method: Optional[AllergenConfirmMethod] = None

    # Special Instructions
    special_requests: Optional[str] = Field(None, max_length=2000)


# =====================================================
# Chef Prep Summary (for Chef App)
# =====================================================


class AllergenPrepNote(BaseModel):
    """Single allergen with cooking action for chef."""

    allergen: str = Field(..., description="Allergen code")
    display_name: str = Field(..., description="Human-readable name")
    icon: str = Field("⚠️", description="Emoji icon")
    chef_action: str = Field(..., description="What chef should do")


class ChefPrepAllergensResponse(BaseModel):
    """Allergen summary for chef prep view."""

    booking_id: UUID
    customer_name: str
    event_datetime: datetime

    # Allergens
    has_allergens: bool = Field(False)
    allergen_notes: List[AllergenPrepNote] = Field(default_factory=list)
    other_dietary: Optional[str] = Field(None, description="Free text dietary notes")

    # Confirmation status
    allergen_confirmed: bool = Field(False)
    allergen_confirmed_method: Optional[str] = None

    # Special requests
    special_requests: Optional[str] = None


# =====================================================
# Bonus Calculation Response
# =====================================================


class ChefRequestBonusInfo(BaseModel):
    """Information about chef request bonus for a booking."""

    booking_id: UUID
    chef_was_requested: bool = False
    requested_chef_id: Optional[UUID] = None
    requested_chef_name: Optional[str] = None
    assigned_chef_id: Optional[UUID] = None
    assigned_chef_name: Optional[str] = None

    # Bonus calculation
    bonus_eligible: bool = Field(
        False, description="True if requested chef = assigned chef"
    )
    bonus_percentage: int = Field(
        10, description="Bonus percentage from SSoT (default 10%)"
    )
    base_order_cents: int = Field(
        0, description="Base order value (adults × rate + kids × rate)"
    )
    bonus_amount_cents: int = Field(0, description="Calculated bonus amount")
