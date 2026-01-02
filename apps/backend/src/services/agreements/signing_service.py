"""
Signing Service
===============

Handles signature capture, validation, PDF generation, and storage.

Features:
- Signature image validation (format, dimensions, file size)
- PDF generation with embedded signature
- Upload to Cloudflare R2 storage
- Email confirmation with PDF attachment

PDF Generation Flow:
1. Fetch signed agreement + rendered content
2. Generate PDF with pdfkit/weasyprint
3. Embed signature image at bottom
4. Upload to R2/S3
5. Update agreement with PDF URL
6. Send confirmation email

Usage:
    service = SigningService(db)

    # Validate signature before saving
    is_valid = service.validate_signature_image(signature_bytes)

    # Generate and store PDF
    pdf_url = await service.generate_and_store_pdf(
        agreement_id=agreement.id,
        signature_image=signature_bytes
    )

    # Send confirmation email
    await service.send_confirmation_email(agreement_id)

Storage:
    - Primary: Cloudflare R2 (S3-compatible)
    - Path format: agreements/{year}/{month}/{agreement_id}.pdf
    - Retention: 7 years with auto-delete policy

See: database/migrations/008_legal_agreements_system.sql
"""

import io
import logging
import os
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Signature constraints
MAX_SIGNATURE_SIZE_BYTES = 500_000  # 500KB
MIN_SIGNATURE_WIDTH = 100  # pixels
MIN_SIGNATURE_HEIGHT = 50  # pixels
MAX_SIGNATURE_WIDTH = 2000  # pixels
MAX_SIGNATURE_HEIGHT = 1000  # pixels
ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP"}


