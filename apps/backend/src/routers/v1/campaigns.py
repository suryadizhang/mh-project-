"""
Nurture Campaign API endpoints.

Provides REST API for automated lead nurturing campaigns.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from services.nurture_campaign_service import (
    NurtureCampaignService,
    CampaignType,
    CampaignStatus,
)
from core.dependencies import get_nurture_campaign_service


router = APIRouter(prefix="/campaigns", tags=["campaigns"])


# Request/Response models


class EnrollLeadRequest(BaseModel):
    """Request model for enrolling a lead in a campaign."""

    lead_id: int
    campaign_type: CampaignType
    personalization: Optional[dict] = None
    skip_if_enrolled: bool = True


class SendMessageRequest(BaseModel):
    """Request model for sending next campaign message."""

    lead_id: int
    campaign_type: CampaignType


class HandleResponseRequest(BaseModel):
    """Request model for handling campaign response."""

    lead_id: int
    response_type: str  # 'reply', 'click', 'opt_out', 'booking'
    response_data: Optional[dict] = None


# Endpoints


@router.post("/enroll", status_code=status.HTTP_201_CREATED)
async def enroll_lead(
    request: EnrollLeadRequest,
    service: NurtureCampaignService = Depends(get_nurture_campaign_service),
):
    """
    Enroll a lead in a nurture campaign.

    Starts automated message sequence based on campaign type.
    """
    try:
        enrollment = await service.enroll_lead(
            lead_id=request.lead_id,
            campaign_type=request.campaign_type,
            personalization=request.personalization,
            skip_if_enrolled=request.skip_if_enrolled,
        )
        return {"success": True, "data": enrollment}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/send-message", status_code=status.HTTP_200_OK)
async def send_next_message(
    request: SendMessageRequest,
    service: NurtureCampaignService = Depends(get_nurture_campaign_service),
):
    """
    Send the next scheduled message in a campaign.

    Called by scheduled job to process pending messages.
    """
    try:
        result = await service.send_next_message(
            lead_id=request.lead_id,
            campaign_type=request.campaign_type,
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/response", status_code=status.HTTP_200_OK)
async def handle_response(
    request: HandleResponseRequest,
    service: NurtureCampaignService = Depends(get_nurture_campaign_service),
):
    """
    Handle lead response to campaign message.

    Tracks engagement and adjusts campaign flow accordingly.
    """
    try:
        result = await service.handle_response(
            lead_id=request.lead_id,
            response_type=request.response_type,
            response_data=request.response_data,
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/stats")
async def get_campaign_stats(
    campaign_type: Optional[CampaignType] = None,
    service: NurtureCampaignService = Depends(get_nurture_campaign_service),
):
    """
    Get campaign performance statistics.

    Returns metrics like open rate, click rate, and conversion rate.
    """
    try:
        stats = await service.get_campaign_stats(campaign_type)
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/types")
async def list_campaign_types():
    """
    List available campaign types.

    Returns all supported campaign types with descriptions.
    """
    return {
        "success": True,
        "data": [
            {"type": "welcome", "description": "Welcome new leads"},
            {"type": "post_inquiry", "description": "Follow up after inquiry"},
            {"type": "abandoned_quote", "description": "Recover abandoned quotes"},
            {"type": "post_event", "description": "Post-event feedback and referral"},
            {"type": "reactivation", "description": "Re-engage inactive leads"},
            {"type": "seasonal", "description": "Holiday/seasonal promotions"},
        ],
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "campaigns"}
