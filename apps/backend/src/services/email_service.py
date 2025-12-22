"""
Email Notification Service with SMTP and Resend API support
Sends emails for user approval, rejection, booking confirmations, and other events

Supports two providers:
1. SMTP (IONOS webmail) - Default, uses cs@myhibachichef.com
2. Resend API - Optional, higher deliverability

Configuration:
- EMAIL_ENABLED=true to enable email sending
- EMAIL_PROVIDER=smtp|resend (default: smtp)
- SMTP_HOST, SMTP_PORT, SMTP_FROM_EMAIL, SMTP_PASSWORD for SMTP
- RESEND_API_KEY, RESEND_FROM_EMAIL for Resend
"""

from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
import smtplib
import ssl
from typing import Optional

try:
    import resend
except ImportError:
    resend = None

logger = logging.getLogger(__name__)

# Email templates
EMAIL_TEMPLATES = {
    "approval": {
        "subject": "Your MyHibachi Account Has Been Approved! 🎉",
        "html": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2563eb; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
        .button {{ background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Welcome to MyHibachi!</h1>
        </div>
        <div class="content">
            <h2>Hello {full_name},</h2>
            <p>Great news! Your MyHibachi account has been approved by our administrator.</p>
            <p>You can now access the full admin dashboard and start managing your business.</p>
            <p style="text-align: center;">
                <a href="{frontend_url}/login" class="button">Login to Dashboard</a>
            </p>
            <p><strong>Your account details:</strong></p>
            <ul>
                <li>Email: {email}</li>
                <li>Account Status: Active</li>
                <li>Approved Date: {approval_date}</li>
            </ul>
            <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
        </div>
        <div class="footer">
            <p>© 2025 MyHibachi Chef. All rights reserved.</p>
            <p>If you didn't request this account, please ignore this email.</p>
        </div>
    </div>
</body>
</html>
        """,
        "text": """
Hello {full_name},

Great news! Your MyHibachi account has been approved by our administrator.

You can now access the full admin dashboard at: {frontend_url}/login

Your account details:
- Email: {email}
- Account Status: Active
- Approved Date: {approval_date}

If you have any questions or need assistance, please contact our support team.

© 2025 MyHibachi Chef. All rights reserved.
        """,
    },
    "rejection": {
        "subject": "MyHibachi Account Application Update",
        "html": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #dc2626; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
        .button {{ background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Account Application Update</h1>
        </div>
        <div class="content">
            <h2>Hello {full_name},</h2>
            <p>Thank you for your interest in MyHibachi.</p>
            <p>Unfortunately, we are unable to approve your account application at this time.</p>
            {reason_html}
            <p>If you believe this is an error or would like to discuss your application further, please contact our support team.</p>
            <p style="text-align: center;">
                <a href="mailto:support@myhibachi.com" class="button">Contact Support</a>
            </p>
        </div>
        <div class="footer">
            <p>© 2025 MyHibachi Chef. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """,
        "text": """
Hello {full_name},

Thank you for your interest in MyHibachi.

Unfortunately, we are unable to approve your account application at this time.

{reason_text}

If you believe this is an error or would like to discuss your application, please contact us at support@myhibachi.com.

© 2025 MyHibachi Chef. All rights reserved.
        """,
    },
    "suspension": {
        "subject": "MyHibachi Account Suspended",
        "html": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f59e0b; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
        .button {{ background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Account Suspended</h1>
        </div>
        <div class="content">
            <h2>Hello {full_name},</h2>
            <p>Your MyHibachi account has been temporarily suspended.</p>
            {reason_html}
            <p>During this suspension period, you will not be able to access the admin dashboard.</p>
            <p>If you would like to discuss this suspension or request reinstatement, please contact our support team.</p>
            <p style="text-align: center;">
                <a href="mailto:support@myhibachi.com" class="button">Contact Support</a>
            </p>
        </div>
        <div class="footer">
            <p>© 2025 MyHibachi Chef. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """,
        "text": """
Hello {full_name},

Your MyHibachi account has been temporarily suspended.

{reason_text}

During this suspension period, you will not be able to access the admin dashboard.

If you would like to discuss this suspension, please contact us at support@myhibachi.com.

© 2025 MyHibachi Chef. All rights reserved.
        """,
    },
    "welcome": {
        "subject": "Welcome to MyHibachi! Your Account is Pending Approval",
        "html": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2563eb; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
        .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to MyHibachi!</h1>
        </div>
        <div class="content">
            <h2>Hello {full_name},</h2>
            <p>Thank you for signing up with MyHibachi using your Google account!</p>
            <p>Your account has been created successfully and is currently pending approval from our administrator.</p>
            <p><strong>What happens next?</strong></p>
            <ul>
                <li>Our team will review your account details</li>
                <li>You'll receive an email notification once approved (typically 1-2 business days)</li>
                <li>After approval, you'll be able to access the full admin dashboard</li>
            </ul>
            <p>If you need immediate access or have any questions, please contact our support team.</p>
        </div>
        <div class="footer">
            <p>© 2025 MyHibachi Chef. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """,
        "text": """
Hello {full_name},

Thank you for signing up with MyHibachi using your Google account!

Your account has been created successfully and is currently pending approval from our administrator.

What happens next?
- Our team will review your account details
- You'll receive an email notification once approved (typically 1-2 business days)
- After approval, you'll be able to access the full admin dashboard

If you need immediate access, please contact us at support@myhibachi.com.

© 2025 MyHibachi Chef. All rights reserved.
        """,
    },
    "new_booking_customer": {
        "subject": "🎉 Your Hibachi Booking Confirmed! - My Hibachi Chef",
        "html": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #16a34a; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
        .details {{ background-color: #ffffff; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #e5e7eb; }}
        .detail-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f3f4f6; }}
        .button {{ background-color: #16a34a; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px; }}
        .warning {{ background-color: #fef3c7; border: 1px solid #f59e0b; padding: 15px; border-radius: 6px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Booking Confirmed!</h1>
        </div>
        <div class="content">
            <h2>Hello {customer_name},</h2>
            <p>Thank you for choosing My Hibachi Chef! Your hibachi party is booked and we can't wait to cook for you!</p>
            
            <div class="details">
                <h3>📋 Booking Details</h3>
                <div class="detail-row"><span><strong>Booking #:</strong></span><span>{booking_id}</span></div>
                <div class="detail-row"><span><strong>Date:</strong></span><span>{event_date}</span></div>
                <div class="detail-row"><span><strong>Time:</strong></span><span>{event_time}</span></div>
                <div class="detail-row"><span><strong>Guests:</strong></span><span>~{guest_count} people</span></div>
                <div class="detail-row"><span><strong>Location:</strong></span><span>{location}</span></div>
            </div>
            
            <div class="warning">
                <strong>⚠️ Allergen Notice:</strong> We use shared cooking surfaces and cannot guarantee 100% allergen-free meals. 
                Please reply to this email with any allergies or dietary restrictions.
            </div>
            
            <p><strong>What's Next?</strong></p>
            <ul>
                <li>Pay your $100 deposit within 2 hours to confirm</li>
                <li>We'll send a reminder before your event</li>
                <li>Our chef will arrive 30 mins early to set up</li>
            </ul>
            
            <p>Questions? Reply to this email or call us at <strong>(916) 740-8768</strong></p>
        </div>
        <div class="footer">
            <p>© 2025 My Hibachi Chef. All rights reserved.</p>
            <p>Northern California's Premier Hibachi Catering</p>
        </div>
    </div>
</body>
</html>
        """,
        "text": """
Hello {customer_name},

🎉 BOOKING CONFIRMED!

Thank you for choosing My Hibachi Chef! Your hibachi party is booked.

BOOKING DETAILS:
- Booking #: {booking_id}
- Date: {event_date}
- Time: {event_time}
- Guests: ~{guest_count} people
- Location: {location}

⚠️ ALLERGEN NOTICE: We use shared cooking surfaces and cannot guarantee 100% allergen-free. 
Please reply with any allergies or dietary restrictions.

WHAT'S NEXT:
1. Pay your $100 deposit within 2 hours to confirm
2. We'll send a reminder before your event
3. Our chef will arrive 30 mins early to set up

Questions? Reply to this email or call (916) 740-8768

© 2025 My Hibachi Chef. Northern California's Premier Hibachi Catering.
        """,
    },
    "new_booking_admin": {
        "subject": "🆕 New Booking Alert! - {customer_name} on {event_date}",
        "html": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2563eb; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
        .details {{ background-color: #ffffff; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #e5e7eb; }}
        .button {{ background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px; }}
        .urgent {{ color: #dc2626; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🆕 New Booking Received!</h1>
        </div>
        <div class="content">
            <p class="urgent">Action Required: Assign chef and confirm booking</p>
            
            <div class="details">
                <h3>📋 Booking Details</h3>
                <p><strong>Booking #:</strong> {booking_id}</p>
                <p><strong>Customer:</strong> {customer_name}</p>
                <p><strong>Phone:</strong> {customer_phone}</p>
                <p><strong>Email:</strong> {customer_email}</p>
                <p><strong>Date:</strong> {event_date}</p>
                <p><strong>Time:</strong> {event_time}</p>
                <p><strong>Guests:</strong> ~{guest_count} people</p>
                <p><strong>Location:</strong> {location}</p>
                <p><strong>Special Requests:</strong> {special_requests}</p>
            </div>
            
            <p style="text-align: center;">
                <a href="{admin_url}/bookings/{booking_id}" class="button">View in Admin Portal</a>
            </p>
        </div>
        <div class="footer">
            <p>This is an automated notification from My Hibachi Chef booking system.</p>
        </div>
    </div>
</body>
</html>
        """,
        "text": """
🆕 NEW BOOKING RECEIVED!

Action Required: Assign chef and confirm booking

BOOKING DETAILS:
- Booking #: {booking_id}
- Customer: {customer_name}
- Phone: {customer_phone}
- Email: {customer_email}
- Date: {event_date}
- Time: {event_time}
- Guests: ~{guest_count} people
- Location: {location}
- Special Requests: {special_requests}

View in admin portal: {admin_url}/bookings/{booking_id}

This is an automated notification from My Hibachi Chef booking system.
        """,
    },
}


class EmailService:
    """Service for sending email notifications using SMTP or Resend API"""

    def __init__(self):
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
        self.provider = os.getenv("EMAIL_PROVIDER", "smtp").lower()  # smtp or resend
        self.from_name = os.getenv("EMAIL_FROM_NAME", "My Hibachi Chef")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")

        # SMTP Configuration (IONOS)
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.ionos.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_from_email = os.getenv("SMTP_FROM_EMAIL", "cs@myhibachichef.com")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")

        # Resend Configuration (fallback)
        self.resend_api_key = os.getenv("RESEND_API_KEY")
        self.resend_from_email = os.getenv("RESEND_FROM_EMAIL", "cs@myhibachichef.com")

        # Determine active from_email based on provider
        if self.provider == "resend":
            self.from_email = self.resend_from_email
        else:
            self.from_email = self.smtp_from_email

        # Initialize based on provider
        if not self.enabled:
            logger.info("📧 Email service disabled (EMAIL_ENABLED=false)")
        elif self.provider == "smtp":
            if self.smtp_host and self.smtp_password:
                logger.info(
                    f"✅ SMTP email service initialized (host: {self.smtp_host}, from: {self.from_email})"
                )
            else:
                logger.error(
                    "❌ EMAIL_ENABLED=true with SMTP but missing SMTP_HOST or SMTP_PASSWORD"
                )
        elif self.provider == "resend":
            if self.resend_api_key and resend:
                resend.api_key = self.resend_api_key
                logger.info(f"✅ Resend email service initialized (from: {self.from_email})")
            elif not self.resend_api_key:
                logger.error("❌ EMAIL_PROVIDER=resend but RESEND_API_KEY not found")
            elif not resend:
                logger.error("❌ EMAIL_PROVIDER=resend but resend library not installed")
        else:
            logger.warning(f"⚠️ Unknown EMAIL_PROVIDER={self.provider}, defaulting to smtp")
            self.provider = "smtp"

    def _format_sender(self) -> str:
        """Format sender email with name"""
        return f"{self.from_name} <{self.from_email}>"

    def send_approval_email(self, email: str, full_name: str) -> bool:
        """Send approval notification email"""
        try:
            template = EMAIL_TEMPLATES["approval"]
            html_body = template["html"].format(
                full_name=full_name,
                email=email,
                frontend_url=self.frontend_url,
                approval_date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
            )
            text_body = template["text"].format(
                full_name=full_name,
                email=email,
                frontend_url=self.frontend_url,
                approval_date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
            )

            return self._send_email(
                to_email=email,
                subject=template["subject"],
                html_body=html_body,
                text_body=text_body,
            )
        except Exception as e:
            logger.exception(f"Failed to send approval email to {email}: {e}")
            return False

    def send_rejection_email(self, email: str, full_name: str, reason: str | None = None) -> bool:
        """Send rejection notification email"""
        try:
            template = EMAIL_TEMPLATES["rejection"]

            reason_html = ""
            reason_text = ""
            if reason:
                reason_html = f"<p><strong>Reason:</strong> {reason}</p>"
                reason_text = f"Reason: {reason}\n"

            html_body = template["html"].format(full_name=full_name, reason_html=reason_html)
            text_body = template["text"].format(full_name=full_name, reason_text=reason_text)

            return self._send_email(
                to_email=email,
                subject=template["subject"],
                html_body=html_body,
                text_body=text_body,
            )
        except Exception as e:
            logger.exception(f"Failed to send rejection email to {email}: {e}")
            return False

    def send_suspension_email(self, email: str, full_name: str, reason: str | None = None) -> bool:
        """Send suspension notification email"""
        try:
            template = EMAIL_TEMPLATES["suspension"]

            reason_html = ""
            reason_text = ""
            if reason:
                reason_html = f"<p><strong>Reason:</strong> {reason}</p>"
                reason_text = f"Reason: {reason}\n"

            html_body = template["html"].format(full_name=full_name, reason_html=reason_html)
            text_body = template["text"].format(full_name=full_name, reason_text=reason_text)

            return self._send_email(
                to_email=email,
                subject=template["subject"],
                html_body=html_body,
                text_body=text_body,
            )
        except Exception as e:
            logger.exception(f"Failed to send suspension email to {email}: {e}")
            return False

    def send_welcome_email(self, email: str, full_name: str) -> bool:
        """Send welcome email for new registrations"""
        try:
            template = EMAIL_TEMPLATES["welcome"]
            html_body = template["html"].format(full_name=full_name)
            text_body = template["text"].format(full_name=full_name)

            return self._send_email(
                to_email=email,
                subject=template["subject"],
                html_body=html_body,
                text_body=text_body,
            )
        except Exception as e:
            logger.exception(f"Failed to send welcome email to {email}: {e}")
            return False

    def send_new_booking_email_to_customer(
        self,
        customer_email: str,
        customer_name: str,
        booking_id: str,
        event_date: str,
        event_time: str,
        guest_count: int,
        location: str,
    ) -> bool:
        """Send booking confirmation email to customer"""
        try:
            template = EMAIL_TEMPLATES["new_booking_customer"]
            html_body = template["html"].format(
                customer_name=customer_name,
                booking_id=booking_id,
                event_date=event_date,
                event_time=event_time,
                guest_count=guest_count,
                location=location,
            )
            text_body = template["text"].format(
                customer_name=customer_name,
                booking_id=booking_id,
                event_date=event_date,
                event_time=event_time,
                guest_count=guest_count,
                location=location,
            )

            return self._send_email(
                to_email=customer_email,
                subject=template["subject"],
                html_body=html_body,
                text_body=text_body,
                tags=[{"name": "type", "value": "booking_confirmation"}],
            )
        except Exception as e:
            logger.exception(f"Failed to send booking confirmation email to {customer_email}: {e}")
            return False

    def send_new_booking_email_to_admin(
        self,
        admin_email: str,
        customer_name: str,
        customer_phone: str,
        customer_email: str,
        booking_id: str,
        event_date: str,
        event_time: str,
        guest_count: int,
        location: str,
        special_requests: str | None = None,
    ) -> bool:
        """Send new booking alert email to admin"""
        try:
            template = EMAIL_TEMPLATES["new_booking_admin"]
            admin_url = os.getenv("ADMIN_URL", "https://admin.mysticdatanode.net")

            subject = template["subject"].format(
                customer_name=customer_name,
                event_date=event_date,
            )
            html_body = template["html"].format(
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                booking_id=booking_id,
                event_date=event_date,
                event_time=event_time,
                guest_count=guest_count,
                location=location,
                special_requests=special_requests or "None",
                admin_url=admin_url,
            )
            text_body = template["text"].format(
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                booking_id=booking_id,
                event_date=event_date,
                event_time=event_time,
                guest_count=guest_count,
                location=location,
                special_requests=special_requests or "None",
                admin_url=admin_url,
            )

            return self._send_email(
                to_email=admin_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                tags=[{"name": "type", "value": "booking_admin_alert"}],
            )
        except Exception as e:
            logger.exception(f"Failed to send booking alert email to admin {admin_email}: {e}")
            return False

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
        tags: Optional[list] = None,
    ) -> bool:
        """Internal method to send email via SMTP or Resend API"""
        if not self.enabled:
            logger.info(f"📧 Email disabled. Would send to {to_email}: {subject}")
            logger.debug(f"Email preview:\n{text_body[:200]}...")
            return True

        # Route to appropriate provider
        if self.provider == "smtp":
            return self._send_via_smtp(to_email, subject, html_body, text_body)
        else:
            return self._send_via_resend(to_email, subject, html_body, text_body, tags)

    def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> bool:
        """Send email via SMTP (IONOS)"""
        if not self.smtp_host or not self.smtp_password:
            logger.error("❌ Cannot send email: SMTP not configured properly")
            return False

        try:
            # Create multipart message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self._format_sender()
            msg["To"] = to_email

            # Attach both text and HTML versions
            part1 = MIMEText(text_body, "plain", "utf-8")
            part2 = MIMEText(html_body, "html", "utf-8")
            msg.attach(part1)
            msg.attach(part2)

            # Create secure SSL/TLS context
            context = ssl.create_default_context()

            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_from_email, self.smtp_password)
                server.sendmail(self.smtp_from_email, to_email, msg.as_string())

            logger.info(f"✅ Email sent via SMTP to {to_email} | Subject: {subject}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP authentication failed for {self.smtp_from_email}: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.exception(f"❌ SMTP error sending to {to_email}: {e}")
            return False
        except Exception as e:
            logger.exception(f"❌ Failed to send email via SMTP to {to_email}: {e}")
            return False

    def _send_via_resend(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
        tags: Optional[list] = None,
    ) -> bool:
        """Send email via Resend API"""
        if not self.resend_api_key or not resend:
            logger.error("❌ Cannot send email: Resend not configured properly")
            return False

        try:
            # Prepare email parameters
            params = {
                "from": self._format_sender(),
                "to": [to_email],
                "subject": subject,
                "html": html_body,
                "text": text_body,
            }

            # Add tags if provided
            if tags:
                params["tags"] = tags

            # Send via Resend API
            response = resend.Emails.send(params)

            logger.info(
                f"✅ Email sent via Resend to {to_email} | Subject: {subject} | ID: {response.get('id', 'N/A')}"
            )
            return True

        except Exception as e:
            logger.exception(f"❌ Failed to send email via Resend to {to_email}: {e}")
            return False


# Global email service instance
email_service = EmailService()
