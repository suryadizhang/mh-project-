"""
Image Upload Service - Using Cloudinary (FREE tier)

Features:
- Upload images to Cloudinary
- Auto-optimization (resize, compress, format conversion)
- Thumbnail generation
- Free CDN delivery
- 25GB storage + 25GB bandwidth/month (FREE)

Setup:
1. Sign up at cloudinary.com (free)
2. Get your credentials from dashboard
3. Add to .env:
   CLOUDINARY_CLOUD_NAME=your-cloud-name
   CLOUDINARY_API_KEY=your-api-key
   CLOUDINARY_API_SECRET=your-api-secret

Install: pip install cloudinary pillow
"""

import io
import os
from pathlib import Path
import uuid

# Cloudinary
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# FastAPI
from fastapi import HTTPException, UploadFile

# Image processing
from PIL import Image


class ImageService:
    """
    Image upload and processing service using Cloudinary

    Free tier includes:
    - 25GB storage
    - 25GB bandwidth/month
    - Auto image optimization
    - Global CDN delivery
    """

    def __init__(self):
        # Configure Cloudinary from environment
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
            secure=True,
        )

        self.max_image_size = 10 * 1024 * 1024  # 10MB for images
        self.max_video_size = 100 * 1024 * 1024  # 100MB for videos
        self.allowed_image_formats = {"jpg", "jpeg", "png", "webp", "gif"}
        self.allowed_video_formats = {"mp4", "mov", "webm", "avi"}

    async def upload_review_images(
        self,
        media_files: list[UploadFile],  # Changed: supports images + videos
        review_id: int | None = None,
    ) -> list[dict[str, str]]:
        """
        Upload multiple media files (images + videos) for a review

        Args:
            media_files: List of uploaded files (images AND videos)
            review_id: Optional review ID for organization

        Returns:
            List of dicts with media URLs, thumbnails, and metadata
        """
        uploaded_media = []

        for idx, media_file in enumerate(media_files):
            try:
                # Detect if image or video
                is_video = self._is_video(media_file)

                # Validate file
                self._validate_media(media_file, is_video)

                # Read file content
                contents = await media_file.read()

                # Generate unique filename
                filename = f"review_{review_id or 'temp'}_{uuid.uuid4().hex[:8]}_{idx}"

                if is_video:
                    # Upload VIDEO to Cloudinary
                    result = cloudinary.uploader.upload(
                        contents,
                        folder="customer-reviews/videos",
                        public_id=filename,
                        resource_type="video",
                        # Video optimization
                        transformation=[
                            {
                                "width": 1280,
                                "height": 720,
                                "crop": "limit",
                            },  # Max HD
                            {"quality": "auto"},  # Auto quality
                        ],
                        # Generate video thumbnail
                        eager=[
                            {
                                "width": 400,
                                "height": 300,
                                "crop": "fill",
                                "format": "jpg",
                            }
                        ],
                    )

                    # Extract URLs
                    video_url = result["secure_url"]
                    thumbnail_url = (
                        result["eager"][0]["secure_url"]
                        if result.get("eager")
                        else video_url
                    )

                    uploaded_media.append(
                        {
                            "url": video_url,
                            "thumbnail": thumbnail_url,
                            "width": result.get("width", 0),
                            "height": result.get("height", 0),
                            "format": result.get("format", "mp4"),
                            "size": result.get("bytes", 0),
                            "duration": result.get(
                                "duration", 0
                            ),  # Video duration in seconds
                            "resource_type": "video",
                            "public_id": result["public_id"],
                            "filename": media_file.filename,
                        }
                    )

                else:
                    # Upload IMAGE to Cloudinary
                    result = cloudinary.uploader.upload(
                        contents,
                        folder="customer-reviews/images",
                        public_id=filename,
                        resource_type="image",
                        # Auto-optimization
                        transformation=[
                            {
                                "width": 1920,
                                "height": 1920,
                                "crop": "limit",
                            },  # Max size
                            {"quality": "auto:good"},  # Auto quality
                            {
                                "fetch_format": "auto"
                            },  # Auto format (WebP for modern browsers)
                        ],
                        # Generate thumbnail
                        eager=[
                            {
                                "width": 400,
                                "height": 300,
                                "crop": "fill",
                                "gravity": "auto",
                            }
                        ],
                    )

                    # Extract URLs
                    image_url = result["secure_url"]
                    thumbnail_url = (
                        result["eager"][0]["secure_url"]
                        if result.get("eager")
                        else image_url
                    )

                    uploaded_media.append(
                        {
                            "url": image_url,
                            "thumbnail": thumbnail_url,
                            "width": result.get("width", 0),
                            "height": result.get("height", 0),
                            "format": result.get("format", "jpg"),
                            "size": result.get("bytes", 0),
                            "resource_type": "image",
                            "public_id": result["public_id"],
                            "filename": media_file.filename,
                        }
                    )

            except Exception:
                # Continue with other files
                continue

        return uploaded_media

    def _is_video(self, media_file: UploadFile) -> bool:
        """Check if file is a video"""
        if media_file.content_type and media_file.content_type.startswith(
            "video/"
        ):
            return True

        ext = Path(media_file.filename).suffix.lower().strip(".")
        return ext in self.allowed_video_formats

    def _validate_media(self, media_file: UploadFile, is_video: bool):
        """Validate uploaded media file"""
        # Check file type
        if is_video:
            if (
                not media_file.content_type
                or not media_file.content_type.startswith("video/")
            ):
                ext = Path(media_file.filename).suffix.lower().strip(".")
                if ext not in self.allowed_video_formats:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File {media_file.filename} is not a valid video. Use: {', '.join(self.allowed_video_formats)}",
                    )
        else:
            if (
                not media_file.content_type
                or not media_file.content_type.startswith("image/")
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"File {media_file.filename} is not an image",
                )

            # Check file extension
            ext = Path(media_file.filename).suffix.lower().strip(".")
            if ext not in self.allowed_image_formats:
                raise HTTPException(
                    status_code=400,
                    detail=f"Format {ext} not allowed. Use: {', '.join(self.allowed_image_formats)}",
                )

    async def delete_review_images(self, public_ids: list[str]):
        """
        Delete images from Cloudinary

        Args:
            public_ids: List of Cloudinary public IDs to delete
        """
        try:
            for public_id in public_ids:
                cloudinary.uploader.destroy(public_id, resource_type="image")
        except Exception:
            pass

    def get_optimized_url(
        self, public_id: str, width: int = 800, height: int = 600
    ) -> str:
        """
        Get optimized image URL with custom dimensions

        Args:
            public_id: Cloudinary public ID
            width: Desired width
            height: Desired height

        Returns:
            Optimized image URL
        """
        url, options = cloudinary_url(
            public_id,
            width=width,
            height=height,
            crop="fill",
            gravity="auto",
            quality="auto:good",
            fetch_format="auto",
        )
        return url


