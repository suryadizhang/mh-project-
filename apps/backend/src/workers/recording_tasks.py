"""
Call Recording Worker Tasks
Background jobs for downloading, storing, and managing call recordings
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session
from workers.celery_config import celery_app
from core.database import get_db_session, get_async_session

# MIGRATED: from models.call_recording → db.models.call_recording
from db.models.support_communications import CallRecording, RecordingStatus
from services.ringcentral_service import get_ringcentral_service
from services.recording_linking_service import RecordingLinkingService

logger = logging.getLogger(__name__)


# VPS filesystem path for recordings (instead of S3)
RECORDINGS_BASE_PATH = os.getenv("RECORDINGS_STORAGE_PATH", "/var/www/vhosts/myhibachi/recordings")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def fetch_call_recording(self, recording_id: str):
    """
    Download call recording from RingCentral and store on VPS filesystem

    Args:
        recording_id: CallRecording model ID (UUID)

    Retries: 3 times with 2 minute delay
    """
    db: Session = next(get_db_session())

    try:
        # Get recording record
        recording = db.query(CallRecording).filter(CallRecording.id == recording_id).first()

        if not recording:
            logger.error(f"Recording {recording_id} not found")
            return {"status": "error", "message": "Recording not found"}

        # Update status to downloading
        recording.status = RecordingStatus.DOWNLOADING
        recording.download_attempts += 1
        db.commit()

        # Get RingCentral service
        rc_service = get_ringcentral_service()

        if not rc_service.is_configured():
            raise RuntimeError("RingCentral not configured")

        # Fetch recording metadata first
        metadata = rc_service.get_recording_metadata(recording.rc_recording_id)
        recording.duration_seconds = metadata.get("duration", 0)
        recording.content_type = metadata.get("content_type", "audio/mpeg")

        # Download recording content
        logger.info(f"Downloading recording {recording.rc_recording_id} from RingCentral")
        content = rc_service.get_recording(recording.rc_recording_id)

        # Create directory structure: /recordings/YYYY/MM/
        date_path = recording.call_started_at.strftime("%Y/%m")
        storage_dir = Path(RECORDINGS_BASE_PATH) / date_path
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename: recording_<id>_<timestamp>.<ext>
        ext = "mp3" if "mpeg" in recording.content_type else "wav"
        filename = (
            f"recording_{recording.id}_{recording.call_started_at.strftime('%Y%m%d_%H%M%S')}.{ext}"
        )
        file_path = storage_dir / filename

        # Save to filesystem
        with open(file_path, "wb") as f:
            f.write(content)

        recording.file_size_bytes = len(content)

        # Update recording record with filesystem path
        recording.s3_bucket = None  # Not using S3
        recording.s3_key = f"{date_path}/{filename}"  # Store relative path
        recording.s3_uri = f"file://{file_path}"  # Local filesystem URI
        recording.status = RecordingStatus.AVAILABLE
        recording.downloaded_at = datetime.utcnow()

        # Set retention policy
        recording.set_retention_policy()

        db.commit()

        logger.info(
            f"Recording {recording_id} downloaded successfully, "
            f"size: {recording.file_size_bytes} bytes, "
            f"path: {file_path}"
        )

        return {
            "status": "success",
            "recording_id": recording_id,
            "file_size": recording.file_size_bytes,
            "file_path": str(file_path),
            "duration": recording.duration_seconds,
        }

    except Exception as e:
        logger.error(f"Failed to download recording {recording_id}: {str(e)}")

        # Update recording error status
        try:
            recording.status = RecordingStatus.ERROR
            recording.error_message = str(e)
            db.commit()
        except Exception:
            pass

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=120 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=180)
def fetch_recording_transcript(self, recording_id: str, call_session_id: str):
    """
    Fetch AI transcript from RingCentral for a call recording.

    Uses RingCentral AI Insights API to get:
    - Full transcript with timestamps
    - Speaker separation
    - Confidence scores
    - AI insights (sentiment, topics, action items)

    Args:
        recording_id: CallRecording model ID (UUID)
        call_session_id: RingCentral call session ID for transcript API

    Retries: 3 times with 3 minute delay (transcription may take time)
    """
    db: Session = next(get_db_session())

    try:
        # Get recording record
        recording = db.query(CallRecording).filter(CallRecording.id == recording_id).first()

        if not recording:
            logger.error(f"Recording {recording_id} not found")
            return {"status": "error", "message": "Recording not found"}

        # Get RingCentral service
        rc_service = get_ringcentral_service()

        if not rc_service.is_configured():
            raise RuntimeError("RingCentral not configured")

        logger.info(f"Fetching transcript for call {call_session_id}")

        # Fetch transcript from RingCentral AI
        transcript_data = rc_service.get_call_transcript(call_session_id)

        # Check if transcript is available
        if not transcript_data.get("full_text"):
            # Transcript not ready yet, retry
            if "error" in transcript_data:
                logger.warning(
                    f"Transcript not ready for {call_session_id}: {transcript_data['error']}"
                )
                raise RuntimeError("Transcript not ready, will retry")
            else:
                logger.info(f"No transcript available for {call_session_id}")

        # Save transcript to database
        recording.rc_transcript = transcript_data.get("full_text", "")
        recording.rc_transcript_confidence = transcript_data.get("confidence", 0)
        recording.rc_transcript_fetched_at = datetime.utcnow()
        recording.rc_ai_insights = transcript_data.get("insights", {})

        db.commit()

        logger.info(
            f"Transcript saved for recording {recording_id}: "
            f"{len(recording.rc_transcript)} chars, "
            f"{recording.rc_transcript_confidence}% confidence"
        )

        return {
            "status": "success",
            "recording_id": recording_id,
            "transcript_length": len(recording.rc_transcript),
            "confidence": recording.rc_transcript_confidence,
            "has_insights": bool(recording.rc_ai_insights),
        }

    except Exception as e:
        logger.error(f"Failed to fetch transcript for {recording_id}: {str(e)}")

        # Retry if not last attempt
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying transcript fetch (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=180 * (2**self.request.retries))
        else:
            logger.error(f"All transcript fetch retries exhausted for {recording_id}")
            return {
                "status": "error",
                "recording_id": recording_id,
                "message": str(e),
            }

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2)
def link_recording_entities(self, recording_id: str):
    """
    Link call recording to customer and booking entities.

    Automatically runs after transcript fetch completes.
    Links recording to:
    1. Customer - by matching phone numbers (from_phone/to_phone)
    2. Booking - by correlating call timing with booking dates

    Args:
        recording_id: CallRecording model ID (UUID)

    Retries: 2 times with exponential backoff

    Returns:
        dict with linking results
    """
    import asyncio
    from uuid import UUID

    async def async_link():
        """Async wrapper for linking service"""
        async for db in get_async_session():
            try:
                linking_service = RecordingLinkingService(db)
                result = await linking_service.link_recording(UUID(recording_id))
                return result
            finally:
                await db.close()

    try:
        logger.info(f"Starting entity linking for recording {recording_id}")

        # Run async linking in event loop
        result = asyncio.run(async_link())

        if result.get("error"):
            logger.error(f"Entity linking failed for {recording_id}: {result['error']}")

            # Retry on error
            if self.request.retries < self.max_retries:
                raise self.retry(
                    exc=Exception(result["error"]), countdown=60 * (2**self.request.retries)
                )
        else:
            logger.info(
                f"Entity linking complete for {recording_id}: "
                f"customer={'linked' if result['customer_linked'] else 'not found'}, "
                f"booking={'linked' if result['booking_linked'] else 'not found'}"
            )

        return result

    except Exception as e:
        logger.error(
            f"Failed to link recording entities for {recording_id}: {str(e)}", exc_info=True
        )

        # Retry if not last attempt
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2**self.request.retries))
        else:
            return {
                "recording_id": recording_id,
                "customer_linked": False,
                "booking_linked": False,
                "error": str(e),
            }


@celery_app.task
def cleanup_expired_recordings():
    """
    Periodic task to clean up recordings that have passed their retention period

    Runs hourly via Celery Beat
    Deletes recording files and updates database records
    """
    db: Session = next(get_db_session())

    try:
        # Find expired recordings
        now = datetime.utcnow()
        expired_recordings = (
            db.query(CallRecording)
            .filter(
                CallRecording.delete_after.isnot(None),
                CallRecording.delete_after <= now,
                CallRecording.status != RecordingStatus.DELETED,
            )
            .all()
        )

        if not expired_recordings:
            logger.info("No expired recordings to clean up")
            return {"status": "success", "deleted": 0}

        deleted_count = 0
        deleted_bytes = 0

        for recording in expired_recordings:
            try:
                # Delete file from filesystem
                if recording.s3_key:
                    file_path = Path(RECORDINGS_BASE_PATH) / recording.s3_key

                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        deleted_bytes += file_size
                        logger.info(f"Deleted recording file: {file_path}")

                # Update database record
                recording.status = RecordingStatus.DELETED
                recording.deleted_at = now
                recording.s3_uri = None  # Clear file reference

                deleted_count += 1

            except Exception as e:
                logger.error(f"Failed to delete recording {recording.id}: {str(e)}")
                continue

        db.commit()

        logger.info(
            f"Cleaned up {deleted_count} expired recordings, "
            f"freed {deleted_bytes / 1024 / 1024:.2f} MB"
        )

        return {
            "status": "success",
            "deleted": deleted_count,
            "bytes_freed": deleted_bytes,
        }

    except Exception as e:
        logger.error(f"Failed to cleanup expired recordings: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


@celery_app.task
def process_recording_metadata(recording_id: str):
    """
    Process and index recording metadata for search and analytics

    Args:
        recording_id: CallRecording model ID

    TODO: Implement:
    - Speech-to-text transcription
    - Sentiment analysis
    - Keyword extraction
    - Add to search index
    """
    db: Session = next(get_db_session())

    try:
        recording = db.query(CallRecording).filter(CallRecording.id == recording_id).first()

        if not recording:
            logger.error(f"Recording {recording_id} not found")
            return {"status": "error", "message": "Recording not found"}

        # Placeholder for future processing
        logger.info(f"Processing metadata for recording {recording_id}")

        # Add processing metadata
        if "processing" not in recording.recording_metadata:
            recording.recording_metadata["processing"] = {}

        recording.recording_metadata["processing"]["processed_at"] = datetime.utcnow().isoformat()
        recording.recording_metadata["processing"]["status"] = "pending"

        db.commit()

        return {
            "status": "success",
            "recording_id": recording_id,
            "message": "Metadata processing queued",
        }

    except Exception as e:
        logger.error(f"Failed to process recording metadata: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


@celery_app.task
def archive_old_recordings():
    """
    Periodic task to move old recordings to cold storage

    Runs daily via Celery Beat
    Moves recordings older than 30 days to archive directory
    """
    db: Session = next(get_db_session())

    try:
        # Find recordings older than 30 days that are not archived
        archive_threshold = datetime.utcnow() - timedelta(days=30)

        old_recordings = (
            db.query(CallRecording)
            .filter(
                CallRecording.call_started_at < archive_threshold,
                CallRecording.status == RecordingStatus.AVAILABLE,
            )
            .all()
        )

        if not old_recordings:
            logger.info("No recordings to archive")
            return {"status": "success", "archived": 0}

        archived_count = 0
        archive_dir = Path(RECORDINGS_BASE_PATH) / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        for recording in old_recordings:
            try:
                if not recording.s3_key:
                    continue

                current_path = Path(RECORDINGS_BASE_PATH) / recording.s3_key

                if not current_path.exists():
                    logger.warning(f"Recording file not found: {current_path}")
                    continue

                # Move to archive directory
                archive_path = archive_dir / current_path.name
                current_path.rename(archive_path)

                # Update database
                recording.status = RecordingStatus.ARCHIVED
                recording.archived_at = datetime.utcnow()
                recording.s3_key = f"archive/{current_path.name}"
                recording.s3_uri = f"file://{archive_path}"

                archived_count += 1

            except Exception as e:
                logger.error(f"Failed to archive recording {recording.id}: {str(e)}")
                continue

        db.commit()

        logger.info(f"Archived {archived_count} recordings")

        return {"status": "success", "archived": archived_count}

    except Exception as e:
        logger.error(f"Failed to archive recordings: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()
