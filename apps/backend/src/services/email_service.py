"""
Email Notification Service
Sends emails for user approval, rejection, and other events
Supports SMTP for IONOS and other providers
"""
from typing import Optional
import logging
from datetime import datetime
import os
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
        """
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
        """
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
        """
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
        """
    }
}


class EmailService:
    """Service for sending email notifications with SMTP support"""
    
    def __init__(self):
        self.enabled = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "false").lower() == "true"
        self.from_email = os.getenv("EMAIL_FROM_ADDRESS", "cs@myhibachichef.com")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "MyHibachi Chef")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        
        # Email routing configuration
        self.customer_smtp = "ionos"  # Use IONOS for customer emails
        self.admin_smtp = "gmail"     # Use Gmail for internal admin emails
        self.admin_domain = "@myhibachichef.com"  # Internal domain
        
        logger.info(f"Email service initialized (enabled={self.enabled})")
        if self.enabled:
            logger.info(f"Customer emails via: {self.customer_smtp}")
            logger.info(f"Admin emails via: {self.admin_smtp}")
    
    def _is_admin_email(self, email: str) -> bool:
        """Check if email is an admin/internal email"""
        email_lower = email.lower()
        return (
            email.endswith(self.admin_domain) or 
            email_lower == "myhibachichef@gmail.com" or  # Specific business Gmail only
            "admin" in email_lower or
            "staff" in email_lower
        )
    
    def _get_smtp_provider(self, to_email: str) -> str:
        """Automatically select SMTP provider based on recipient"""
        if self._is_admin_email(to_email):
            return self.admin_smtp
        return self.customer_smtp
        
    def send_approval_email(self, email: str, full_name: str) -> bool:
        """Send approval notification email"""
        try:
            template = EMAIL_TEMPLATES["approval"]
            html_body = template["html"].format(
                full_name=full_name,
                email=email,
                frontend_url=self.frontend_url,
                approval_date=datetime.utcnow().strftime("%B %d, %Y")
            )
            text_body = template["text"].format(
                full_name=full_name,
                email=email,
                frontend_url=self.frontend_url,
                approval_date=datetime.utcnow().strftime("%B %d, %Y")
            )
            
            return self._send_email(
                to_email=email,
                subject=template["subject"],
                html_body=html_body,
                text_body=text_body
            )
        except Exception as e:
            logger.error(f"Failed to send approval email to {email}: {e}")
            return False
    
    def send_rejection_email(self, email: str, full_name: str, reason: Optional[str] = None) -> bool:
        """Send rejection notification email"""
        try:
            template = EMAIL_TEMPLATES["rejection"]
            
            reason_html = ""
            reason_text = ""
            if reason:
                reason_html = f"<p><strong>Reason:</strong> {reason}</p>"
                reason_text = f"Reason: {reason}\n"
            
            html_body = template["html"].format(
                full_name=full_name,
                reason_html=reason_html
            )
            text_body = template["text"].format(
                full_name=full_name,
                reason_text=reason_text
            )
            
            return self._send_email(
                to_email=email,
                subject=template["subject"],
                html_body=html_body,
                text_body=text_body
            )
        except Exception as e:
            logger.error(f"Failed to send rejection email to {email}: {e}")
            return False
    
    def send_suspension_email(self, email: str, full_name: str, reason: Optional[str] = None) -> bool:
        """Send suspension notification email"""
        try:
            template = EMAIL_TEMPLATES["suspension"]
            
            reason_html = ""
            reason_text = ""
            if reason:
                reason_html = f"<p><strong>Reason:</strong> {reason}</p>"
                reason_text = f"Reason: {reason}\n"
            
            html_body = template["html"].format(
                full_name=full_name,
                reason_html=reason_html
            )
            text_body = template["text"].format(
                full_name=full_name,
                reason_text=reason_text
            )
            
            return self._send_email(
                to_email=email,
                subject=template["subject"],
                html_body=html_body,
                text_body=text_body
            )
        except Exception as e:
            logger.error(f"Failed to send suspension email to {email}: {e}")
            return False
    
    def send_welcome_email(self, email: str, full_name: str) -> bool:
        """Send welcome email for new registrations"""
        try:
            template = EMAIL_TEMPLATES["welcome"]
            html_body = template["html"].format(
                full_name=full_name
            )
            text_body = template["text"].format(
                full_name=full_name
            )
            
            return self._send_email(
                to_email=email,
                subject=template["subject"],
                html_body=html_body,
                text_body=text_body
            )
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {e}")
            return False
    
    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Internal method to send email via SMTP with automatic routing"""
        if not self.enabled:
            logger.info(f"Email notifications disabled. Would send to {to_email}: {subject}")
            logger.debug(f"Email body:\n{text_body}")
            return True
        
        # Automatically select SMTP provider based on recipient
        smtp_provider = self._get_smtp_provider(to_email)
        logger.info(f"Routing email to {to_email} via {smtp_provider.upper()} SMTP")
        
        if smtp_provider == "ionos":
            return self._send_smtp_ionos(to_email, subject, html_body, text_body)
        elif smtp_provider == "gmail":
            return self._send_smtp_gmail(to_email, subject, html_body, text_body)
        else:
            # Fallback to generic SMTP
            return self._send_smtp_generic(to_email, subject, html_body, text_body)
    
    def _send_smtp_ionos(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send email via IONOS SMTP"""
        try:
            # IONOS SMTP settings
            smtp_host = os.getenv("SMTP_HOST", "smtp.ionos.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))  # 587 for TLS, 465 for SSL
            smtp_username = os.getenv("SMTP_USERNAME", "cs@myhibachichef.com")
            smtp_password = os.getenv("SMTP_PASSWORD")
            
            if not smtp_password:
                logger.error("SMTP_PASSWORD not configured in environment")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{smtp_username}>"
            msg['To'] = to_email
            
            # Attach both plain text and HTML versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email via SMTP
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()  # Enable TLS
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent successfully via IONOS SMTP to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via IONOS SMTP to {to_email}: {e}")
            return False
    
    def _send_smtp_gmail(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send email via Gmail SMTP (for internal admin communications)"""
        try:
            # Gmail SMTP settings
            smtp_host = "smtp.gmail.com"
            smtp_port = 587
            smtp_username = os.getenv("GMAIL_USERNAME", "myhibachichef@gmail.com")
            smtp_password = os.getenv("GMAIL_APP_PASSWORD")  # Use App Password, not regular password
            
            if not smtp_password:
                logger.error("GMAIL_APP_PASSWORD not configured in environment")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{smtp_username}>"
            msg['To'] = to_email
            
            # Attach both plain text and HTML versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email via SMTP
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent successfully via Gmail SMTP to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via Gmail SMTP to {to_email}: {e}")
            return False
    
    def _send_smtp_generic(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send email via generic SMTP configuration"""
        try:
            smtp_host = os.getenv("SMTP_HOST", "localhost")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
            
            if not smtp_username or not smtp_password:
                logger.error("SMTP credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{smtp_username}>"
            msg['To'] = to_email
            
            # Attach both plain text and HTML versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email via SMTP
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if smtp_use_tls:
                    server.starttls()
                if smtp_username and smtp_password:
                    server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent successfully via SMTP to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via SMTP to {to_email}: {e}")
            return False


# Global email service instance
email_service = EmailService()