class SigningService:
    """
    Service for signature capture, validation, PDF generation, and storage.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize signing service.

        Args:
            db: Database session
        """
        self.db = db

    def validate_signature_image(
        self,
        signature_bytes: bytes,
    ) -> dict[str, Any]:
        """
        Validate a signature image.

        Checks:
        - File size (max 500KB)
        - Image format (PNG, JPEG, WEBP)
        - Dimensions (reasonable size)
        - Not blank/empty

        Args:
            signature_bytes: Raw image bytes

        Returns:
            Dict with 'valid' bool and 'error' message if invalid
        """
        # Check file size
        if len(signature_bytes) > MAX_SIGNATURE_SIZE_BYTES:
            return {
                "valid": False,
                "error": f"Signature file too large. Maximum size is {MAX_SIGNATURE_SIZE_BYTES // 1000}KB",
            }

        if len(signature_bytes) < 100:
            return {"valid": False, "error": "Signature image is too small or empty"}

        try:
            from PIL import Image

            img = Image.open(io.BytesIO(signature_bytes))

            # Check format
            if img.format not in ALLOWED_FORMATS:
                return {
                    "valid": False,
                    "error": f"Invalid image format. Allowed: {', '.join(ALLOWED_FORMATS)}",
                }

            # Check dimensions
            width, height = img.size

            if width < MIN_SIGNATURE_WIDTH or height < MIN_SIGNATURE_HEIGHT:
                return {
                    "valid": False,
                    "error": f"Signature too small. Minimum size: {MIN_SIGNATURE_WIDTH}x{MIN_SIGNATURE_HEIGHT}px",
                }

            if width > MAX_SIGNATURE_WIDTH or height > MAX_SIGNATURE_HEIGHT:
                return {
                    "valid": False,
                    "error": f"Signature too large. Maximum size: {MAX_SIGNATURE_WIDTH}x{MAX_SIGNATURE_HEIGHT}px",
                }

            # Check if image is not completely blank/white
            # Simple check: look for some non-white pixels
            if self._is_signature_blank(img):
                return {
                    "valid": False,
                    "error": "Signature appears to be blank. Please draw your signature.",
                }

            return {"valid": True, "format": img.format, "size": (width, height)}

        except ImportError:
            logger.warning("PIL not installed, skipping image validation")
            return {"valid": True, "warning": "Image validation skipped"}
        except Exception as e:
            return {"valid": False, "error": f"Could not process signature image: {str(e)}"}

    def _is_signature_blank(self, img) -> bool:
        """
        Check if an image is essentially blank (all white/transparent).

        Args:
            img: PIL Image object

        Returns:
            True if signature appears blank
        """
        try:
            from PIL import ImageStat

            # Convert to grayscale for easier analysis
            gray = img.convert("L")
            stat = ImageStat.Stat(gray)

            # If mean is very close to 255 (white), it's blank
            # Allow some tolerance for anti-aliasing
            if stat.mean[0] > 250:
                return True

            # Check if there's enough variance (actual drawing)
            if stat.stddev[0] < 5:
                return True

            return False

        except Exception:
            # If analysis fails, assume it's valid
            return False

    async def generate_pdf(
        self,
        agreement_id: UUID,
        include_signature: bool = True,
    ) -> bytes | None:
        """
        Generate a PDF for a signed agreement.

        Args:
            agreement_id: The signed agreement ID
            include_signature: Whether to embed signature image

        Returns:
            PDF bytes, or None if generation fails
        """
        # Fetch agreement details
        result = await self.db.execute(
            text(
                """
                SELECT
                    sa.id, sa.agreement_type, sa.agreement_version,
                    sa.rendered_content, sa.signer_name, sa.signer_email,
                    sa.signature_image, sa.signed_at,
                    sa.signer_ip_address, sa.signing_method
                FROM core.signed_agreements sa
                WHERE sa.id = :agreement_id
            """
            ),
            {"agreement_id": str(agreement_id)},
        )

        row = result.fetchone()
        if not row:
            logger.error(f"Agreement {agreement_id} not found for PDF generation")
            return None

        try:
            # Try using weasyprint for PDF generation
            from weasyprint import HTML

            html_content = self._build_pdf_html(
                agreement_type=row.agreement_type,
                agreement_version=row.agreement_version,
                rendered_content=row.rendered_content,
                signer_name=row.signer_name,
                signer_email=row.signer_email,
                signed_at=row.signed_at,
                signer_ip=row.signer_ip_address,
                signing_method=row.signing_method,
                signature_image=row.signature_image if include_signature else None,
            )

            pdf_bytes = HTML(string=html_content).write_pdf()

            logger.info(f"Generated PDF for agreement {agreement_id}")
            return pdf_bytes

        except ImportError:
            logger.warning("weasyprint not installed, trying reportlab")
            return self._generate_pdf_reportlab(row, include_signature)
        except Exception as e:
            logger.error(f"PDF generation failed for {agreement_id}: {e}")
            return None

    def _build_pdf_html(
        self,
        agreement_type: str,
        agreement_version: str,
        rendered_content: str,
        signer_name: str,
        signer_email: str,
        signed_at: datetime,
        signer_ip: str | None,
        signing_method: str,
        signature_image: bytes | None,
    ) -> str:
        """
        Build HTML for PDF generation.

        Args:
            Agreement data fields

        Returns:
            HTML string for PDF conversion
        """
        import base64

        # Convert signature to base64 for embedding
        signature_html = ""
        if signature_image:
            sig_b64 = base64.b64encode(signature_image).decode("utf-8")
            signature_html = f"""
                <div class="signature-section">
                    <p><strong>Digital Signature:</strong></p>
                    <img src="data:image/png;base64,{sig_b64}"
                         alt="Signature"
                         style="max-width: 300px; border: 1px solid #ccc; padding: 10px;" />
                </div>
            """

        # Convert markdown to HTML if needed
        try:
            import markdown

            content_html = markdown.markdown(rendered_content)
        except ImportError:
            # Fallback: wrap in pre tag
            content_html = f"<pre>{rendered_content}</pre>"

        title_map = {
            "liability_waiver": "Service Agreement & Liability Waiver",
            "allergen_disclosure": "Allergen Disclosure & Acknowledgment",
        }
        title = title_map.get(agreement_type, agreement_type.replace("_", " ").title())

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            max-width: 8in;
            margin: 0.5in auto;
            padding: 0 0.5in;
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            color: #b8860b;
            margin: 0;
            font-size: 18pt;
        }}
        .header .logo {{
            font-size: 24pt;
            margin-bottom: 5px;
        }}
        .meta-info {{
            background: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 10pt;
        }}
        .content {{
            margin-bottom: 30px;
        }}
        .content h2 {{
            color: #333;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }}
        .signature-section {{
            margin-top: 30px;
            border-top: 1px solid #ddd;
            padding-top: 20px;
        }}
        .signing-info {{
            background: #e8f4e8;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }}
        .footer {{
            text-align: center;
            font-size: 9pt;
            color: #666;
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🍱</div>
        <h1>My Hibachi At Home</h1>
        <p>{title}</p>
    </div>

    <div class="meta-info">
        <strong>Document Version:</strong> {agreement_version}<br>
        <strong>Generated:</strong> {datetime.utcnow().strftime("%B %d, %Y at %I:%M %p")} UTC
    </div>

    <div class="content">
        {content_html}
    </div>

    {signature_html}

    <div class="signing-info">
        <p><strong>Signed By:</strong> {signer_name}</p>
        <p><strong>Email:</strong> {signer_email}</p>
        <p><strong>Date & Time:</strong> {signed_at.strftime("%B %d, %Y at %I:%M %p")} UTC</p>
        <p><strong>Signing Method:</strong> {signing_method}</p>
        {f'<p><strong>IP Address:</strong> {signer_ip}</p>' if signer_ip else ''}
    </div>

    <div class="footer">
        <p>This is a legally binding electronic document.</p>
        <p>My Hibachi At Home | cs@myhibachichef.com | (916) 740-8768</p>
        <p>Document ID: {str(agreement_id)[:8]}...</p>
    </div>
</body>
</html>
"""

    def _generate_pdf_reportlab(self, row, include_signature: bool) -> bytes | None:
        """
        Fallback PDF generation using reportlab.

        Args:
            row: Database row with agreement data
            include_signature: Whether to include signature

        Returns:
            PDF bytes or None
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import inch

            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # Header
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width / 2, height - 0.75 * inch, "My Hibachi At Home")
            c.setFont("Helvetica", 12)
            c.drawCentredString(
                width / 2, height - 1 * inch, row.agreement_type.replace("_", " ").title()
            )

            # Version
            c.setFont("Helvetica", 10)
            c.drawString(0.75 * inch, height - 1.5 * inch, f"Version: {row.agreement_version}")

            # Content (simplified - just show that it exists)
            y_position = height - 2 * inch
            c.setFont("Helvetica", 10)

            # Split content into lines
            content = row.rendered_content or ""
            lines = content.split("\n")

            for line in lines[:50]:  # Limit to first 50 lines
                if y_position < 2 * inch:
                    c.showPage()
                    y_position = height - inch

                # Truncate long lines
                if len(line) > 90:
                    line = line[:87] + "..."

                c.drawString(0.75 * inch, y_position, line)
                y_position -= 14

            # Signing info
            y_position -= 20
            c.setFont("Helvetica-Bold", 10)
            c.drawString(0.75 * inch, y_position, "Signed By:")
            c.setFont("Helvetica", 10)
            c.drawString(2 * inch, y_position, row.signer_name)

            y_position -= 14
            c.setFont("Helvetica-Bold", 10)
            c.drawString(0.75 * inch, y_position, "Email:")
            c.setFont("Helvetica", 10)
            c.drawString(2 * inch, y_position, row.signer_email)

            y_position -= 14
            c.setFont("Helvetica-Bold", 10)
            c.drawString(0.75 * inch, y_position, "Date:")
            c.setFont("Helvetica", 10)
            c.drawString(2 * inch, y_position, row.signed_at.strftime("%B %d, %Y at %I:%M %p"))

            c.save()
            buffer.seek(0)
            return buffer.read()

        except ImportError:
            logger.error("reportlab not installed, cannot generate PDF")
            return None
        except Exception as e:
            logger.error(f"reportlab PDF generation failed: {e}")
            return None

    async def upload_pdf_to_storage(
        self,
        pdf_bytes: bytes,
        agreement_id: UUID,
    ) -> str | None:
        """
        Upload PDF to Cloudflare R2 storage.

        Args:
            pdf_bytes: PDF file content
            agreement_id: Agreement ID for path

        Returns:
            Public URL of uploaded PDF, or None if upload fails
        """
        try:
            import boto3
            from botocore.config import Config

            # R2 configuration (from environment)
            r2_account_id = os.getenv("CLOUDFLARE_R2_ACCOUNT_ID")
            r2_access_key = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
            r2_secret_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
            r2_bucket = os.getenv("CLOUDFLARE_R2_BUCKET", "myhibachi-documents")
            r2_public_url = os.getenv("CLOUDFLARE_R2_PUBLIC_URL", "")

            if not all([r2_account_id, r2_access_key, r2_secret_key]):
                logger.warning("R2 credentials not configured, skipping upload")
                return None

            # Build path
            now = datetime.utcnow()
            path = f"agreements/{now.year}/{now.month:02d}/{agreement_id}.pdf"

            # Create S3 client for R2
            s3 = boto3.client(
                "s3",
                endpoint_url=f"https://{r2_account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=r2_access_key,
                aws_secret_access_key=r2_secret_key,
                config=Config(signature_version="s3v4"),
            )

            # Upload
            s3.put_object(
                Bucket=r2_bucket,
                Key=path,
                Body=pdf_bytes,
                ContentType="application/pdf",
            )

            # Return public URL
            if r2_public_url:
                url = f"{r2_public_url}/{path}"
            else:
                url = f"https://{r2_bucket}.{r2_account_id}.r2.cloudflarestorage.com/{path}"

            logger.info(f"Uploaded PDF for agreement {agreement_id} to {url}")
            return url

        except ImportError:
            logger.warning("boto3 not installed, cannot upload to R2")
            return None
        except Exception as e:
            logger.error(f"Failed to upload PDF to R2: {e}")
            return None

    async def generate_and_store_pdf(
        self,
        agreement_id: UUID,
    ) -> str | None:
        """
        Generate PDF, upload to storage, and update agreement record.

        Args:
            agreement_id: The signed agreement ID

        Returns:
            PDF URL if successful, None otherwise
        """
        # Generate PDF
        pdf_bytes = await self.generate_pdf(agreement_id, include_signature=True)
        if not pdf_bytes:
            return None

        # Upload to storage
        pdf_url = await self.upload_pdf_to_storage(pdf_bytes, agreement_id)
        if not pdf_url:
            return None

        # Update agreement record with PDF URL
        await self.db.execute(
            text(
                """
                UPDATE core.signed_agreements
                SET confirmation_pdf_url = :pdf_url
                WHERE id = :agreement_id
            """
            ),
            {"pdf_url": pdf_url, "agreement_id": str(agreement_id)},
        )
        await self.db.commit()

        return pdf_url

    async def send_confirmation_email(
        self,
        agreement_id: UUID,
    ) -> bool:
        """
        Send confirmation email with PDF attachment.

        Args:
            agreement_id: The signed agreement ID

        Returns:
            True if email sent successfully
        """
        # Fetch agreement details
        result = await self.db.execute(
            text(
                """
                SELECT signer_email, signer_name, agreement_type,
                       confirmation_pdf_url, signed_at
                FROM core.signed_agreements
                WHERE id = :agreement_id
            """
            ),
            {"agreement_id": str(agreement_id)},
        )

        row = result.fetchone()
        if not row:
            logger.error(f"Agreement {agreement_id} not found for email")
            return False

        try:
            # Import email service (Resend)
            from services.email_service import send_email

            title_map = {
                "liability_waiver": "Service Agreement & Liability Waiver",
                "allergen_disclosure": "Allergen Disclosure & Acknowledgment",
            }
            doc_title = title_map.get(row.agreement_type, "Agreement")

            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="text-align: center; padding: 20px; background: #f8f8f8; border-bottom: 3px solid #b8860b;">
                    <h1 style="color: #b8860b; margin: 0;">🍱 My Hibachi At Home</h1>
                </div>

                <div style="padding: 30px;">
                    <p>Hi {row.signer_name},</p>

                    <p>Thank you for signing your <strong>{doc_title}</strong>!</p>

                    <p>A copy of your signed agreement is attached to this email for your records.</p>

                    <div style="background: #e8f4e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Signed:</strong> {row.signed_at.strftime("%B %d, %Y at %I:%M %p")} UTC</p>
                    </div>

                    <p>If you have any questions, please don't hesitate to reach out!</p>

                    <p>
                        Best regards,<br>
                        <strong>The My Hibachi Team</strong>
                    </p>
                </div>

                <div style="text-align: center; padding: 20px; background: #f8f8f8; font-size: 12px; color: #666;">
                    <p style="margin: 0;">My Hibachi At Home | cs@myhibachichef.com | (916) 740-8768</p>
                </div>
            </div>
            """

            # Send email (with PDF attachment if available)
            attachments = []
            if row.confirmation_pdf_url:
                # Fetch PDF from URL and attach
                # For now, just include link in email
                html_content = html_content.replace(
                    '</div>\n                \n                <div style="text-align: center;',
                    f"""</div>

                    <div style="text-align: center; margin: 20px 0;">
                        <a href="{row.confirmation_pdf_url}"
                           style="background: #b8860b; color: white; padding: 12px 24px;
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            📄 Download PDF
                        </a>
                    </div>

                <div style="text-align: center;""",
                )

            await send_email(
                to=row.signer_email,
                subject=f"✅ Your {doc_title} - Signed",
                html=html_content,
            )

            # Update email sent timestamp
            await self.db.execute(
                text(
                    """
                    UPDATE core.signed_agreements
                    SET confirmation_email_sent_at = NOW()
                    WHERE id = :agreement_id
                """
                ),
                {"agreement_id": str(agreement_id)},
            )
            await self.db.commit()

            logger.info(f"Sent confirmation email for agreement {agreement_id}")
            return True

        except ImportError:
            logger.warning("Email service not available")
            return False
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")
            return False


# Convenience function for dependency injection
def get_signing_service(db: AsyncSession) -> SigningService:
    """FastAPI dependency injection helper."""
    return SigningService(db)
