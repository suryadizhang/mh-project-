"""
TOTP Service - Two-Factor Authentication using Google Authenticator
"""

import pyotp
import qrcode
import io
import base64
from typing import Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from core.security import get_password_hash, verify_password
from services.audit_service import AuditService


class TOTPService:
    """
    Service for managing Time-based One-Time Passwords (TOTP) for 2FA.

    Uses pyotp library for Google Authenticator compatibility.
    """

    def __init__(self, db: AsyncSession, audit_service: AuditService = None):
        self.db = db
        self.audit_service = audit_service

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret key.

        Returns:
            32-character base32 secret key
        """
        return pyotp.random_base32()

    def generate_qr_code(self, secret: str, email: str, issuer: str = "MyHibachi") -> str:
        """
        Generate QR code for Google Authenticator setup.

        Args:
            secret: TOTP secret key
            email: User's email address
            issuer: Application name (default: "MyHibachi")

        Returns:
            Base64-encoded PNG image of QR code
        """
        # Generate provisioning URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=email, issuer_name=issuer)

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_base64}"

    def verify_code(self, secret: str, code: str) -> bool:
        """
        Verify a TOTP code against the secret.

        Args:
            secret: User's TOTP secret key
            code: 6-digit code from authenticator app

        Returns:
            True if code is valid, False otherwise
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # Allow 30s time drift

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup codes for account recovery.

        Args:
            count: Number of backup codes to generate (default: 10)

        Returns:
            List of backup codes (8 characters each)
        """
        import secrets
        import string

        backup_codes = []
        for _ in range(count):
            code = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            backup_codes.append(code)

        return backup_codes

    def hash_backup_codes(self, codes: List[str]) -> List[str]:
        """
        Hash backup codes before storing in database.

        Args:
            codes: List of plain text backup codes

        Returns:
            List of hashed backup codes
        """
        return [get_password_hash(code) for code in codes]

    def verify_backup_code(self, hashed_codes: List[str], code: str) -> Tuple[bool, List[str]]:
        """
        Verify a backup code and remove it if valid.

        Args:
            hashed_codes: List of hashed backup codes from database
            code: Plain text backup code to verify

        Returns:
            Tuple of (is_valid, remaining_codes)
        """
        for i, hashed_code in enumerate(hashed_codes):
            if verify_password(code, hashed_code):
                # Remove used code
                remaining = hashed_codes[:i] + hashed_codes[i + 1 :]
                return True, remaining

        return False, hashed_codes

    async def enable_2fa(
        self, user: User, code: str, ip_address: str = None, user_agent: str = None
    ) -> Tuple[bool, List[str]]:
        """
        Enable 2FA for a user after verifying setup code.

        Args:
            user: User instance
            code: 6-digit verification code from authenticator
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Tuple of (success, backup_codes)
        """
        # Verify the code
        if not user.mfa_secret:
            raise ValueError("MFA secret not set. Call generate_secret() first.")

        if not self.verify_code(user.mfa_secret, code):
            # Log failed 2FA setup
            if self.audit_service:
                await self.audit_service.log_security_event(
                    event_type="2FA_SETUP",
                    description=f"Failed 2FA setup - invalid code: {user.email}",
                    user_id=user.id,
                    success=False,
                    failure_reason="Invalid verification code",
                    ip_address=ip_address,
                    user_agent=user_agent,
                )

            return False, []

        # Generate and store backup codes
        backup_codes = self.generate_backup_codes()
        hashed_codes = self.hash_backup_codes(backup_codes)

        user.mfa_enabled = True
        user.mfa_backup_codes = hashed_codes
        await self.db.commit()

        # Log successful 2FA setup
        if self.audit_service:
            await self.audit_service.log_security_event(
                event_type="2FA_SETUP",
                description=f"2FA enabled successfully: {user.email}",
                user_id=user.id,
                success=True,
                metadata={"backup_codes_generated": len(backup_codes)},
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return True, backup_codes

    async def disable_2fa(
        self, user: User, password: str, ip_address: str = None, user_agent: str = None
    ) -> bool:
        """
        Disable 2FA for a user after verifying password.

        Args:
            user: User instance
            password: User's password for confirmation
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            True if 2FA disabled, False if password wrong
        """
        # Verify password
        if not verify_password(password, user.hashed_password):
            # Log failed 2FA disable attempt
            if self.audit_service:
                await self.audit_service.log_security_event(
                    event_type="2FA_DISABLE",
                    description=f"Failed 2FA disable - wrong password: {user.email}",
                    user_id=user.id,
                    success=False,
                    failure_reason="Wrong password",
                    ip_address=ip_address,
                    user_agent=user_agent,
                )

            return False

        # Disable 2FA
        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_backup_codes = None
        await self.db.commit()

        # Log successful 2FA disable
        if self.audit_service:
            await self.audit_service.log_security_event(
                event_type="2FA_DISABLE",
                description=f"2FA disabled: {user.email}",
                user_id=user.id,
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return True

    async def verify_2fa_login(
        self, user: User, code: str, ip_address: str = None, user_agent: str = None
    ) -> bool:
        """
        Verify 2FA code during login.

        Args:
            user: User instance
            code: 6-digit code or backup code
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            True if code valid, False otherwise
        """
        # Try TOTP code first
        if self.verify_code(user.mfa_secret, code):
            # Log successful 2FA login
            if self.audit_service:
                await self.audit_service.log_security_event(
                    event_type="2FA_LOGIN",
                    description=f"Successful 2FA login: {user.email}",
                    user_id=user.id,
                    success=True,
                    metadata={"method": "totp"},
                    ip_address=ip_address,
                    user_agent=user_agent,
                )

            return True

        # Try backup code
        if user.mfa_backup_codes:
            is_valid, remaining_codes = self.verify_backup_code(user.mfa_backup_codes, code)

            if is_valid:
                # Update remaining backup codes
                user.mfa_backup_codes = remaining_codes
                await self.db.commit()

                # Log successful backup code usage
                if self.audit_service:
                    await self.audit_service.log_security_event(
                        event_type="2FA_LOGIN",
                        description=f"Successful 2FA login with backup code: {user.email}",
                        user_id=user.id,
                        success=True,
                        metadata={"method": "backup_code", "remaining_codes": len(remaining_codes)},
                        ip_address=ip_address,
                        user_agent=user_agent,
                    )

                return True

        # Log failed 2FA login
        if self.audit_service:
            await self.audit_service.log_security_event(
                event_type="2FA_LOGIN",
                description=f"Failed 2FA login - invalid code: {user.email}",
                user_id=user.id,
                success=False,
                failure_reason="Invalid 2FA code or backup code",
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return False


def get_totp_service(db: AsyncSession, audit_service: AuditService = None) -> TOTPService:
    """Get TOTPService instance."""
    return TOTPService(db, audit_service)