# Fallback: Local filesystem storage (for development/testing)
class LocalImageService:
    """
    Local filesystem image storage (fallback for development)

    Use this if you don't want to set up Cloudinary yet.
    Images stored in: apps/customer/public/uploads/reviews/
    """

    def __init__(self):
        self.upload_dir = (
            Path(__file__).parent.parent.parent.parent.parent
            / "apps"
            / "customer"
            / "public"
            / "uploads"
            / "reviews"
        )
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_formats = {"jpg", "jpeg", "png", "webp"}

    async def upload_review_images(
        self, images: list[UploadFile], review_id: int | None = None
    ) -> list[dict[str, str]]:
        """Upload images to local filesystem"""
        uploaded_images = []

        for idx, image_file in enumerate(images):
            try:
                # Validate
                self._validate_image(image_file)

                # Read contents
                contents = await image_file.read()

                # Validate size
                if len(contents) > self.max_file_size:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Image {image_file.filename} exceeds 10MB",
                    )

                # Process with PIL
                image = Image.open(io.BytesIO(contents))

                # Generate filenames
                filename = f"review_{review_id or 'temp'}_{uuid.uuid4().hex[:8]}_{idx}.jpg"
                thumb_filename = f"thumb_{filename}"

                # Resize main image (max 1920x1920)
                image.thumbnail((1920, 1920), Image.Resampling.LANCZOS)

                # Save optimized image
                image_path = self.upload_dir / filename
                image.save(image_path, "JPEG", quality=85, optimize=True)

                # Generate thumbnail (400x300)
                thumbnail = image.copy()
                thumbnail.thumbnail((400, 300), Image.Resampling.LANCZOS)
                thumb_path = self.upload_dir / thumb_filename
                thumbnail.save(thumb_path, "JPEG", quality=80, optimize=True)

                # Get URLs (relative to public/)
                base_url = "/uploads/reviews"

                uploaded_images.append(
                    {
                        "url": f"{base_url}/{filename}",
                        "thumbnail": f"{base_url}/{thumb_filename}",
                        "width": image.width,
                        "height": image.height,
                        "format": "jpg",
                        "size": image_path.stat().st_size,
                        "filename": image_file.filename,
                    }
                )

            except Exception:
                continue

        return uploaded_images

    def _validate_image(self, image_file: UploadFile):
        """Validate uploaded image"""
        if (
            not image_file.content_type
            or not image_file.content_type.startswith("image/")
        ):
            raise HTTPException(
                status_code=400,
                detail=f"File {image_file.filename} is not an image",
            )

        ext = Path(image_file.filename).suffix.lower().strip(".")
        if ext not in self.allowed_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Format {ext} not allowed. Use: {', '.join(self.allowed_formats)}",
            )


# Factory function - use Cloudinary if configured, else local
def get_image_service() -> ImageService | LocalImageService:
    """
    Get image service based on environment configuration

    Returns:
        ImageService (Cloudinary) if configured, else LocalImageService
    """
    if os.getenv("CLOUDINARY_CLOUD_NAME"):
        return ImageService()
    else:
        return LocalImageService()
