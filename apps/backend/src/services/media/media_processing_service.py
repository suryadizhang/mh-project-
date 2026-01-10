"""
Media Processing Service
========================

Handles image and video processing for review uploads.

Processing Pipeline:
    1. Image Processing (Pillow + ImageMagick fallback):
       - Resize to max dimensions
       - Compress for web (WebP preferred)
       - Generate thumbnails
       - HEIC conversion via ImageMagick

    2. Video Processing (FFmpeg):
       - Transcode to H.264/MP4
       - Generate thumbnail from first frame
       - Compress for web streaming

Dependencies:
    - Pillow: pip install Pillow
    - ImageMagick: system package (for HEIC)
    - FFmpeg: system package (for video)

Usage:
    processor = MediaProcessingService()

    # Process an image
    result = await processor.process_image(
        image_bytes=uploaded_file,
        original_filename="photo.heic"
    )
    # Returns: {"optimized": bytes, "thumbnail": bytes, "format": "webp"}

    # Process a video
    result = await processor.process_video(
        video_bytes=uploaded_file,
        original_filename="video.mov"
    )
    # Returns: {"optimized": bytes, "thumbnail": bytes, "format": "mp4"}
"""

import asyncio
import io
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)

# Image settings
MAX_IMAGE_WIDTH = 1920
MAX_IMAGE_HEIGHT = 1080
THUMBNAIL_SIZE = (300, 300)
IMAGE_QUALITY = 85
WEBP_QUALITY = 80

# Video settings
MAX_VIDEO_WIDTH = 1280
MAX_VIDEO_HEIGHT = 720
VIDEO_BITRATE = "2M"
AUDIO_BITRATE = "128k"

# Allowed MIME types
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/heic",
    "image/heif",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/quicktime",  # .mov
    "video/x-msvideo",  # .avi
    "video/webm",
    "video/x-m4v",
}

# File size limits (bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB


class MediaProcessingError(Exception):
    """Exception raised when media processing fails."""

    pass


