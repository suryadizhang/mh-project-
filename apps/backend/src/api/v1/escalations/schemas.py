"""
Escalation API Schemas
Request/response models for customer support escalations
"""

from datetime import datetime
from pydantic import BaseModel, Field, validator
import re
from typing import Optional


class EscalationCreateRequest(BaseModel):
    """Request to create a new escalation"""

    conversation_id: str = Field(..., description="ID of the conversation to escalate")
    phone: str = Field(..., description="Customer phone number", min_length=10, max_length=20)
    email: Optional[str] = Field(None, description="Customer email (optional)")
    preferred_method: str = Field(
        "sms", description="Preferred contact method: sms, call, or email"
    )
    reason: str = Field(..., description="Reason for escalation", min_length=10, max_length=1000)
    priority: str = Field("medium", description="Priority level: low, medium, high, urgent")
    customer_consent: bool = Field(True, description="Customer consent to receive SMS/calls")
    metadata: dict = Field(default_factory=dict, description="Additional context")

    @validator("phone")
    def validate_phone(cls, v):
        """Validate phone number format"""
        # Remove all non-digit characters
        digits_only = re.sub(r"\D", "", v)

        # Check if it's a valid length (10-15 digits)
        if not (10 <= len(digits_only) <= 15):
            raise ValueError("Phone number must be between 10 and 15 digits")

        # Return formatted phone (keep original format or normalize)
        return v

    @validator("preferred_method")
    def validate_method(cls, v):
        """Validate preferred contact method"""
        valid_methods = ["sms", "call", "email"]
        if v.lower() not in valid_methods:
            raise ValueError(f"Method must be one of: {', '.join(valid_methods)}")
        return v.lower()

    @validator("priority")
    def validate_priority(cls, v):
        """Validate priority level"""
        valid_priorities = ["low", "medium", "high", "urgent"]
        if v.lower() not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v.lower()

    class Config:
        schema_extra = {
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "phone": "+1-555-0100",
                "email": "customer@example.com",
                "preferred_method": "sms",
                "reason": "Need immediate assistance with booking modification for tomorrow",
                "priority": "high",
                "customer_consent": True,
                "metadata": {"booking_id": "booking-123", "issue_type": "booking_modification"},
            }
        }


class EscalationResponse(BaseModel):
    """Response for escalation operations"""

    id: str
    conversation_id: str
    customer_id: Optional[str]
    phone: str
    email: Optional[str]
    preferred_method: str
    reason: str
    priority: str
    status: str
    assigned_to_id: Optional[str]
    assigned_to: Optional[str]
    resolved_by_id: Optional[str]
    resolved_by: Optional[str]
    resolution_notes: Optional[str]
    error_message: Optional[str]
    metadata: dict
    tags: list
    created_at: str
    updated_at: str
    resolved_at: Optional[str]

    class Config:
        from_attributes = True


class EscalationAssignRequest(BaseModel):
    """Request to assign escalation to an admin"""

    admin_id: str = Field(..., description="ID of admin to assign to")
    notes: Optional[str] = Field(None, description="Assignment notes")


class EscalationResolveRequest(BaseModel):
    """Request to resolve an escalation"""

    resolution_notes: str = Field(..., description="Resolution notes", min_length=10)
    resume_ai: bool = Field(True, description="Resume AI conversation after resolution")


class EscalationListRequest(BaseModel):
    """Request to list escalations with filters"""

    status: Optional[str] = Field(None, description="Filter by status")
    priority: Optional[str] = Field(None, description="Filter by priority")
    assigned_to_id: Optional[str] = Field(None, description="Filter by assigned admin")
    from_date: Optional[datetime] = Field(None, description="Filter from date")
    to_date: Optional[datetime] = Field(None, description="Filter to date")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")


class EscalationListResponse(BaseModel):
    """Response for list escalations"""

    escalations: list[EscalationResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class EscalationStatsResponse(BaseModel):
    """Statistics about escalations"""

    total_escalations: int
    pending: int
    assigned: int
    in_progress: int
    resolved: int
    closed: int
    error: int
    average_resolution_time_hours: Optional[float]
    escalations_today: int
    escalations_this_week: int


class SendSMSRequest(BaseModel):
    """Request to send SMS via escalation"""

    escalation_id: str = Field(..., description="ID of the escalation")
    message: str = Field(..., description="SMS message content", min_length=1, max_length=1600)
    metadata: dict = Field(default_factory=dict, description="Additional context")


class SMSResponse(BaseModel):
    """Response for SMS operations"""

    escalation_id: str
    message_id: Optional[str]
    status: str
    sent_at: Optional[str]
    error_message: Optional[str]
