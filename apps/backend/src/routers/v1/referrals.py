"""
Referral API endpoints.

Provides REST API for referral program management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from services.referral_service import ReferralService, ReferralStatus
from core.dependencies import get_referral_service


router = APIRouter(prefix="/referrals", tags=["referrals"])


# Request/Response models


class CreateReferralRequest(BaseModel):
    """Request model for creating a referral."""

    referrer_id: int
    referee_email: EmailStr
    referee_name: Optional[str] = None
    referee_phone: Optional[str] = None
    reward_amount: float = 50.0
    reward_type: str = "credit"


class TrackConversionRequest(BaseModel):
    """Request model for tracking referral conversion."""

    referral_code: str
    referee_id: int
    conversion_value: float
    conversion_type: str = "booking"


class AwardCreditRequest(BaseModel):
    """Request model for awarding referral credit."""

    referrer_id: int
    amount: float
    reason: str


# Endpoints


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_referral(
    request: CreateReferralRequest,
    service: ReferralService = Depends(get_referral_service),
):
    """
    Create a new referral.

    Returns the referral code and details.
    """
    try:
        referral = await service.create_referral(
            referrer_id=request.referrer_id,
            referee_email=request.referee_email,
            referee_name=request.referee_name,
            referee_phone=request.referee_phone,
            reward_amount=request.reward_amount,
            reward_type=request.reward_type,
        )
        return {"success": True, "data": referral}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/conversions", status_code=status.HTTP_200_OK)
async def track_conversion(
    request: TrackConversionRequest,
    service: ReferralService = Depends(get_referral_service),
):
    """
    Track a referral conversion.

    Called when a referred customer completes a qualifying action.
    """
    try:
        result = await service.track_conversion(
            referral_code=request.referral_code,
            referee_id=request.referee_id,
            conversion_value=request.conversion_value,
            conversion_type=request.conversion_type,
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{referrer_id}/stats")
async def get_referral_stats(
    referrer_id: int,
    service: ReferralService = Depends(get_referral_service),
):
    """
    Get referral statistics for a referrer.

    Returns total referrals, conversions, and earnings.
    """
    try:
        stats = await service.get_referral_stats(referrer_id)
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/credits", status_code=status.HTTP_200_OK)
async def award_credit(
    request: AwardCreditRequest,
    service: ReferralService = Depends(get_referral_service),
):
    """
    Award referral credit to a referrer.

    Used for manual credit adjustments or special rewards.
    """
    try:
        result = await service.award_referral_credit(
            referrer_id=request.referrer_id,
            amount=request.amount,
            reason=request.reason,
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "referrals"}
