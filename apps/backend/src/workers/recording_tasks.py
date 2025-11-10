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
from core.database import get_db_session
from models.call_recording import CallRecording, RecordingStatus
from services.ringcentral_service import get_ringcentral_service

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
        if "processing" not in recording.metadata:
            recording.metadata["processing"] = {}

        recording.metadata["processing"]["processed_at"] = datetime.utcnow().isoformat()
        recording.metadata["processing"]["status"] = "pending"

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
