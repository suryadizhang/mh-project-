"""
Voice Webhooks Router
Handles RingCentral voice call webhooks
"""

import logging
from typing import Any

from api.deps_enhanced import get_database_session
from fastapi import APIRouter, Depends, HTTPException, Request, status
from services.ringcentral_voice_service import voice_service
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ringcentral/voice/inbound")
async def handle_inbound_call_webhook(
    request: Request,
    db: Session = Depends(get_database_session),
):
    """
    Handle inbound call webhook from RingCentral.

    This endpoint receives webhooks when a call comes in.
    """
    try:
        payload = await request.json()
        logger.info(f"Inbound call webhook received: {payload}")

        # Extract call data
        call_data = payload.get("body", {})

        # Handle the call
        result = await voice_service.handle_inbound_call(db, call_data)

        return result

    except Exception as e:
        logger.exception(f"Error handling inbound call webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}",
        )


@router.post("/ringcentral/voice/status")
async def handle_call_status_webhook(
    request: Request,
    db: Session = Depends(get_database_session),
):
    """
    Handle call status update webhook from RingCentral.

    This endpoint receives webhooks when call status changes.
    """
    try:
        payload = await request.json()
        logger.info(f"Call status webhook received: {payload}")

        # Extract status data
        status_data = payload.get("body", {})

        # Handle the status update
        result = await voice_service.handle_call_status(db, status_data)

        return result

    except Exception as e:
        logger.exception(f"Error handling call status webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}",
        )


@router.post("/ringcentral/voice/recording")
async def handle_recording_webhook(
    request: Request,
    db: Session = Depends(get_database_session),
):
    """
    Handle recording ready webhook from RingCentral.

    This endpoint receives webhooks when call recording is ready.
    """
    try:
        payload = await request.json()
        logger.info(f"Recording webhook received: {payload}")

        # Extract recording data
        recording_data = payload.get("body", {})

        # Handle the recording
        result = await voice_service.handle_recording_ready(db, recording_data)

        return result

    except Exception as e:
        logger.exception(f"Error handling recording webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}",
        )


@router.get("/ringcentral/voice/active")
async def get_active_calls():
    """
    Get list of currently active voice calls.

    Returns:
        List of active call data
    """
    try:
        active_calls = voice_service.get_active_calls()

        return {
            "success": True,
            "active_calls": active_calls,
            "count": len(active_calls),
        }

    except Exception as e:
        logger.exception(f"Error getting active calls: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active calls: {str(e)}",
        )


@router.get("/ringcentral/voice/analytics")
async def get_call_analytics(
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_database_session),
):
    """
    Get call analytics for a date range.

    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)

    Returns:
        Call analytics data
    """
    try:
        from datetime import datetime

        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        analytics = await voice_service.get_call_analytics(db, start, end)

        return {"success": True, "analytics": analytics}

    except Exception as e:
        logger.exception(f"Error getting call analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}",
        )
