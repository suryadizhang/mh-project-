"""
Media Services Package
======================

Provides media upload, storage, and processing capabilities for the My Hibachi platform.

Storage: Cloudflare R2 (S3-compatible, zero egress fees)
Image Processing: Pillow + ImageMagick fallback (for HEIC)
Video Processing: FFmpeg
Processing Mode: Async background tasks

Usage:
    from services.media import R2StorageService, MediaProcessingService

    # Upload a file
    storage = R2StorageService()
    url = await storage.upload_file(file_bytes, "reviews/2025/01/123/image.jpg", "image/jpeg")

    # Process an image
    processor = MediaProcessingService()
    optimized, thumbnail = await processor.process_image(file_bytes, "image.jpg")
"""

from .r2_storage_service import R2StorageService
from .media_processing_service import MediaProcessingService, MediaProcessingError

__all__ = ["R2StorageService", "MediaProcessingService", "MediaProcessingError"]
