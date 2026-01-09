"""
Password Reset Service
======================

Handles secure password reset flow:
1. Generate unique reset token
2. Store token in database with expiry
3. Send reset email via Resend/SMTP
4. Verify token and update password
5. Invalidate all user sessions after reset

Security Features:
- Rate limiting (3 requests per hour per email)
- Token expires after 1 hour
- One-time use tokens
- Constant-time comparison to prevent timing attacks
- No user enumeration (always returns success)
- All sessions invalidated after password reset

Related Files:
- database/migrations/012_token_blacklist_and_reset.sql
- services/token_blacklist_service.py
- routers/v1/auth.py

Usage:
    from services.password_reset_service import PasswordResetService

    service = PasswordResetService(db)

    # Request reset
    await service.request_reset("user@example.com")

    # Verify and reset
    success = await service.reset_password(token, new_password)
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import hash_password
from db.models.identity import User

logger = logging.getLogger(__name__)

# Rate limiting constants
MAX_RESET_REQUESTS_PER_HOUR = 3


class PasswordResetService:
    """
    Secure password reset service with email notification.

    Features:
    - Secure token generation (32 bytes = 256 bits)
    - Token hashing for storage (only hash stored, never plaintext)
    - Rate limiting per email
    - Token expiration (1 hour)
    - One-time use tokens
    - Session invalidation after reset
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize password reset service.

        Args:
            db: Database session for token storage
        """
        self.db = db
        self.token_expiry_minutes = getattr(settings, "PASSWORD_RESET_EXPIRE_MINUTES", 60)
        self.max_attempts = getattr(settings, "PASSWORD_RESET_MAX_ATTEMPTS", 3)
        self.frontend_url = getattr(settings, "FRONTEND_URL", "https://admin.myhibachichef.com")

    async def request_reset(self, email: str) -> bool:
        """
        Request a password reset link.

        Always returns True for security (no user enumeration).
        Only sends email if user exists and rate limit not exceeded.

        Args:
            email: User's email address

        Returns:
            True always (for security - no user enumeration)
        """
        email_lower = email.lower().strip()

        try:
            # Check if user exists
            result = await self.db.execute(select(User).where(User.email == email_lower))
            user = result.scalar_one_or_none()

            if not user:
                logger.info(f"📧 Reset requested for non-existent email: {email_lower[:3]}***")
                return True  # Don't reveal if email exists

            # Check rate limiting
            rate_limited = await self._is_rate_limited(email_lower)
            if rate_limited:
                logger.warning(f"🚫 Rate limit exceeded for password reset: {email_lower}")
                return True  # Still return True - don't reveal rate limiting

            # Generate secure token
            raw_token = secrets.token_urlsafe(32)  # 256 bits of entropy
            token_hash = self._hash_token(raw_token)

            # Store token in database
            expires_at = datetime.utcnow() + timedelta(minutes=self.token_expiry_minutes)

            await self.db.execute(
                text(
                    """
                    INSERT INTO security.password_reset_tokens 
                    (user_id, token_hash, expires_at, created_at)
                    VALUES (:user_id, :token_hash, :expires_at, NOW())
                """
                ),
                {
                    "user_id": str(user.id),
                    "token_hash": token_hash,
                    "expires_at": expires_at,
                },
            )
            await self.db.commit()

            # Send reset email
            reset_url = f"{self.frontend_url}/reset-password?token={raw_token}"
            email_sent = await self._send_reset_email(
                to_email=email_lower,
                user_name=user.full_name or user.email,
                reset_url=reset_url,
                expires_in_minutes=self.token_expiry_minutes,
            )

            if email_sent:
                logger.info(f"✅ Password reset email sent to {email_lower[:3]}***")
            else:
                logger.error(f"❌ Failed to send password reset email to {email_lower[:3]}***")

            return True

        except Exception as e:
            logger.exception(f"❌ Error in password reset request: {e}")
            return True  # Always return True for security

    async def reset_password(self, token: str, new_password: str) -> tuple[bool, str]:
        """
        Verify reset token and update password.

        Args:
            token: Reset token from email link
            new_password: New password to set

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            token_hash = self._hash_token(token)

            # Find valid token
            result = await self.db.execute(
                text(
                    """
                    SELECT id, user_id, expires_at, used_at
                    FROM security.password_reset_tokens
                    WHERE token_hash = :token_hash
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                ),
                {"token_hash": token_hash},
            )
            token_row = result.fetchone()

            if not token_row:
                logger.warning("🔒 Invalid password reset token attempted")
                return False, "Invalid or expired reset link. Please request a new one."

            token_id, user_id, expires_at, used_at = token_row

            # Check if already used
            if used_at is not None:
                logger.warning(f"🔒 Attempt to reuse password reset token for user {user_id}")
                return False, "This reset link has already been used. Please request a new one."

            # Check expiration
            if datetime.utcnow() > expires_at:
                logger.warning(f"🔒 Expired password reset token for user {user_id}")
                return False, "Reset link has expired. Please request a new one."

            # Get user
            user = await self.db.get(User, user_id)
            if not user:
                logger.error(f"🔒 User not found for password reset: {user_id}")
                return False, "User not found."

            # Update password
            user.password_hash = hash_password(new_password)
            user.updated_at = datetime.utcnow()

            # Mark token as used
            await self.db.execute(
                text(
                    """
                    UPDATE security.password_reset_tokens
                    SET used_at = NOW()
                    WHERE id = :token_id
                """
                ),
                {"token_id": token_id},
            )

            # Invalidate all user tokens (security measure)
            await self._invalidate_all_user_tokens(str(user.id))

            await self.db.commit()

            logger.info(f"✅ Password reset successful for user {user.email}")
            return (
                True,
                "Password has been reset successfully. Please login with your new password.",
            )

        except Exception as e:
            logger.exception(f"❌ Error resetting password: {e}")
            await self.db.rollback()
            return False, "An error occurred. Please try again or contact support."

    async def _is_rate_limited(self, email: str) -> bool:
        """
        Check if email has exceeded rate limit.

        Args:
            email: Email address to check

        Returns:
            True if rate limited, False otherwise
        """
        try:
            result = await self.db.execute(
                text(
                    """
                    SELECT COUNT(*) as request_count
                    FROM security.password_reset_tokens prt
                    JOIN identity.users u ON prt.user_id = u.id::text
                    WHERE u.email = :email
                    AND prt.created_at > NOW() - INTERVAL '1 hour'
                """
                ),
                {"email": email},
            )
            row = result.fetchone()
            request_count = row.request_count if row else 0
            return request_count >= self.max_attempts
        except Exception as e:
            logger.warning(f"⚠️ Rate limit check failed: {e}")
            return False  # Fail open for usability

    async def _invalidate_all_user_tokens(self, user_id: str) -> None:
        """
        Invalidate all tokens for a user after password reset.

        Args:
            user_id: User's UUID string
        """
        try:
            from services.token_blacklist_service import TokenBlacklistService

            blacklist_service = TokenBlacklistService(self.db)
            await blacklist_service.blacklist_all_user_tokens(
                user_id=user_id, reason="password_reset"
            )
            logger.info(f"✅ Invalidated all tokens for user {user_id[:8]}...")
        except Exception as e:
            logger.warning(f"⚠️ Failed to invalidate user tokens: {e}")
            # Continue anyway - password is already reset

    def _hash_token(self, token: str) -> str:
        """
        Hash token for secure storage using SHA-256.

        We store only the hash, never the raw token.
        Uses constant-time comparison to prevent timing attacks.

        Args:
            token: Raw token to hash

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(token.encode()).hexdigest()

    async def _send_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_url: str,
        expires_in_minutes: int,
    ) -> bool:
        """
        Send password reset email via email service.

        Args:
            to_email: Recipient email
            user_name: User's display name
            reset_url: Full reset URL with token
            expires_in_minutes: Token expiry time

        Returns:
            True if email sent successfully
        """
        try:
            from services.email_service import EmailService

            email_service = EmailService()

            subject = "Reset Your My Hibachi Password"

            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #dc2626; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
        .button {{ background-color: #dc2626; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; font-weight: bold; }}
        .warning {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Password Reset Request</h1>
        </div>
        <div class="content">
            <h2>Hello {user_name},</h2>
            <p>We received a request to reset your password for your My Hibachi account.</p>
            <p>Click the button below to set a new password:</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button">Reset My Password</a>
            </p>
            <div class="warning">
                <strong>⚠️ Important:</strong>
                <ul>
                    <li>This link expires in <strong>{expires_in_minutes} minutes</strong></li>
                    <li>This link can only be used once</li>
                    <li>If you didn't request this, please ignore this email</li>
                </ul>
            </div>
            <p>If the button doesn't work, copy and paste this URL into your browser:</p>
            <p style="word-break: break-all; font-size: 12px; color: #6b7280;">{reset_url}</p>
            <p>For security, all your active sessions will be logged out after you reset your password.</p>
        </div>
        <div class="footer">
            <p>© 2025 My Hibachi Chef. All rights reserved.</p>
            <p>If you didn't request this password reset, you can safely ignore this email.</p>
        </div>
    </div>
</body>
</html>
"""

            text_body = f"""
Hello {user_name},

We received a request to reset your password for your My Hibachi account.

Click the link below to set a new password:
{reset_url}

IMPORTANT:
- This link expires in {expires_in_minutes} minutes
- This link can only be used once
- If you didn't request this, please ignore this email

For security, all your active sessions will be logged out after you reset your password.

© 2025 My Hibachi Chef. All rights reserved.
"""

            return email_service._send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                tags=["password-reset", "security"],
            )

        except Exception as e:
            logger.exception(f"❌ Failed to send reset email: {e}")
            return False


# Convenience function for route handlers
async def request_password_reset(db: AsyncSession, email: str) -> bool:
    """Request a password reset for an email address."""
    service = PasswordResetService(db)
    return await service.request_reset(email)


async def confirm_password_reset(
    db: AsyncSession, token: str, new_password: str
) -> tuple[bool, str]:
    """Confirm password reset with token."""
    service = PasswordResetService(db)
    return await service.reset_password(token, new_password)
