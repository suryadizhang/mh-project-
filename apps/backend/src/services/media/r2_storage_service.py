"""
Cloudflare R2 Storage Service
=============================

S3-compatible object storage for media files.
Zero egress fees - perfect for serving images/videos to customers.

Environment Variables Required:
    CLOUDFLARE_R2_ACCOUNT_ID: Your R2 account ID
    CLOUDFLARE_R2_ACCESS_KEY_ID: Access key from R2 dashboard
    CLOUDFLARE_R2_SECRET_ACCESS_KEY: Secret key from R2 dashboard
    CLOUDFLARE_R2_BUCKET: Bucket name (default: myhibachi-documents)
    CLOUDFLARE_R2_PUBLIC_URL: Public domain for serving files (optional)

Usage:
    storage = R2StorageService()

    # Upload a file
    url = await storage.upload_file(
        file_bytes=image_bytes,
        path="reviews/2025/01/review-123/image.jpg",
        content_type="image/jpeg"
    )

    # Delete a file
    await storage.delete_file("reviews/2025/01/review-123/image.jpg")

    # Get public URL
    url = storage.get_public_url("reviews/2025/01/review-123/image.jpg")
"""

import logging
import os
from datetime import datetime
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class R2StorageService:
    """
    Cloudflare R2 Storage Service using S3-compatible API.

    Features:
    - S3-compatible uploads/downloads
    - Zero egress fees for serving files
    - Public URL generation
    - Organized path structure by date
    """

    def __init__(self):
        """Initialize R2 storage service with environment configuration."""
        self.account_id = os.getenv("CLOUDFLARE_R2_ACCOUNT_ID")
        self.access_key = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
        self.secret_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        self.bucket = os.getenv("CLOUDFLARE_R2_BUCKET", "myhibachi-documents")
        self.public_url = os.getenv("CLOUDFLARE_R2_PUBLIC_URL", "")

        self._client = None
        self._configured = bool(self.account_id and self.access_key and self.secret_key)

        if not self._configured:
            logger.warning(
                "R2 credentials not configured. Set CLOUDFLARE_R2_ACCOUNT_ID, "
                "CLOUDFLARE_R2_ACCESS_KEY_ID, and CLOUDFLARE_R2_SECRET_ACCESS_KEY"
            )

    @property
    def is_configured(self) -> bool:
        """Check if R2 is properly configured."""
        return self._configured

    def _get_client(self):
        """
        Get or create S3 client for R2.

        Lazily initialized to avoid import errors if boto3 not installed.
        """
        if self._client is not None:
            return self._client

        if not self._configured:
            return None

        try:
            import boto3
            from botocore.config import Config

            self._client = boto3.client(
                "s3",
                endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(signature_version="s3v4"),
            )
            return self._client

        except ImportError:
            logger.error("boto3 not installed. Run: pip install boto3")
            return None
        except Exception as e:
            logger.error(f"Failed to create R2 client: {e}")
            return None

    def get_public_url(self, path: str) -> str:
        """
        Get public URL for a file path.

        Args:
            path: File path in bucket (e.g., "reviews/2025/01/123/image.jpg")

        Returns:
            Full public URL for the file
        """
        if self.public_url:
            return f"{self.public_url.rstrip('/')}/{path}"
        else:
            return f"https://{self.bucket}.{self.account_id}.r2.cloudflarestorage.com/{path}"

    def generate_review_path(
        self, review_id: int | str | UUID, filename: str, subfolder: str = "original"
    ) -> str:
        """
        Generate organized path for review media.

        Path format: reviews/{year}/{month}/{review_id}/{subfolder}/{filename}

        Args:
            review_id: Review ID
            filename: Original filename
            subfolder: Subfolder (original, optimized, thumbnail)

        Returns:
            Full path for the file
        """
        now = datetime.utcnow()

        # Sanitize filename
        safe_filename = "".join(c if c.isalnum() or c in ".-_" else "_" for c in filename)

        return f"reviews/{now.year}/{now.month:02d}/{review_id}/{subfolder}/{safe_filename}"

    async def upload_file(
        self,
        file_bytes: bytes,
        path: str,
        content_type: str = "application/octet-stream",
        cache_control: Optional[str] = None,
    ) -> Optional[str]:
        """
        Upload a file to R2 storage.

        Args:
            file_bytes: File content as bytes
            path: Target path in bucket
            content_type: MIME type of the file
            cache_control: Optional cache control header

        Returns:
            Public URL of uploaded file, or None if upload failed
        """
        client = self._get_client()
        if client is None:
            logger.warning("R2 client not available, cannot upload file")
            return None

        try:
            # Build extra args
            extra_args = {"ContentType": content_type}
            if cache_control:
                extra_args["CacheControl"] = cache_control

            # Upload to R2
            client.put_object(
                Bucket=self.bucket,
                Key=path,
                Body=file_bytes,
                **extra_args,
            )

            url = self.get_public_url(path)
            logger.info(f"Uploaded file to R2: {path} ({len(file_bytes)} bytes)")
            return url

        except Exception as e:
            logger.error(f"Failed to upload file to R2: {e}")
            return None

    async def upload_review_media(
        self,
        file_bytes: bytes,
        review_id: int | str | UUID,
        filename: str,
        content_type: str,
        subfolder: str = "original",
    ) -> Optional[str]:
        """
        Upload review media with organized path structure.

        Args:
            file_bytes: File content
            review_id: Review ID for path organization
            filename: Original filename
            content_type: MIME type
            subfolder: original, optimized, or thumbnail

        Returns:
            Public URL of uploaded file
        """
        path = self.generate_review_path(review_id, filename, subfolder)

        # Set cache headers for media (1 year for immutable content)
        cache_control = "public, max-age=31536000, immutable"

        return await self.upload_file(
            file_bytes=file_bytes,
            path=path,
            content_type=content_type,
            cache_control=cache_control,
        )

    async def delete_file(self, path: str) -> bool:
        """
        Delete a file from R2 storage.

        Args:
            path: File path in bucket

        Returns:
            True if deleted, False otherwise
        """
        client = self._get_client()
        if client is None:
            return False

        try:
            client.delete_object(Bucket=self.bucket, Key=path)
            logger.info(f"Deleted file from R2: {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file from R2: {e}")
            return False

    async def delete_review_media(self, review_id: int | str | UUID) -> int:
        """
        Delete all media for a review.

        Args:
            review_id: Review ID

        Returns:
            Number of files deleted
        """
        client = self._get_client()
        if client is None:
            return 0

        try:
            # List all objects with review prefix
            now = datetime.utcnow()
            prefix = f"reviews/{now.year}/{now.month:02d}/{review_id}/"

            response = client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
            )

            if "Contents" not in response:
                return 0

            # Delete each object
            deleted = 0
            for obj in response["Contents"]:
                if await self.delete_file(obj["Key"]):
                    deleted += 1

            logger.info(f"Deleted {deleted} files for review {review_id}")
            return deleted

        except Exception as e:
            logger.error(f"Failed to delete review media: {e}")
            return 0

    async def file_exists(self, path: str) -> bool:
        """
        Check if a file exists in R2.

        Args:
            path: File path in bucket

        Returns:
            True if file exists
        """
        client = self._get_client()
        if client is None:
            return False

        try:
            client.head_object(Bucket=self.bucket, Key=path)
            return True
        except Exception:
            return False

    async def get_file_info(self, path: str) -> Optional[dict]:
        """
        Get file metadata from R2.

        Args:
            path: File path in bucket

        Returns:
            Dict with file info (size, content_type, last_modified)
        """
        client = self._get_client()
        if client is None:
            return None

        try:
            response = client.head_object(Bucket=self.bucket, Key=path)
            return {
                "size": response.get("ContentLength", 0),
                "content_type": response.get("ContentType", "application/octet-stream"),
                "last_modified": response.get("LastModified"),
                "etag": response.get("ETag", "").strip('"'),
            }
        except Exception:
            return None
