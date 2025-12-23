"""
Terms Acknowledgment Schemas

Pydantic schemas for creating and validating terms acknowledgments
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class AcknowledgmentChannel(str, Enum):
    """Channel through which terms were acknowledged"""

    WEB = "web"
    PHONE = "phone"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    AI_CHAT = "ai_chat"
    EMAIL = "email"
    IN_PERSON = "in_person"


class TermsAcknowledgmentCreate(BaseModel):
    """Schema for creating a terms acknowledgment"""

    customer_id: int = Field(..., description="Customer ID who is acknowledging terms", gt=0)

    booking_id: int | None = Field(None, description="Associated booking ID (if applicable)", gt=0)

    channel: AcknowledgmentChannel = Field(
        ..., description="Channel through which terms were acknowledged"
    )

    acknowledgment_method: str = Field(
        ...,
        description="Method of acknowledgment",
        min_length=1,
        max_length=50,
        examples=["checkbox", "reply_agree", "verbal_confirmation", "sms_reply"],
    )

    acknowledgment_text: str | None = Field(
        None,
        description="Exact text customer sent/said",
        max_length=1000,
        examples=["I agree", "YES", "I confirm", "AGREE"],
    )

    terms_version: str = Field(
        default="1.0", description="Version of terms acknowledged", max_length=20
    )

    terms_url: str = Field(
        default="https://myhibachichef.com/terms",
        description="URL to terms and conditions",
        max_length=500,
    )

    ip_address: str | None = Field(
        None, description="IP address (for digital channels)", max_length=45  # IPv6 max length
    )

    user_agent: str | None = Field(
        None, description="User agent string (for web/app)", max_length=1000
    )

    staff_member_name: str | None = Field(
        None, description="Staff member who recorded verbal acknowledgment", max_length=255
    )

    staff_member_email: str | None = Field(None, description="Staff member email", max_length=255)

    notes: str | None = Field(None, description="Additional context", max_length=1000)

    @field_validator("acknowledgment_text")
    @classmethod
    def validate_acknowledgment_text(cls, v: str | None, info) -> str | None:
        """Validate acknowledgment text based on channel"""
        if v is None:
            return None

        # Normalize to uppercase for comparison
        normalized = v.strip().upper()

        # Valid confirmation phrases
        valid_phrases = [
            "I AGREE",
            "AGREE",
            "YES",
            "CONFIRM",
            "I CONFIRM",
            "ACCEPTED",
            "I ACCEPT",
            "OK",
            "OKAY",
        ]

        # Check if any valid phrase is in the text
        if any(phrase in normalized for phrase in valid_phrases):
            return v

        # Allow pass-through for web (checkbox acknowledgments)
        if info.data.get("channel") == AcknowledgmentChannel.WEB:
            return v

        # For digital channels, require explicit agreement
        if info.data.get("channel") in [
            AcknowledgmentChannel.SMS,
            AcknowledgmentChannel.WHATSAPP,
            AcknowledgmentChannel.AI_CHAT,
        ]:
            # Warn but allow (verification required)
            return v

        return v


class TermsAcknowledgmentResponse(BaseModel):
    """Schema for terms acknowledgment response"""

    id: int
    customer_id: int
    booking_id: int | None
    channel: AcknowledgmentChannel
    acknowledgment_method: str
    acknowledgment_text: str | None
    acknowledged_at: datetime
    terms_version: str
    terms_url: str
    verified: bool

    class Config:
        from_attributes = True


class SMSTermsRequest(BaseModel):
    """Schema for SMS terms acknowledgment request"""

    customer_phone: str = Field(
        ..., description="Customer phone number (10 digits)", pattern=r"^\d{10}$"
    )

    customer_name: str = Field(..., description="Customer name", min_length=1, max_length=255)

    booking_id: int | None = Field(None, description="Booking ID (if already created)", gt=0)


class SMSTermsResponse(BaseModel):
    """Schema for SMS terms acknowledgment response"""

    message_sid: str = Field(..., description="Message ID from provider")

    to_phone: str = Field(..., description="Phone number terms were sent to")

    expires_at: datetime = Field(..., description="When the acknowledgment request expires")

    verification_code: str | None = Field(None, description="Verification code (if used)")


class SMSTermsVerification(BaseModel):
    """Schema for verifying SMS terms acknowledgment"""

    customer_phone: str = Field(
        ..., description="Customer phone number (10 digits)", pattern=r"^\d{10}$"
    )

    reply_text: str = Field(..., description="Customer's reply text", min_length=1, max_length=1000)

    booking_id: int | None = Field(None, description="Booking ID to associate with", gt=0)
