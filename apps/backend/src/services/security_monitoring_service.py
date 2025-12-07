"""
Security Monitoring Service

Provides comprehensive security monitoring for authentication events:
- Progressive lockout with escalating durations
- Real-time alerts to Super Admins (Email + WhatsApp)
- Security audit logging to database
- Dashboard alerts for Admin Panel
- Breach detection and anomaly alerts

Alert Triggers:
1. Account lockout (5 failed PIN attempts)
2. Multiple accounts targeted from same IP
3. Unusual login location/device
4. After-hours access attempts
5. Repeated lockouts (potential brute force)

Integration:
- Email: Resend API (via email_service)
- WhatsApp: Twilio (via whatsapp_notification_service)
- Database: security.security_events + security.admin_alerts tables
"""

import json
import logging
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ============================================
# Enums and Constants
# ============================================


class SecurityEventType(str, Enum):
    """Types of security events to track"""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILED = "mfa_failed"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    PASSWORD_CHANGED = "password_changed"
    PIN_SETUP = "pin_setup"
    PIN_RESET = "pin_reset"
    WEBAUTHN_REGISTERED = "webauthn_registered"
    WEBAUTHN_REMOVED = "webauthn_removed"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BRUTE_FORCE_DETECTED = "brute_force_detected"
    UNUSUAL_LOCATION = "unusual_location"
    AFTER_HOURS_ACCESS = "after_hours_access"
    # New IP tracking events
    NEW_IP_LOGIN = "new_ip_login"
    GEO_IMPOSSIBLE_TRAVEL = "geo_impossible_travel"
    MULTI_ACCOUNT_IP = "multi_account_ip"
    BAD_IP_REPUTATION = "bad_ip_reputation"
    EXCESSIVE_NEW_IPS = "excessive_new_ips"


class AlertSeverity(str, Enum):
    """Alert severity levels"""

    LOW = "low"  # Informational
    MEDIUM = "medium"  # Needs attention
    HIGH = "high"  # Requires action
    CRITICAL = "critical"  # Immediate action required


class AlertStatus(str, Enum):
    """Alert status for dashboard"""

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


# Progressive lockout durations (in minutes)
LOCKOUT_DURATIONS = [
    15,
    30,
    60,
    1440,
    -1,
]  # 15min, 30min, 1hr, 24hr, permanent (-1)


# ============================================
# Pydantic Models
# ============================================


class SecurityEvent(BaseModel):
    """Security event data"""

    event_type: SecurityEventType
    user_id: Optional[str] = None
    email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: dict = {}
    severity: AlertSeverity = AlertSeverity.LOW


class AdminAlert(BaseModel):
    """Alert for Super Admin dashboard"""

    title: str
    message: str
    severity: AlertSeverity
    event_type: SecurityEventType
    user_id: Optional[str] = None
    email: Optional[str] = None
    ip_address: Optional[str] = None
    requires_action: bool = False
    action_url: Optional[str] = None


# ============================================
# Security Monitoring Service
# ============================================