class MediaProcessingService:
    """
    Processes images and videos for web optimization.

    Features:
    - Image resizing and compression
    - WebP conversion for smaller file sizes
    - HEIC/HEIF support via ImageMagick
    - Video transcoding to H.264/MP4
    - Thumbnail generation for both images and videos
    """

    def __init__(self):
        """Initialize media processing service."""
        self._pillow_available = self._check_pillow()
        self._imagemagick_available = self._check_imagemagick()
        self._ffmpeg_available = self._check_ffmpeg()

        if not self._pillow_available:
            logger.warning("Pillow not available. Image processing will be limited.")

        if not self._imagemagick_available:
            logger.warning("ImageMagick not available. HEIC conversion disabled.")

        if not self._ffmpeg_available:
            logger.warning("FFmpeg not available. Video processing disabled.")

    @staticmethod
    def _check_pillow() -> bool:
        """Check if Pillow is available."""
        try:
            from PIL import Image

            return True
        except ImportError:
            return False

    @staticmethod
    def _check_imagemagick() -> bool:
        """Check if ImageMagick is available."""
        try:
            result = subprocess.run(["convert", "-version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def _check_ffmpeg() -> bool:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def validate_image(self, content_type: str, file_size: int) -> Tuple[bool, str]:
        """
        Validate an image file.

        Args:
            content_type: MIME type
            file_size: Size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        if content_type not in ALLOWED_IMAGE_TYPES:
            return False, f"Unsupported image type: {content_type}"

        if file_size > MAX_IMAGE_SIZE:
            return False, f"Image too large. Max size: {MAX_IMAGE_SIZE // (1024*1024)}MB"

        return True, ""

    def validate_video(self, content_type: str, file_size: int) -> Tuple[bool, str]:
        """
        Validate a video file.

        Args:
            content_type: MIME type
            file_size: Size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        if content_type not in ALLOWED_VIDEO_TYPES:
            return False, f"Unsupported video type: {content_type}"

        if file_size > MAX_VIDEO_SIZE:
            return False, f"Video too large. Max size: {MAX_VIDEO_SIZE // (1024*1024)}MB"

        return True, ""

    async def process_image(
        self,
        image_bytes: bytes,
        original_filename: str,
        content_type: str = "image/jpeg",
    ) -> dict:
        """
        Process an image for web optimization.

        Steps:
        1. Convert HEIC to JPEG if needed (via ImageMagick)
        2. Resize to max dimensions
        3. Convert to WebP for compression
        4. Generate thumbnail

        Args:
            image_bytes: Raw image data
            original_filename: Original filename for type detection
            content_type: MIME type

        Returns:
            Dict with optimized bytes, thumbnail bytes, and format info

        Raises:
            MediaProcessingError: If processing fails
        """
        if not self._pillow_available:
            raise MediaProcessingError("Pillow not available for image processing")

        from PIL import Image, ImageOps

        try:
            # Check if HEIC and convert first
            if content_type in ("image/heic", "image/heif") or original_filename.lower().endswith(
                (".heic", ".heif")
            ):
                if not self._imagemagick_available:
                    raise MediaProcessingError("HEIC conversion requires ImageMagick")

                image_bytes = await self._convert_heic_to_jpeg(image_bytes)

            # Open image with Pillow
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if needed (for PNG with alpha, etc.)
            if image.mode in ("RGBA", "P"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "RGBA":
                    background.paste(image, mask=image.split()[3])
                else:
                    background.paste(image)
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")

            # Auto-orient based on EXIF
            image = ImageOps.exif_transpose(image)

            # Resize if larger than max dimensions
            if image.width > MAX_IMAGE_WIDTH or image.height > MAX_IMAGE_HEIGHT:
                image.thumbnail((MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT), Image.Resampling.LANCZOS)

            # Create optimized version (WebP)
            optimized_buffer = io.BytesIO()
            image.save(
                optimized_buffer,
                format="WEBP",
                quality=WEBP_QUALITY,
                method=4,  # Compression effort (0-6, higher = smaller but slower)
            )
            optimized_bytes = optimized_buffer.getvalue()

            # Create thumbnail
            thumbnail = image.copy()
            thumbnail.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

            thumbnail_buffer = io.BytesIO()
            thumbnail.save(
                thumbnail_buffer,
                format="WEBP",
                quality=75,
            )
            thumbnail_bytes = thumbnail_buffer.getvalue()

            logger.info(
                f"Processed image: {original_filename} "
                f"({len(image_bytes)} -> {len(optimized_bytes)} bytes)"
            )

            return {
                "optimized": optimized_bytes,
                "thumbnail": thumbnail_bytes,
                "format": "webp",
                "content_type": "image/webp",
                "width": image.width,
                "height": image.height,
                "thumbnail_width": thumbnail.width,
                "thumbnail_height": thumbnail.height,
            }

        except MediaProcessingError:
            raise
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise MediaProcessingError(f"Failed to process image: {str(e)}")

    async def _convert_heic_to_jpeg(self, heic_bytes: bytes) -> bytes:
        """
        Convert HEIC image to JPEG using ImageMagick.

        Args:
            heic_bytes: HEIC image data

        Returns:
            JPEG image data
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            heic_path = Path(temp_dir) / "input.heic"
            jpeg_path = Path(temp_dir) / "output.jpg"

            # Write HEIC file
            heic_path.write_bytes(heic_bytes)

            # Convert with ImageMagick
            process = await asyncio.create_subprocess_exec(
                "convert",
                str(heic_path),
                "-quality",
                "90",
                str(jpeg_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            _, stderr = await process.communicate()

            if process.returncode != 0:
                raise MediaProcessingError(f"HEIC conversion failed: {stderr.decode()}")

            return jpeg_path.read_bytes()

    async def process_video(
        self,
        video_bytes: bytes,
        original_filename: str,
        content_type: str = "video/mp4",
    ) -> dict:
        """
        Process a video for web streaming.

        Steps:
        1. Transcode to H.264/MP4
        2. Resize to max dimensions
        3. Optimize for streaming (faststart)
        4. Generate thumbnail from first frame

        Args:
            video_bytes: Raw video data
            original_filename: Original filename
            content_type: MIME type

        Returns:
            Dict with optimized bytes, thumbnail bytes, and format info

        Raises:
            MediaProcessingError: If processing fails
        """
        if not self._ffmpeg_available:
            raise MediaProcessingError("FFmpeg not available for video processing")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            input_path = temp_dir / f"input{Path(original_filename).suffix}"
            output_path = temp_dir / "output.mp4"
            thumbnail_path = temp_dir / "thumbnail.jpg"

            try:
                # Write input file
                input_path.write_bytes(video_bytes)

                # Transcode video with FFmpeg
                transcode_cmd = [
                    "ffmpeg",
                    "-i",
                    str(input_path),
                    "-c:v",
                    "libx264",
                    "-preset",
                    "medium",
                    "-crf",
                    "23",
                    "-c:a",
                    "aac",
                    "-b:a",
                    AUDIO_BITRATE,
                    "-vf",
                    f"scale='min({MAX_VIDEO_WIDTH},iw)':min'({MAX_VIDEO_HEIGHT},ih)':force_original_aspect_ratio=decrease",
                    "-movflags",
                    "+faststart",  # Enable streaming
                    "-y",  # Overwrite output
                    str(output_path),
                ]

                process = await asyncio.create_subprocess_exec(
                    *transcode_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                _, stderr = await process.communicate()

                if process.returncode != 0:
                    logger.error(f"FFmpeg transcode failed: {stderr.decode()}")
                    raise MediaProcessingError("Video transcoding failed")

                # Generate thumbnail from first frame
                thumbnail_cmd = [
                    "ffmpeg",
                    "-i",
                    str(output_path),
                    "-vframes",
                    "1",
                    "-q:v",
                    "2",
                    "-y",
                    str(thumbnail_path),
                ]

                process = await asyncio.create_subprocess_exec(
                    *thumbnail_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                await process.communicate()

                # Read output files
                optimized_bytes = output_path.read_bytes()

                thumbnail_bytes = None
                if thumbnail_path.exists():
                    # Convert thumbnail to WebP if Pillow available
                    if self._pillow_available:
                        from PIL import Image

                        thumb_img = Image.open(thumbnail_path)
                        thumb_img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                        thumb_buffer = io.BytesIO()
                        thumb_img.save(thumb_buffer, format="WEBP", quality=75)
                        thumbnail_bytes = thumb_buffer.getvalue()
                        thumbnail_format = "webp"
                    else:
                        thumbnail_bytes = thumbnail_path.read_bytes()
                        thumbnail_format = "jpeg"

                logger.info(
                    f"Processed video: {original_filename} "
                    f"({len(video_bytes)} -> {len(optimized_bytes)} bytes)"
                )

                return {
                    "optimized": optimized_bytes,
                    "thumbnail": thumbnail_bytes,
                    "format": "mp4",
                    "content_type": "video/mp4",
                    "thumbnail_format": thumbnail_format if thumbnail_bytes else None,
                }

            except MediaProcessingError:
                raise
            except Exception as e:
                logger.error(f"Video processing failed: {e}")
                raise MediaProcessingError(f"Failed to process video: {str(e)}")

    async def process_media(
        self,
        file_bytes: bytes,
        original_filename: str,
        content_type: str,
    ) -> dict:
        """
        Process any media file (image or video).

        Automatically detects media type and routes to appropriate processor.

        Args:
            file_bytes: Raw file data
            original_filename: Original filename
            content_type: MIME type

        Returns:
            Dict with optimized bytes, thumbnail bytes, and format info
        """
        if content_type in ALLOWED_IMAGE_TYPES or any(
            original_filename.lower().endswith(ext)
            for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif")
        ):
            return await self.process_image(file_bytes, original_filename, content_type)

        elif content_type in ALLOWED_VIDEO_TYPES or any(
            original_filename.lower().endswith(ext)
            for ext in (".mp4", ".mov", ".avi", ".webm", ".m4v")
        ):
            return await self.process_video(file_bytes, original_filename, content_type)

        else:
            raise MediaProcessingError(f"Unsupported media type: {content_type}")

    def get_capabilities(self) -> dict:
        """Get available processing capabilities."""
        return {
            "pillow_available": self._pillow_available,
            "imagemagick_available": self._imagemagick_available,
            "ffmpeg_available": self._ffmpeg_available,
            "supported_image_types": list(ALLOWED_IMAGE_TYPES),
            "supported_video_types": list(ALLOWED_VIDEO_TYPES),
            "max_image_size_mb": MAX_IMAGE_SIZE // (1024 * 1024),
            "max_video_size_mb": MAX_VIDEO_SIZE // (1024 * 1024),
        }
