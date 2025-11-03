"""
Admin Alert Service

Handles escalation and notifications to administrators for critical issues
that require human intervention.
"""

from datetime import datetime
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class AdminAlertService:
    """Service for sending alerts to administrators"""

    ALERT_TYPES = {
        "API_ERROR": "API Service Error",
        "PRICING_ERROR": "Pricing Calculation Error",
        "BOOKING_CONFLICT": "Booking Conflict",
        "CUSTOMER_ESCALATION": "Customer Inquiry Escalation",
        "SYSTEM_ERROR": "System Error",
    }

    PRIORITY_LEVELS = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

    def __init__(self):
        self.admin_email = os.getenv("ADMIN_EMAIL", "admin@yourcompany.com")
        self.admin_phone = os.getenv("ADMIN_PHONE", "(916) 740-8768")
        self.whatsapp_webhook = os.getenv("WHATSAPP_WEBHOOK_URL")
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")

    def send_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        priority: str = "MEDIUM",
        customer_info: dict[str, Any] | None = None,
        error_details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send alert to administrators through multiple channels

        Args:
            alert_type: Type of alert (API_ERROR, PRICING_ERROR, etc.)
            title: Short title of the issue
            message: Detailed message
            priority: LOW, MEDIUM, HIGH, CRITICAL
            customer_info: Optional customer details
            error_details: Optional technical error details

        Returns:
            Dict with alert status
        """
        alert_data = {
            "alert_id": f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": alert_type,
            "type_label": self.ALERT_TYPES.get(alert_type, "Unknown"),
            "title": title,
            "message": message,
            "priority": priority,
            "priority_level": self.PRIORITY_LEVELS.get(priority, 2),
            "timestamp": datetime.now().isoformat(),
            "customer_info": customer_info,
            "error_details": error_details,
            "channels_notified": [],
        }

        # Log the alert
        log_message = f"[{priority}] {title}: {message}"
        if priority in ["HIGH", "CRITICAL"]:
            logger.error(log_message)
        else:
            logger.warning(log_message)

        # Send to various channels based on priority
        try:
            # Always log to database (for admin dashboard)
            self._log_to_database(alert_data)
            alert_data["channels_notified"].append("database")

            # Send email for MEDIUM and above
            if self.PRIORITY_LEVELS.get(priority, 2) >= 2:
                self._send_email_alert(alert_data)
                alert_data["channels_notified"].append("email")

            # Send WhatsApp for HIGH and CRITICAL
            if self.PRIORITY_LEVELS.get(priority, 2) >= 3:
                if self.whatsapp_webhook:
                    self._send_whatsapp_alert(alert_data)
                    alert_data["channels_notified"].append("whatsapp")

            # Send Slack notification
            if self.slack_webhook:
                self._send_slack_alert(alert_data)
                alert_data["channels_notified"].append("slack")

        except Exception as e:
            logger.exception(f"Error sending admin alert: {e}")

        return alert_data

    def alert_api_error(
        self,
        service_name: str,
        error_message: str,
        customer_name: str | None = None,
        customer_email: str | None = None,
        customer_address: str | None = None,
    ) -> dict[str, Any]:
        """
        Alert administrators about API service errors

        Args:
            service_name: Name of the failed service (e.g., "Google Maps")
            error_message: Technical error message
            customer_name: Customer affected by the error
            customer_email: Customer email for follow-up
            customer_address: Address that caused the error

        Returns:
            Dict with alert status
        """
        customer_info = None
        if customer_name:
            customer_info = {
                "name": customer_name,
                "email": customer_email,
                "address": customer_address,
            }

        return self.send_alert(
            alert_type="API_ERROR",
            title=f"{service_name} API Error",
            message=f"""
⚠️ {service_name} API Error - Requires Admin Attention

Error: {error_message}

{f"Customer: {customer_name} ({customer_email})" if customer_name else ""}
{f"Address: {customer_address}" if customer_address else ""}

Action Required:
1. Verify {service_name} API credentials and status
2. Contact customer with manual quote if needed
3. Check service status dashboard