class SecurityMonitoringService:
    """
    Handles security event logging and alerting.

    Features:
    - Progressive lockout with escalating durations
    - Real-time alerts to Super Admins
    - Email + WhatsApp notifications
    - Dashboard alerts for Admin Panel
    - Breach detection patterns
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._email_service = None
        self._whatsapp_service = None

        # Load Super Admin notification settings
        self.admin_email = os.getenv(
            "SUPER_ADMIN_EMAIL", "admin@myhibachichef.com"
        )
        self.admin_phone = os.getenv(
            "SUPER_ADMIN_PHONE",
            os.getenv("ADMIN_NOTIFICATION_PHONE", "+19167408768"),
        )
        self.enable_email_alerts = (
            os.getenv("SECURITY_EMAIL_ALERTS", "true").lower() == "true"
        )
        self.enable_whatsapp_alerts = (
            os.getenv("SECURITY_WHATSAPP_ALERTS", "true").lower() == "true"
        )

        # Business hours (for after-hours detection)
        self.business_start = int(
            os.getenv("BUSINESS_HOURS_START", "8")
        )  # 8 AM
        self.business_end = int(os.getenv("BUSINESS_HOURS_END", "22"))  # 10 PM

    @property
    def email_service(self):
        """Lazy load email service"""
        if self._email_service is None:
            try:
                from services.email_service import email_service

                self._email_service = email_service
            except ImportError:
                logger.warning("Email service not available")
        return self._email_service

    @property
    def whatsapp_service(self):
        """Lazy load WhatsApp service"""
        if self._whatsapp_service is None:
            try:
                from services.whatsapp_notification_service import (
                    get_whatsapp_service,
                )

                self._whatsapp_service = get_whatsapp_service()
            except ImportError:
                logger.warning("WhatsApp service not available")
        return self._whatsapp_service

    # ============================================
    # Progressive Lockout
    # ============================================

    async def get_progressive_lockout_duration(self, user_id: str) -> int:
        """
        Calculate progressive lockout duration based on recent lockouts.

        Returns:
            Lockout duration in minutes (-1 means permanent/disabled)
        """
        # Count recent lockouts (last 24 hours)
        query = text(
            """
            SELECT COUNT(*)
            FROM security.security_events
            WHERE user_id = :user_id
              AND event_type = 'account_locked'
              AND created_at > NOW() - INTERVAL '24 hours'
        """
        )

        try:
            result = await self.db.execute(query, {"user_id": user_id})
            lockout_count = result.scalar() or 0

            # Get appropriate lockout duration (capped at max index)
            index = min(lockout_count, len(LOCKOUT_DURATIONS) - 1)
            duration = LOCKOUT_DURATIONS[index]

            logger.info(
                f"Progressive lockout: User {user_id} has {lockout_count} recent lockouts, duration={duration} minutes"
            )

            return duration

        except Exception as e:
            logger.error(f"Error calculating lockout duration: {e}")
            return LOCKOUT_DURATIONS[0]  # Default to first level

    async def is_account_disabled(self, user_id: str) -> bool:
        """Check if account is permanently disabled due to security"""
        query = text(
            """
            SELECT 1 FROM security.security_events
            WHERE user_id = :user_id
              AND event_type = 'account_locked'
              AND details->>'permanent' = 'true'
              AND created_at > NOW() - INTERVAL '24 hours'
            LIMIT 1
        """
        )

        try:
            result = await self.db.execute(query, {"user_id": user_id})
            return result.scalar() is not None
        except Exception:
            return False

    # ============================================
    # Security Event Logging
    # ============================================

    async def log_event(self, event: SecurityEvent) -> None:
        """Log security event to database"""

        query = text(
            """
            INSERT INTO security.security_events
            (event_type, user_id, email, ip_address, user_agent, details, severity, created_at)
            VALUES
            (:event_type, CAST(:user_id AS uuid), :email, :ip_address, :user_agent, CAST(:details AS jsonb), :severity, NOW())
        """
        )

        try:
            # Serialize details to proper JSON string
            details_json = json.dumps(event.details) if event.details else "{}"

            await self.db.execute(
                query,
                {
                    "event_type": event.event_type.value,
                    "user_id": event.user_id,
                    "email": event.email,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "details": details_json,
                    "severity": event.severity.value,
                },
            )
            await self.db.commit()

            logger.debug(
                f"Security event logged: {event.event_type} for {event.email or event.user_id}"
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to log security event: {e}")

    # ============================================
    # Dashboard Alerts
    # ============================================

    async def create_dashboard_alert(self, alert: AdminAlert) -> None:
        """Create alert for Super Admin dashboard"""
        query = text(
            """
            INSERT INTO security.admin_alerts
            (title, message, severity, event_type, user_id, email, ip_address,
             requires_action, action_url, status, created_at)
            VALUES
            (:title, :message, :severity, :event_type, CAST(:user_id AS uuid), :email, :ip_address,
             :requires_action, :action_url, 'new', NOW())
        """
        )

        try:
            await self.db.execute(
                query,
                {
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity.value,
                    "event_type": alert.event_type.value,
                    "user_id": alert.user_id,
                    "email": alert.email,
                    "ip_address": alert.ip_address,
                    "requires_action": alert.requires_action,
                    "action_url": alert.action_url,
                },
            )
            await self.db.commit()

            logger.info(f"Dashboard alert created: {alert.title}")

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create dashboard alert: {e}")

    async def get_active_alerts(self, limit: int = 50) -> list[dict]:
        """Get active alerts for Super Admin dashboard"""
        query = text(
            """
            SELECT id, title, message, severity, event_type, user_id, email,
                   ip_address, requires_action, action_url, status, created_at
            FROM security.admin_alerts
            WHERE status IN ('new', 'acknowledged')
            ORDER BY
                CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    ELSE 4
                END,
                created_at DESC
            LIMIT :limit
        """
        )

        try:
            result = await self.db.execute(query, {"limit": limit})
            rows = result.fetchall()

            return [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "message": row.message,
                    "severity": row.severity,
                    "event_type": row.event_type,
                    "user_id": str(row.user_id) if row.user_id else None,
                    "email": row.email,
                    "ip_address": row.ip_address,
                    "requires_action": row.requires_action,
                    "action_url": row.action_url,
                    "status": row.status,
                    "created_at": (
                        row.created_at.isoformat() if row.created_at else None
                    ),
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []

    async def update_alert_status(
        self, alert_id: str, status: AlertStatus, resolved_by: str = None
    ) -> bool:
        """Update alert status"""
        query = text(
            """
            UPDATE security.admin_alerts
            SET status = :status,
                resolved_by = :resolved_by,
                resolved_at = CASE WHEN :status IN ('resolved', 'dismissed') THEN NOW() ELSE NULL END,
                updated_at = NOW()
            WHERE id = :alert_id
        """
        )

        try:
            await self.db.execute(
                query,
                {
                    "alert_id": alert_id,
                    "status": status.value,
                    "resolved_by": resolved_by,
                },
            )
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update alert status: {e}")
            return False

    # ============================================
    # Notification Methods
    # ============================================

    async def send_email_alert(
        self, subject: str, message: str, severity: AlertSeverity
    ) -> bool:
        """Send email alert to Super Admins"""
        if not self.enable_email_alerts or not self.email_service:
            logger.debug("Email alerts disabled or service unavailable")
            return False

        try:
            # Get all Super Admin emails
            query = text(
                """
                SELECT DISTINCT u.email
                FROM identity.users u
                JOIN identity.user_roles ur ON u.id = ur.user_id
                JOIN identity.roles r ON ur.role_id = r.id
                WHERE r.role_type = 'SUPER_ADMIN'
                  AND u.status = 'ACTIVE'
            """
            )

            result = await self.db.execute(query)
            admin_emails = [row.email for row in result.fetchall()]

            if not admin_emails:
                admin_emails = [self.admin_email]

            # Build HTML email
            severity_colors = {
                AlertSeverity.LOW: "#17a2b8",
                AlertSeverity.MEDIUM: "#ffc107",
                AlertSeverity.HIGH: "#fd7e14",
                AlertSeverity.CRITICAL: "#dc3545",
            }

            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: {severity_colors.get(severity, '#6c757d')}; color: white; padding: 20px; text-align: center;">
                    <h1>🔒 Security Alert</h1>
                    <p style="font-size: 18px; margin: 0;">{severity.value.upper()}</p>
                </div>
                <div style="padding: 20px; background: #f8f9fa; border: 1px solid #dee2e6;">
                    <h2 style="margin-top: 0;">{subject}</h2>
                    <p style="white-space: pre-line;">{message}</p>
                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
                    <p style="color: #6c757d; font-size: 12px;">
                        This is an automated security alert from My Hibachi Admin Panel.<br>
                        Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </p>
                </div>
                <div style="padding: 15px; text-align: center; background: #343a40; color: white;">
                    <a href="https://admin.myhibachichef.com/security/alerts"
                       style="color: #17a2b8; text-decoration: none;">
                        View in Dashboard →
                    </a>
                </div>
            </div>
            """

            text_body = f"""
🔒 SECURITY ALERT - {severity.value.upper()}

{subject}

{message}

---
Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
View in Dashboard: https://admin.myhibachichef.com/security/alerts
            """

            # Send to all admins
            for email in admin_emails:
                try:
                    self.email_service._send_email(
                        to_email=email,
                        subject=f"[{severity.value.upper()}] Security Alert: {subject}",
                        html_body=html_body,
                        text_body=text_body,
                        tags=[{"name": "category", "value": "security_alert"}],
                    )
                    logger.info(f"Security email sent to {email}")
                except Exception as e:
                    logger.error(
                        f"Failed to send security email to {email}: {e}"
                    )

            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False

    async def send_whatsapp_alert(
        self, message: str, severity: AlertSeverity
    ) -> bool:
        """Send WhatsApp alert to Super Admins"""
        if not self.enable_whatsapp_alerts or not self.whatsapp_service:
            logger.debug("WhatsApp alerts disabled or service unavailable")
            return False

        try:
            # Get all Super Admin phones
            query = text(
                """
                SELECT DISTINCT u.phone
                FROM identity.users u
                JOIN identity.user_roles ur ON u.id = ur.user_id
                JOIN identity.roles r ON ur.role_id = r.id
                WHERE r.role_type = 'SUPER_ADMIN'
                  AND u.status = 'ACTIVE'
                  AND u.phone IS NOT NULL
            """
            )

            result = await self.db.execute(query)
            admin_phones = [
                row.phone for row in result.fetchall() if row.phone
            ]

            if not admin_phones:
                admin_phones = [self.admin_phone]

            # Format message with emoji based on severity
            severity_emoji = {
                AlertSeverity.LOW: "ℹ️",
                AlertSeverity.MEDIUM: "⚠️",
                AlertSeverity.HIGH: "🔴",
                AlertSeverity.CRITICAL: "🚨",
            }

            formatted_message = f"""
{severity_emoji.get(severity, '🔒')} *SECURITY ALERT*
Severity: {severity.value.upper()}

{message}

Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
Dashboard: admin.myhibachichef.com/security
            """.strip()

            # Send to all admin phones
            for phone in admin_phones:
                try:
                    await self.whatsapp_service._send_whatsapp(
                        phone, formatted_message
                    )
                    logger.info(f"Security WhatsApp sent to {phone[-4:]}")
                except Exception as e:
                    logger.error(f"Failed to send WhatsApp to {phone}: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to send WhatsApp alert: {e}")
            return False

    # ============================================
    # High-Level Alert Methods
    # ============================================

    async def alert_account_locked(
        self,
        user_id: str,
        email: str,
        ip_address: str = None,
        lockout_minutes: int = 15,
        attempt_count: int = 5,
        is_permanent: bool = False,
    ) -> None:
        """
        Alert Super Admins when an account gets locked.

        Creates:
        - Security event log
        - Dashboard alert
        - Email notification
        - WhatsApp notification
        """
        severity = (
            AlertSeverity.CRITICAL if is_permanent else AlertSeverity.HIGH
        )

        # 1. Log security event
        event = SecurityEvent(
            event_type=SecurityEventType.ACCOUNT_LOCKED,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            severity=severity,
            details={
                "lockout_minutes": lockout_minutes,
                "attempt_count": attempt_count,
                "permanent": is_permanent,
            },
        )
        await self.log_event(event)

        # 2. Create dashboard alert
        if is_permanent:
            title = f"🚨 Account Permanently Disabled: {email}"
            message = f"Account {email} has been permanently disabled after repeated failed PIN attempts from IP {ip_address or 'Unknown'}. This may indicate a brute force attack. Manual intervention required."
        else:
            title = f"🔒 Account Locked: {email}"
            message = f"Account {email} locked for {lockout_minutes} minutes after {attempt_count} failed PIN attempts from IP {ip_address or 'Unknown'}."

        alert = AdminAlert(
            title=title,
            message=message,
            severity=severity,
            event_type=SecurityEventType.ACCOUNT_LOCKED,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            requires_action=is_permanent,
            action_url=f"/admin/users/{user_id}" if is_permanent else None,
        )
        await self.create_dashboard_alert(alert)

        # 3. Send notifications (for HIGH and CRITICAL)
        if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            await self.send_email_alert(title, message, severity)
            await self.send_whatsapp_alert(message, severity)

        logger.warning(f"Account locked alert sent for {email}")

    async def alert_brute_force_detected(
        self,
        ip_address: str,
        target_emails: list[str],
        attempt_count: int,
    ) -> None:
        """Alert when brute force attack is detected (multiple accounts from same IP)"""
        severity = AlertSeverity.CRITICAL

        # Log event
        event = SecurityEvent(
            event_type=SecurityEventType.BRUTE_FORCE_DETECTED,
            ip_address=ip_address,
            severity=severity,
            details={
                "target_emails": target_emails[:10],  # Limit for storage
                "attempt_count": attempt_count,
            },
        )
        await self.log_event(event)

        # Create alert
        title = f"🚨 BRUTE FORCE DETECTED from {ip_address}"
        message = f"""
Potential brute force attack detected!

IP Address: {ip_address}
Targeted Accounts: {len(target_emails)}
Total Attempts: {attempt_count}

Targeted emails:
{chr(10).join(['• ' + e for e in target_emails[:5]])}
{'... and ' + str(len(target_emails) - 5) + ' more' if len(target_emails) > 5 else ''}

RECOMMENDED ACTION: Block this IP address immediately.
        """.strip()

        alert = AdminAlert(
            title=title,
            message=message,
            severity=severity,
            event_type=SecurityEventType.BRUTE_FORCE_DETECTED,
            ip_address=ip_address,
            requires_action=True,
            action_url="/admin/security/blocked-ips",
        )
        await self.create_dashboard_alert(alert)

        # Send notifications
        await self.send_email_alert(title, message, severity)
        await self.send_whatsapp_alert(message, severity)

        logger.critical(f"Brute force detected from {ip_address}")

    async def alert_after_hours_access(
        self,
        user_id: str,
        email: str,
        ip_address: str = None,
        access_time: datetime = None,
    ) -> None:
        """Alert when access attempt occurs outside business hours"""
        access_time = access_time or datetime.now(timezone.utc)
        severity = AlertSeverity.MEDIUM

        # Log event
        event = SecurityEvent(
            event_type=SecurityEventType.AFTER_HOURS_ACCESS,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            severity=severity,
            details={
                "access_time": access_time.isoformat(),
                "business_hours": f"{self.business_start}:00 - {self.business_end}:00",
            },
        )
        await self.log_event(event)

        # Create dashboard alert (but don't send notifications for medium severity)
        alert = AdminAlert(
            title=f"⏰ After-Hours Access: {email}",
            message=f"User {email} accessed the system at {access_time.strftime('%H:%M UTC')} from IP {ip_address or 'Unknown'}. Business hours are {self.business_start}:00 - {self.business_end}:00.",
            severity=severity,
            event_type=SecurityEventType.AFTER_HOURS_ACCESS,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
        )
        await self.create_dashboard_alert(alert)

    async def check_for_brute_force(
        self, ip_address: str, time_window_minutes: int = 15
    ) -> bool:
        """
        Check if IP is attempting brute force attack.

        Returns True if attack detected (triggers alert automatically).
        """
        if not ip_address:
            return False

        query = text(
            """
            SELECT email, COUNT(*) as attempts
            FROM security.security_events
            WHERE ip_address = :ip_address
              AND event_type IN ('login_failed', 'mfa_failed')
              AND created_at > NOW() - INTERVAL ':minutes minutes'
            GROUP BY email
        """.replace(
                ":minutes", str(time_window_minutes)
            )
        )

        try:
            result = await self.db.execute(query, {"ip_address": ip_address})
            rows = result.fetchall()

            # Brute force criteria: 3+ different accounts OR 10+ total attempts
            if len(rows) >= 3 or sum(r.attempts for r in rows) >= 10:
                emails = [r.email for r in rows if r.email]
                total_attempts = sum(r.attempts for r in rows)

                await self.alert_brute_force_detected(
                    ip_address=ip_address,
                    target_emails=emails,
                    attempt_count=total_attempts,
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking for brute force: {e}")
            return False

    def is_after_hours(self) -> bool:
        """Check if current time is outside business hours"""
        now = datetime.now(timezone.utc)
        return now.hour < self.business_start or now.hour >= self.business_end

    # ============================================
    # IP Tracking and Monitoring
    # ============================================

    async def log_login_with_ip(
        self,
        user_id: str,
        email: str,
        ip_address: str,
        user_agent: str = None,
        success: bool = True,
    ) -> dict:
        """
        Log a login attempt with IP tracking and suspicious pattern detection.

        Returns dict with:
        - is_new_ip: Whether this is a new IP for this user
        - is_suspicious: Whether suspicious patterns were detected
        - alerts: List of alerts triggered
        """
        from services.ip_geolocation_service import IPGeolocationService

        alerts_triggered = []
        is_suspicious = False
        is_new_ip = False

        try:
            # Get IP geolocation
            geo_service = IPGeolocationService(self.db)
            geo = await geo_service.get_geolocation(ip_address)

            # Check if this is a new IP for the user
            is_new_ip = not await geo_service.is_ip_known_for_user(
                user_id, ip_address
            )

            if success:
                # === CHECK SUSPICIOUS PATTERNS (only on successful login) ===

                # 1. Check for geo-impossible travel
                if is_new_ip:
                    geo_alert = await self._check_geo_impossible_travel(
                        user_id, email, ip_address, geo
                    )
                    if geo_alert:
                        alerts_triggered.append(geo_alert)
                        is_suspicious = True

                # 2. Check for same IP hitting multiple accounts
                accounts_from_ip = await geo_service.count_accounts_from_ip_1h(
                    ip_address
                )
                if accounts_from_ip >= 3:
                    multi_alert = await self._alert_multi_account_ip(
                        ip_address, accounts_from_ip, email
                    )
                    alerts_triggered.append(multi_alert)
                    is_suspicious = True

                # 3. Check for bad IP reputation
                if geo.reputation_score < 30 or geo.is_tor or geo.is_proxy:
                    rep_alert = await self._alert_bad_ip_reputation(
                        user_id, email, ip_address, geo
                    )
                    alerts_triggered.append(rep_alert)
                    is_suspicious = True

                # 4. Check for excessive new IPs (3+ in 24 hours)
                if is_new_ip:
                    new_ips_24h = await geo_service.count_new_ips_24h(user_id)
                    if new_ips_24h >= 3:
                        excess_alert = await self._alert_excessive_new_ips(
                            user_id, email, ip_address, new_ips_24h
                        )
                        alerts_triggered.append(excess_alert)
                        is_suspicious = True

                # Register this IP as known for user
                await geo_service.register_user_ip(
                    user_id, ip_address, geo.country, geo.city
                )

            # Log login to history
            await self._log_login_history(
                user_id=user_id,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                geo=geo,
                is_new_ip=is_new_ip,
                is_suspicious=is_suspicious,
                success=success,
            )

            # Log security event
            event_type = (
                SecurityEventType.LOGIN_SUCCESS
                if success
                else SecurityEventType.LOGIN_FAILED
            )
            if is_new_ip and success:
                event_type = SecurityEventType.NEW_IP_LOGIN

            event = SecurityEvent(
                event_type=event_type,
                user_id=user_id,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                severity=(
                    AlertSeverity.HIGH if is_suspicious else AlertSeverity.LOW
                ),
                details={
                    "country": geo.country,
                    "city": geo.city,
                    "is_new_ip": is_new_ip,
                    "is_suspicious": is_suspicious,
                    "alerts_triggered": len(alerts_triggered),
                    "reputation_score": geo.reputation_score,
                },
            )
            await self.log_event(event)

            await geo_service.close()

            return {
                "is_new_ip": is_new_ip,
                "is_suspicious": is_suspicious,
                "alerts": alerts_triggered,
                "country": geo.country,
                "city": geo.city,
            }

        except Exception as e:
            logger.error(f"Error logging login with IP: {e}")
            return {
                "is_new_ip": False,
                "is_suspicious": False,
                "alerts": [],
                "error": str(e),
            }

    async def _log_login_history(
        self,
        user_id: str,
        email: str,
        ip_address: str,
        user_agent: str,
        geo,  # GeoLocation
        is_new_ip: bool,
        is_suspicious: bool,
        success: bool,
    ) -> None:
        """Log login to history table"""
        from services.ip_geolocation_service import IPGeolocationService

        try:
            # Generate device fingerprint
            geo_service = IPGeolocationService(self.db)
            device = geo_service.generate_device_fingerprint(
                user_agent or "", ip_address
            )

            query = text(
                """
                INSERT INTO security.login_history
                (user_id, email, ip_address, user_agent, country, city, latitude, longitude,
                 device_fingerprint, browser, os, device_type, is_new_ip, is_suspicious, success)
                VALUES
                (CAST(:user_id AS uuid), :email, :ip_address, :user_agent, :country, :city,
                 :latitude, :longitude, :device_fingerprint, :browser, :os, :device_type,
                 :is_new_ip, :is_suspicious, :success)
            """
            )

            await self.db.execute(
                query,
                {
                    "user_id": user_id,
                    "email": email,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "country": geo.country if geo else None,
                    "city": geo.city if geo else None,
                    "latitude": geo.latitude if geo else None,
                    "longitude": geo.longitude if geo else None,
                    "device_fingerprint": device.fingerprint,
                    "browser": device.browser,
                    "os": device.os,
                    "device_type": device.device_type,
                    "is_new_ip": is_new_ip,
                    "is_suspicious": is_suspicious,
                    "success": success,
                },
            )
            await self.db.commit()

        except Exception as e:
            logger.error(f"Error logging login history: {e}")
            await self.db.rollback()

    async def _check_geo_impossible_travel(
        self,
        user_id: str,
        email: str,
        ip_address: str,
        current_geo,  # GeoLocation
    ) -> Optional[str]:
        """
        Check for geo-impossible travel (login from distant location too quickly).

        Returns alert title if triggered, None otherwise.
        """
        from services.ip_geolocation_service import IPGeolocationService

        try:
            geo_service = IPGeolocationService(self.db)

            # Get last login
            last_login = await geo_service.get_last_login(user_id)
            if (
                not last_login
                or not last_login.get("latitude")
                or not current_geo.latitude
            ):
                return None

            # Calculate distance and time
            distance_km = geo_service.calculate_distance_km(
                last_login["latitude"],
                last_login["longitude"],
                current_geo.latitude,
                current_geo.longitude,
            )

            minutes_between = (
                datetime.now(timezone.utc) - last_login["login_at"]
            ).total_seconds() / 60

            # Check if travel is impossible
            if geo_service.is_geo_impossible(distance_km, minutes_between):
                severity = AlertSeverity.CRITICAL

                title = f"🌍 IMPOSSIBLE TRAVEL: {email}"
                message = f"""
Geo-impossible travel detected!

User: {email}
Previous: {last_login.get('city', 'Unknown')}, {last_login.get('country', 'Unknown')}
Current: {current_geo.city or 'Unknown'}, {current_geo.country or 'Unknown'}
Distance: {distance_km:.0f} km
Time gap: {minutes_between:.0f} minutes

This would require traveling at {distance_km / (minutes_between / 60):.0f} km/h!

IP: {ip_address}
Previous IP: {last_login.get('ip_address')}

This may indicate account compromise.
                """.strip()

                # Log event
                event = SecurityEvent(
                    event_type=SecurityEventType.GEO_IMPOSSIBLE_TRAVEL,
                    user_id=user_id,
                    email=email,
                    ip_address=ip_address,
                    severity=severity,
                    details={
                        "distance_km": distance_km,
                        "minutes_between": minutes_between,
                        "previous_city": last_login.get("city"),
                        "current_city": current_geo.city,
                    },
                )
                await self.log_event(event)

                # Create alert
                alert = AdminAlert(
                    title=title,
                    message=message,
                    severity=severity,
                    event_type=SecurityEventType.GEO_IMPOSSIBLE_TRAVEL,
                    user_id=user_id,
                    email=email,
                    ip_address=ip_address,
                    requires_action=True,
                )
                await self.create_dashboard_alert(alert)

                # Send notifications
                await self.send_email_alert(title, message, severity)
                await self.send_whatsapp_alert(message, severity)

                logger.critical(f"Geo-impossible travel detected for {email}")
                return title

            return None

        except Exception as e:
            logger.error(f"Error checking geo-impossible travel: {e}")
            return None

    async def _alert_multi_account_ip(
        self,
        ip_address: str,
        account_count: int,
        current_email: str,
    ) -> str:
        """Alert when same IP is used by multiple accounts"""
        severity = AlertSeverity.HIGH

        title = f"⚠️ Multi-Account IP: {ip_address}"
        message = f"""
Same IP address used by multiple accounts!

IP Address: {ip_address}
Accounts logged in (last hour): {account_count}
Most recent: {current_email}

This may indicate:
• Shared VPN or corporate network (normal)
• Account sharing (policy violation)
• Credential stuffing attack (if many failures)

Review the login history for this IP.
        """.strip()

        event = SecurityEvent(
            event_type=SecurityEventType.MULTI_ACCOUNT_IP,
            ip_address=ip_address,
            email=current_email,
            severity=severity,
            details={"account_count": account_count},
        )
        await self.log_event(event)

        alert = AdminAlert(
            title=title,
            message=message,
            severity=severity,
            event_type=SecurityEventType.MULTI_ACCOUNT_IP,
            ip_address=ip_address,
            email=current_email,
        )
        await self.create_dashboard_alert(alert)

        logger.warning(
            f"Multi-account IP alert: {ip_address} with {account_count} accounts"
        )
        return title

    async def _alert_bad_ip_reputation(
        self,
        user_id: str,
        email: str,
        ip_address: str,
        geo,  # GeoLocation
    ) -> str:
        """Alert when login from IP with bad reputation"""
        severity = AlertSeverity.HIGH

        flags = []
        if geo.is_tor:
            flags.append("TOR exit node")
        if geo.is_proxy:
            flags.append("Known proxy")
        if geo.is_vpn:
            flags.append("VPN/Datacenter")
        if geo.reputation_score < 30:
            flags.append(f"Low reputation ({geo.reputation_score}/100)")

        title = f"🚩 Bad IP Reputation: {email}"
        message = f"""
Login from suspicious IP address!

User: {email}
IP: {ip_address}
Location: {geo.city or 'Unknown'}, {geo.country or 'Unknown'}
ISP: {geo.isp or 'Unknown'}

Flags:
{chr(10).join(['• ' + f for f in flags])}

This may indicate:
• User using VPN (may be normal)
• Compromised account
• Automated attack
        """.strip()

        event = SecurityEvent(
            event_type=SecurityEventType.BAD_IP_REPUTATION,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            severity=severity,
            details={
                "reputation_score": geo.reputation_score,
                "is_tor": geo.is_tor,
                "is_proxy": geo.is_proxy,
                "is_vpn": geo.is_vpn,
                "flags": flags,
            },
        )
        await self.log_event(event)

        alert = AdminAlert(
            title=title,
            message=message,
            severity=severity,
            event_type=SecurityEventType.BAD_IP_REPUTATION,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
        )
        await self.create_dashboard_alert(alert)

        logger.warning(f"Bad IP reputation alert: {email} from {ip_address}")
        return title

    async def _alert_excessive_new_ips(
        self,
        user_id: str,
        email: str,
        ip_address: str,
        new_ip_count: int,
    ) -> str:
        """Alert when user logs in from many new IPs in 24 hours"""
        severity = AlertSeverity.MEDIUM

        title = f"📍 Excessive New IPs: {email}"
        message = f"""
User logging in from many new IP addresses!

User: {email}
New IPs in last 24h: {new_ip_count}
Latest new IP: {ip_address}

This may indicate:
• Traveling user (normal)
• VPN hopping (may be normal)
• Account credentials shared/stolen

Consider contacting user to verify.
        """.strip()

        event = SecurityEvent(
            event_type=SecurityEventType.EXCESSIVE_NEW_IPS,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            severity=severity,
            details={"new_ip_count": new_ip_count},
        )
        await self.log_event(event)

        alert = AdminAlert(
            title=title,
            message=message,
            severity=severity,
            event_type=SecurityEventType.EXCESSIVE_NEW_IPS,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
        )
        await self.create_dashboard_alert(alert)

        logger.info(
            f"Excessive new IPs alert: {email} with {new_ip_count} new IPs"
        )
        return title

    async def get_user_login_history(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[dict]:
        """Get login history for a specific user"""
        query = text(
            """
            SELECT
                id, ip_address, user_agent, country, city,
                device_fingerprint, browser, os, device_type,
                is_new_ip, is_suspicious, success, login_at
            FROM security.login_history
            WHERE user_id = CAST(:user_id AS uuid)
            ORDER BY login_at DESC
            LIMIT :limit
        """
        )

        try:
            result = await self.db.execute(
                query,
                {
                    "user_id": user_id,
                    "limit": limit,
                },
            )
            rows = result.fetchall()

            return [
                {
                    "id": str(row.id),
                    "ip_address": row.ip_address,
                    "user_agent": row.user_agent,
                    "country": row.country,
                    "city": row.city,
                    "device_fingerprint": row.device_fingerprint,
                    "browser": row.browser,
                    "os": row.os,
                    "device_type": row.device_type,
                    "is_new_ip": row.is_new_ip,
                    "is_suspicious": row.is_suspicious,
                    "success": row.success,
                    "login_at": (
                        row.login_at.isoformat() if row.login_at else None
                    ),
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error getting login history: {e}")
            return []

    async def get_ip_login_history(
        self,
        ip_address: str,
        limit: int = 50,
    ) -> list[dict]:
        """Get all logins from a specific IP address"""
        query = text(
            """
            SELECT
                id, user_id, email, user_agent, country, city,
                browser, os, device_type, is_suspicious, success, login_at
            FROM security.login_history
            WHERE ip_address = :ip_address
            ORDER BY login_at DESC
            LIMIT :limit
        """
        )

        try:
            result = await self.db.execute(
                query,
                {
                    "ip_address": ip_address,
                    "limit": limit,
                },
            )
            rows = result.fetchall()

            return [
                {
                    "id": str(row.id),
                    "user_id": str(row.user_id) if row.user_id else None,
                    "email": row.email,
                    "user_agent": row.user_agent,
                    "country": row.country,
                    "city": row.city,
                    "browser": row.browser,
                    "os": row.os,
                    "device_type": row.device_type,
                    "is_suspicious": row.is_suspicious,
                    "success": row.success,
                    "login_at": (
                        row.login_at.isoformat() if row.login_at else None
                    ),
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error getting IP login history: {e}")
            return []


# ============================================
# Dependency Injection Helper
# ============================================


async def get_security_service(db: AsyncSession) -> SecurityMonitoringService:
    """Get security monitoring service instance"""
    return SecurityMonitoringService(db)
