"""
IP Verification Service - Detect new IP addresses and send SMS alerts
"""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.identity import User  # Correct: identity.users table (37 columns)
from services.audit_service import AuditService
from services.ringcentral_service import RingCentralSMSService


class IPVerificationService:
    """
    Service for IP address verification and alerts.

    Features:
    - Detect new IP addresses on login
    - Send SMS alerts via RingCentral
    - Manage trusted IP list
    """

    def __init__(
        self,
        db: AsyncSession,
        sms_service: RingCentralSMSService = None,
        audit_service: AuditService = None,
    ):
        self.db = db
        self.sms_service = sms_service
        self.audit_service = audit_service

    async def check_ip_address(self, user: User, current_ip: str, user_agent: str = None) -> bool:
        """
        Check if current IP is trusted. Send SMS alert if new.

        Args:
            user: User instance
            current_ip: Current client IP address
            user_agent: Client user agent string

        Returns:
            True if IP is trusted, False if new IP detected
        """
        # IP verification disabled
        if not user.ip_verification_enabled:
            return True

        # No trusted IPs yet - first login
        if not user.trusted_ips:
            user.trusted_ips = [current_ip]
            user.last_known_ip = current_ip
            await self.db.commit()
            return True

        # Check if current IP is in trusted list
        if current_ip in user.trusted_ips:
            # Update last known IP
            user.last_known_ip = current_ip
            await self.db.commit()
            return True

        # New IP detected - send alert
        await self._send_new_ip_alert(user, current_ip, user_agent)

        # Log security event
        if self.audit_service:
            await self.audit_service.log_security_event(
                event_type="NEW_IP_DETECTED",
                description=f"New IP address detected for {user.email}: {current_ip}",
                user_id=user.id,
                success=True,
                metadata={
                    "new_ip": current_ip,
                    "last_known_ip": user.last_known_ip,
                    "trusted_ips_count": len(user.trusted_ips),
                },
                ip_address=current_ip,
                user_agent=user_agent,
            )

        return False

    async def _send_new_ip_alert(self, user: User, new_ip: str, user_agent: str = None):
        """
        Send SMS alert about new IP address.

        Args:
            user: User instance
            new_ip: New IP address
            user_agent: Client user agent
        """
        if not self.sms_service:
            return

        # Get user's phone number (assuming it's stored somewhere)
        # For now, skip if no phone in profile
        phone = getattr(user, "phone", None)
        if not phone:
            return

        # Format alert message
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        device_info = user_agent[:50] if user_agent else "Unknown device"

        message = (
            f"🔒 Security Alert - MyHibachi\n\n"
            f"New login detected:\n"
            f"IP: {new_ip}\n"
            f"Time: {timestamp}\n"
            f"Device: {device_info}\n\n"
            f"If this wasn't you, secure your account immediately:\n"
            f"https://admin.myhibachichef.com/security"
        )

        try:
            await self.sms_service.send_sms(to_number=phone, message=message)

            # Log alert sent
            if self.audit_service:
                await self.audit_service.log_security_event(
                    event_type="IP_ALERT_SENT",
                    description=f"SMS alert sent for new IP: {user.email}",
                    user_id=user.id,
                    success=True,
                    metadata={"ip": new_ip, "phone": phone[-4:]},  # Last 4 digits only
                    ip_address=new_ip,
                    user_agent=user_agent,
                )

        except Exception as e:
            # Log alert failure
            if self.audit_service:
                await self.audit_service.log_security_event(
                    event_type="IP_ALERT_SENT",
                    description=f"Failed to send SMS alert: {user.email}",
                    user_id=user.id,
                    success=False,
                    failure_reason=str(e),
                    metadata={"ip": new_ip},
                    ip_address=new_ip,
                    user_agent=user_agent,
                )

    async def add_trusted_ip(self, user: User, ip_address: str, user_agent: str = None) -> bool:
        """
        Add IP address to trusted list.

        Args:
            user: User instance
            ip_address: IP address to trust
            user_agent: Client user agent

        Returns:
            True if added, False if already trusted
        """
        if not user.trusted_ips:
            user.trusted_ips = []

        if ip_address in user.trusted_ips:
            return False

        user.trusted_ips.append(ip_address)
        await self.db.commit()

        # Log trusted IP addition
        if self.audit_service:
            await self.audit_service.log_security_event(
                event_type="TRUSTED_IP_ADDED",
                description=f"IP address added to trusted list: {user.email}",
                user_id=user.id,
                success=True,
                metadata={"ip": ip_address, "total_trusted": len(user.trusted_ips)},
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return True

    async def remove_trusted_ip(self, user: User, ip_address: str, user_agent: str = None) -> bool:
        """
        Remove IP address from trusted list.

        Args:
            user: User instance
            ip_address: IP address to remove
            user_agent: Client user agent

        Returns:
            True if removed, False if not in list
        """
        if not user.trusted_ips or ip_address not in user.trusted_ips:
            return False

        user.trusted_ips.remove(ip_address)
        await self.db.commit()

        # Log trusted IP removal
        if self.audit_service:
            await self.audit_service.log_security_event(
                event_type="TRUSTED_IP_REMOVED",
                description=f"IP address removed from trusted list: {user.email}",
                user_id=user.id,
                success=True,
                metadata={"ip": ip_address, "remaining_trusted": len(user.trusted_ips)},
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return True

    async def enable_ip_verification(self, user: User, current_ip: str, user_agent: str = None):
        """
        Enable IP verification for user.

        Args:
            user: User instance
            current_ip: Current IP to add as first trusted IP
            user_agent: Client user agent
        """
        user.ip_verification_enabled = True
        user.trusted_ips = [current_ip]
        user.last_known_ip = current_ip
        await self.db.commit()

        # Log IP verification enabled
        if self.audit_service:
            await self.audit_service.log_security_event(
                event_type="IP_VERIFICATION_ENABLED",
                description=f"IP verification enabled: {user.email}",
                user_id=user.id,
                success=True,
                metadata={"initial_ip": current_ip},
                ip_address=current_ip,
                user_agent=user_agent,
            )

    async def disable_ip_verification(self, user: User, user_agent: str = None):
        """
        Disable IP verification for user.

        Args:
            user: User instance
            user_agent: Client user agent
        """
        user.ip_verification_enabled = False
        await self.db.commit()

        # Log IP verification disabled
        if self.audit_service:
            await self.audit_service.log_security_event(
                event_type="IP_VERIFICATION_DISABLED",
                description=f"IP verification disabled: {user.email}",
                user_id=user.id,
                success=True,
                user_agent=user_agent,
            )


def get_ip_verification_service(
    db: AsyncSession, sms_service: RingCentralSMSService = None, audit_service: AuditService = None
) -> IPVerificationService:
    """Get IPVerificationService instance."""
    return IPVerificationService(db, sms_service, audit_service)