Customer has been provided with phone number for manual quote.
            """.strip(),
            priority="HIGH",
            customer_info=customer_info,
            error_details={"service": service_name, "error": error_message},
        )

    def alert_pricing_error(
        self, error_type: str, details: str, customer_name: str | None = None
    ) -> dict[str, Any]:
        """Alert about pricing calculation errors"""
        return self.send_alert(
            alert_type="PRICING_ERROR",
            title=f"Pricing Error: {error_type}",
            message=f"Pricing calculation issue: {details}\nCustomer: {customer_name or 'Unknown'}",
            priority="HIGH",
            customer_info={"name": customer_name} if customer_name else None,
        )

    def alert_booking_conflict(
        self, date: str, time_slot: str, customer_name: str, conflict_details: str
    ) -> dict[str, Any]:
        """Alert about booking conflicts"""
        return self.send_alert(
            alert_type="BOOKING_CONFLICT",
            title=f"Booking Conflict on {date}",
            message=f"""
Booking conflict detected:

Date: {date}
Time Slot: {time_slot}
Customer: {customer_name}

Details: {conflict_details}

Action Required: Review chef availability and contact customer.
            """.strip(),
            priority="HIGH",
            customer_info={"name": customer_name},
        )

    def escalate_to_human(
        self,
        reason: str,
        customer_name: str,
        customer_email: str,
        customer_message: str,
        ai_confidence: float | None = None,
    ) -> dict[str, Any]:
        """Escalate customer inquiry to human admin"""
        confidence_info = f"\nAI Confidence: {ai_confidence:.1%}" if ai_confidence else ""

        return self.send_alert(
            alert_type="CUSTOMER_ESCALATION",
            title="Customer Inquiry Requires Human Review",
            message=f"""
🤝 Customer Inquiry Escalation

Reason: {reason}
Customer: {customer_name}
Email: {customer_email}{confidence_info}

Original Message:
{customer_message}

Action Required:
1. Review customer inquiry in Admin Dashboard
2. Provide personalized response
3. Update AI training if pattern repeats
            """.strip(),
            priority="MEDIUM",
            customer_info={
                "name": customer_name,
                "email": customer_email,
                "message": customer_message,
                "ai_confidence": ai_confidence,
            },
        )

    def _log_to_database(self, alert_data: dict[str, Any]) -> None:
        """
        Log alert to database for admin dashboard

        TODO: Implement database logging
        Currently logs to file until admin_alerts table is created
        """
        try:
            # Write to alerts log file
            log_dir = os.path.join(os.path.dirname(__file__), "../../../../../logs")
            os.makedirs(log_dir, exist_ok=True)

            log_file = os.path.join(log_dir, "admin_alerts.log")
            with open(log_file, "a") as f:
                f.write(f"{alert_data}\n")
        except Exception as e:
            logger.exception(f"Failed to log alert to database: {e}")

    def _send_email_alert(self, alert_data: dict[str, Any]) -> None:
        """
        Send email alert to administrators

        TODO: Integrate with email service
        """
        logger.info(f"EMAIL ALERT: {alert_data['title']} (Priority: {alert_data['priority']})")
        # Email integration to be implemented

    def _send_whatsapp_alert(self, alert_data: dict[str, Any]) -> None:
        """
        Send WhatsApp notification to administrators

        TODO: Integrate with WhatsApp Business API
        """
        if not self.whatsapp_webhook:
            return

        f"""
🚨 {alert_data['priority']} Priority Alert

{alert_data['title']}

{alert_data['message']}

Alert ID: {alert_data['alert_id']}
Time: {alert_data['timestamp']}
        """.strip()

        logger.info(f"WHATSAPP ALERT: {alert_data['title']}")
        # WhatsApp integration to be implemented

    def _send_slack_alert(self, alert_data: dict[str, Any]) -> None:
        """
        Send Slack notification

        TODO: Integrate with Slack webhook
        """
        if not self.slack_webhook:
            return

        logger.info(f"SLACK ALERT: {alert_data['title']}")
        # Slack integration to be implemented


# Singleton instance
_admin_alert_service = None


def get_admin_alert_service() -> AdminAlertService:
    """Get singleton instance of AdminAlertService"""
    global _admin_alert_service
    if _admin_alert_service is None:
        _admin_alert_service = AdminAlertService()
    return _admin_alert_service
