"""
Call Recordings API Router
Provides endpoints for accessing call recordings and transcripts
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import get_db
from models.call_recording import CallRecording, RecordingStatus
from services.ringcentral_service import get_ringcentral_service
from api.deps import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recordings", tags=["recordings"])


@router.get("/{recording_id}")
async def get_recording(
    recording_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin_user),
):
    """
    Get call recording metadata and transcript.
    
    Returns:
        - Recording metadata (duration, timestamps, status)
        - RingCentral AI transcript (if available)
        - AI insights (sentiment, topics, action items)
    """
    try:
        result = await db.execute(
            select(CallRecording).where(CallRecording.id == recording_id)
        )
        recording = result.scalar_one_or_none()
        
        if not recording:
            raise HTTPException(status_code=404, detail="Recording not found")
        
        return {
            "id": str(recording.id),
            "rc_call_id": recording.rc_call_id,
            "rc_recording_id": recording.rc_recording_id,
            "status": recording.status.value,
            "duration_seconds": recording.duration_seconds,
            "recorded_at": recording.recorded_at.isoformat() if recording.recorded_at else None,
            "transcript": {
                "text": recording.rc_transcript,
                "confidence": recording.rc_transcript_confidence,
                "fetched_at": recording.rc_transcript_fetched_at.isoformat() 
                    if recording.rc_transcript_fetched_at else None,
            },
            "ai_insights": recording.rc_ai_insights or {},
            "metadata": {
                "content_type": recording.content_type,
                "file_size_bytes": recording.file_size_bytes,
                "created_at": recording.created_at.isoformat(),
                "updated_at": recording.updated_at.isoformat(),
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch recording {recording_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recording")


@router.get("/{recording_id}/stream")
async def stream_recording(
    recording_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin_user),
):
    """
    Get streaming URL for call recording audio.
    
    Returns redirect to RingCentral's CDN with time-limited auth token.
    No download needed - stream directly from RingCentral.
    """
    try:
        result = await db.execute(
            select(CallRecording).where(CallRecording.id == recording_id)
        )
        recording = result.scalar_one_or_none()
        
        if not recording:
            raise HTTPException(status_code=404, detail="Recording not found")
        
        if not recording.rc_recording_id:
            raise HTTPException(
                status_code=400, 
                detail="Recording not available in RingCentral"
            )
        
        # Get streaming URL from RingCentral
        rc_service = get_ringcentral_service()
        stream_url = rc_service.get_recording_stream_url(recording.rc_recording_id)
        
        # Redirect to RingCentral CDN
        return RedirectResponse(url=stream_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stream URL for {recording_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get stream URL")


@router.get("/")
async def search_recordings(
    phone_number: Optional[str] = Query(None, description="Filter by phone number"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    search_text: Optional[str] = Query(None, description="Search in transcript"),
    has_transcript: Optional[bool] = Query(None, description="Filter by transcript availability"),
    status: Optional[RecordingStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin_user),
):
    """
    Search call recordings with filters.
    
    Supports filtering by:
    - Phone number
    - Date range
    - Transcript content (full-text search)
    - Transcript availability
    - Recording status
    """
    try:
        # Build query
        query = select(CallRecording)
        
        # Apply filters
        if phone_number:
            # Need to join with related tables to filter by phone
            # For now, filter by RC call ID (which may contain phone info)
            query = query.where(
                or_(
                    CallRecording.rc_call_id.contains(phone_number),
                    CallRecording.phone_number == phone_number,
                )
            )
        
        if start_date:
            query = query.where(CallRecording.recorded_at >= start_date)
        
        if end_date:
            query = query.where(CallRecording.recorded_at <= end_date)
        
        if search_text:
            # PostgreSQL full-text search on transcript
            query = query.where(CallRecording.rc_transcript.ilike(f"%{search_text}%"))
        
        if has_transcript is not None:
            if has_transcript:
                query = query.where(CallRecording.rc_transcript.isnot(None))
            else:
                query = query.where(CallRecording.rc_transcript.is_(None))
        
        if status:
            query = query.where(CallRecording.status == status)
        
        # Apply ordering (newest first)
        query = query.order_by(CallRecording.recorded_at.desc())
        
        # Get total count
        count_query = select(select(CallRecording).count())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute query
        result = await db.execute(query)
        recordings = result.scalars().all()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "recordings": [
                {
                    "id": str(rec.id),
                    "rc_call_id": rec.rc_call_id,
                    "status": rec.status.value,
                    "duration_seconds": rec.duration_seconds,
                    "recorded_at": rec.recorded_at.isoformat() if rec.recorded_at else None,
                    "has_transcript": bool(rec.rc_transcript),
                    "transcript_preview": (
                        rec.rc_transcript[:200] + "..." 
                        if rec.rc_transcript and len(rec.rc_transcript) > 200 
                        else rec.rc_transcript
                    ),
                    "confidence": rec.rc_transcript_confidence,
                    "ai_insights_summary": {
                        "sentiment": rec.rc_ai_insights.get("sentiment", {}) if rec.rc_ai_insights else {},
                        "topics": (rec.rc_ai_insights.get("topics", []) if rec.rc_ai_insights else [])[:3],
                        "has_action_items": bool(
                            rec.rc_ai_insights.get("action_items") if rec.rc_ai_insights else False
                        ),
                    },
                }
                for rec in recordings
            ],
        }
        
    except Exception as e:
        logger.error(f"Failed to search recordings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search recordings")
