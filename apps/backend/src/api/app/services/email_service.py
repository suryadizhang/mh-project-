"""
Email service for sending booking confirmations, notifications, and administrative emails.
Optimized for IONOS Business Email SMTP with proper template support.
"""
import logging
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional
from string import Template

from api.app.config import settings

logger = logging.getLogger(__name__)

# Email templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"


class EmailService:
    """
    Enhanced email service for IONOS Business Email.
    
    Features:
    - HTML email templates with fallback to plain text
    - Proper error handling with retry logic
    - Connection timeout and security
    - Detailed logging for debugging
    - Batch email support for newsletters
    """
    
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.smtp_use_tls = settings.smtp_use_tls
        self.timeout = getattr(settings, 'email_timeout', 30)
        
        # IONOS requires from_email to match SMTP_USER
        self.from_email = settings.from_email or settings.smtp_user
        self.from_name = getattr(settings, 'emails_from_name', 'My Hibachi Chef')
        
        # Check if email is properly configured
        self.enabled = (
            not settings.disable_email 
            and bool(self.smtp_host) 
            and bool(self.smtp_user) 
            and bool(self.smtp_password)
        )
        
        if self.enabled:
            logger.info(f"Email service initialized: {self.smtp_host}:{self.smtp_port} (User: {self.smtp_user})")
        else:
            logger.warning("Email service disabled: Missing configuration")
    
    def _load_template(self, template_name: str, variables: Dict[str, str]) -> tuple[str, str]:
        """
        Load HTML template and generate plain text fallback.
        
        Args:
            template_name: Name of template file (e.g., 'booking_confirmation')
            variables: Dictionary of template variables
            
        Returns:
            Tuple of (plain_text, html_body)
        """
        template_path = TEMPLATES_DIR / f"{template_name}.html"
        
        try:
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    html_template = Template(f.read())
                    html_body = html_template.safe_substitute(**variables)
                    
                    # Generate plain text from variables
                    plain_text = self._generate_plain_text(template_name, variables)
                    
                    return plain_text, html_body
            else:
                logger.warning(f"Template not found: {template_path}, using plain text only")
                plain_text = self._generate_plain_text(template_name, variables)
                return plain_text, None
                
        except Exception as e:
            logger.error(f"Error loading template {template_name}: {e}")
            # Fallback to plain text
            plain_text = self._generate_plain_text(template_name, variables)
            return plain_text, None
    
    def _generate_plain_text(self, template_name: str, variables: Dict[str, str]) -> str:
        """Generate plain text email from variables."""
        # Simple plain text generation based on template type
        if template_name == "booking_confirmation":
            return f"""Dear {variables.get('customer_name', 'Customer')},

Thank you for booking My Hibachi Chef! We're excited to serve you.

Booking Details:
- Date: {variables.get('booking_date', 'N/A')}
- Time: {variables.get('booking_time', 'N/A')}
- Party Size: {variables.get('party_size', 'N/A')} guests
- Location: {variables.get('address', '')}, {variables.get('city', '')}, CA {variables.get('zipcode', '')}
- Phone: {variables.get('phone', 'N/A')}
- Contact via: {variables.get('contact_preference', 'N/A')}

What's Next?
Our team will contact you via {variables.get('contact_preference', 'your preferred method')} within 24 hours to confirm details and arrange payment.

Questions? Contact us:
Phone: (916) 740-8768
Email: cs@myhibachichef.com

Best regards,
My Hibachi Chef Team
"""
        else:
            # Generic fallback
            return "\n".join([f"{k}: {v}" for k, v in variables.items()])
    
    def _send_email(
        self, 
        to_emails: List[str], 
        subject: str, 
        body: str, 
        html_body: Optional[str] = None,
        max_retries: int = 2
    ):
        """
        Send email using SMTP with retry logic.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            max_retries: Number of retry attempts on failure
        """
        if not self.enabled:
            logger.info(f"Email disabled, skipping: {subject} to {to_emails}")
            return
        
        if not to_emails:
            logger.warning("No recipients specified, skipping email")
            return
        
        # Validate email addresses (basic check)
        valid_emails = [email for email in to_emails if '@' in email and '.' in email]
        if not valid_emails:
            logger.error(f"No valid email addresses in {to_emails}")
            return
        
        attempt = 0
        last_error = None
        
        while attempt <= max_retries:
            try:
                # Create message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = f"{self.from_name} <{self.from_email}>"
                msg['To'] = ', '.join(valid_emails)
                msg['Reply-To'] = self.from_email
                
                # Add plain text part (always)
                text_part = MIMEText(body, 'plain', 'utf-8')
                msg.attach(text_part)
                
                # Add HTML part if provided (preferred by email clients)
                if html_body:
                    html_part = MIMEText(html_body, 'html', 'utf-8')
                    msg.attach(html_part)
                
                # Connect and send
                logger.debug(f"Connecting to SMTP: {self.smtp_host}:{self.smtp_port}")
                
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.timeout) as server:
                    # Set debug level for troubleshooting (only in development)
                    if settings.debug:
                        server.set_debuglevel(1)
                    
                    # Start TLS if enabled
                    if self.smtp_use_tls:
                        server.starttls()
                    
                    # Login
                    server.login(self.smtp_user, self.smtp_password)
                    
                    # Send message
                    server.send_message(msg)
                
                logger.info(f"✅ Email sent successfully: '{subject}' to {valid_emails}")
                return  # Success!
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"❌ SMTP Authentication failed: {e} (Check IONOS credentials)")
                raise  # Don't retry auth errors
                
            except smtplib.SMTPException as e:
                last_error = e
                attempt += 1
                logger.warning(f"⚠️  SMTP error (attempt {attempt}/{max_retries + 1}): {e}")
                if attempt <= max_retries:
                    logger.info(f"Retrying in 2 seconds...")
                    import time
                    time.sleep(2)
                    
            except socket.timeout as e:
                last_error = e
                attempt += 1
                logger.warning(f"⚠️  Connection timeout (attempt {attempt}/{max_retries + 1}): {e}")
                if attempt <= max_retries:
                    import time
                    time.sleep(2)
                    
            except Exception as e:
                last_error = e
                logger.error(f"❌ Unexpected error sending email: {e}", exc_info=True)
                raise
        
        # All retries failed
        logger.error(f"❌ Failed to send email after {max_retries + 1} attempts: {last_error}")
        raise Exception(f"Email delivery failed: {last_error}")


email_service = EmailService()


# ==========================================
# Email Sending Functions (Public API)
# ==========================================

async def send_booking_confirmation(booking_data: dict, background_tasks=None):
    """
    Send booking confirmation email with professional template.
    
    Args:
        booking_data: Dict containing booking information
        background_tasks: FastAPI BackgroundTasks (optional)
    """
    try:
        variables = {
            'customer_name': booking_data.get('name', 'Customer'),
            'booking_date': booking_data.get('date', 'N/A'),
            'booking_time': booking_data.get('time_slot', 'N/A'),
            'party_size': str(booking_data.get('party_size', 'N/A')),
            'address': booking_data.get('address', ''),
            'city': booking_data.get('city', ''),
            'zipcode': booking_data.get('zipcode', ''),
            'phone': booking_data.get('phone', 'N/A'),
            'contact_preference': booking_data.get('contact_preference', 'text'),
        }
        
        plain_text, html_body = email_service._load_template('booking_confirmation', variables)
        
        subject = f"🍱 Booking Confirmed - My Hibachi Chef ({variables['booking_date']})"
        
        email_service._send_email(
            to_emails=[booking_data['email']],
            subject=subject,
            body=plain_text,
            html_body=html_body
        )
        
        logger.info(f"Booking confirmation sent to {booking_data['email']}")
        
    except Exception as e:
        logger.error(f"Failed to send booking confirmation: {e}", exc_info=True)
        # Don't raise - email failure shouldn't block booking


async def send_payment_receipt(payment_data: dict, background_tasks=None):
    """
    Send payment receipt email.
    
    Args:
        payment_data: Dict containing payment and booking information
    """
    try:
        variables = {
            'customer_name': payment_data.get('customer_name', 'Customer'),
            'customer_email': payment_data.get('customer_email', ''),
            'receipt_number': payment_data.get('receipt_number', 'N/A'),
            'payment_date': payment_data.get('payment_date', 'N/A'),
            'payment_method': payment_data.get('payment_method', 'Credit Card'),
            'payment_type': payment_data.get('payment_type', 'Deposit'),
            'amount': f"{payment_data.get('amount', 0):.2f}",
            'booking_date': payment_data.get('booking_date', 'N/A'),
            'booking_time': payment_data.get('booking_time', 'N/A'),
            'address': payment_data.get('address', ''),
            'city': payment_data.get('city', ''),
            'zipcode': payment_data.get('zipcode', ''),
        }
        
        plain_text, html_body = email_service._load_template('payment_receipt', variables)
        
        subject = f"💳 Payment Receipt - My Hibachi Chef (${variables['amount']})"
        
        email_service._send_email(
            to_emails=[payment_data['customer_email']],
            subject=subject,
            body=plain_text,
            html_body=html_body
        )
        
        logger.info(f"Payment receipt sent to {payment_data['customer_email']}")
        
    except Exception as e:
        logger.error(f"Failed to send payment receipt: {e}", exc_info=True)


async def send_admin_notification(
    notification_type: str, 
    notification_body: str,
    recipient_emails: List[str] = None,
    background_tasks=None
):
    """
    Send administrative notification email.
    
    Args:
        notification_type: Type of notification (e.g., "New Booking", "Payment Received")
        notification_body: HTML-formatted notification content
        recipient_emails: List of admin emails (defaults to settings.admin_email)
    """
    try:
        if not recipient_emails:
            recipient_emails = [settings.admin_email] if hasattr(settings, 'admin_email') else []
        
        if not recipient_emails:
            logger.warning("No admin email configured, skipping notification")
            return
        
        variables = {
            'notification_type': notification_type,
            'notification_body': notification_body,
            'admin_dashboard_url': f"{settings.app_url}/admin/dashboard",
        }
        
        plain_text, html_body = email_service._load_template('admin_notification', variables)
        
        subject = f"🔔 {notification_type} - My Hibachi Chef Admin"
        
        email_service._send_email(
            to_emails=recipient_emails,
            subject=subject,
            body=plain_text,
            html_body=html_body
        )
        
        logger.info(f"Admin notification sent: {notification_type}")
        
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}", exc_info=True)


# ==========================================
# Legacy Functions (Backwards Compatibility)
# ==========================================

async def send_booking_email(booking_data: dict, background_tasks=None):
    """Legacy function - redirects to send_booking_confirmation."""
    await send_booking_confirmation(booking_data, background_tasks)


async def send_customer_confirmation(booking_data: dict, background_tasks=None):
    """Legacy function - redirects to send_booking_confirmation."""
    await send_booking_confirmation(booking_data, background_tasks)


async def send_waitlist_confirmation(waitlist_data: dict, position: int, background_tasks=None):
    """Send waitlist confirmation email (simple text email)."""
    try:
        subject = "Added to My Hibachi Waitlist"
        
        body = f"""Dear {waitlist_data['name']},

You have been added to our waitlist for {waitlist_data['preferred_date']} at {waitlist_data['preferred_time']}.

Your position: #{position}

We will notify you as soon as a slot becomes available.

Best regards,
My Hibachi Chef Team
"""
        
        email_service._send_email([waitlist_data['email']], subject, body)
        logger.info(f"Waitlist confirmation sent to {waitlist_data['email']}")
        
    except Exception as e:
        logger.error(f"Failed to send waitlist confirmation: {e}", exc_info=True)


async def send_waitlist_slot_opened(waitlist_data: dict, background_tasks=None):
    """Send notification when a waitlist slot opens."""
    try:
        subject = "🎉 Slot Available - My Hibachi Waitlist"
        
        body = f"""Dear {waitlist_data['name']},

Great news! A slot has opened for {waitlist_data['preferred_date']} at {waitlist_data['preferred_time']}.

Please contact us immediately to confirm your booking:
📞 Phone: (916) 740-8768
📧 Email: cs@myhibachichef.com

Best regards,
My Hibachi Chef Team
"""
        
        email_service._send_email([waitlist_data['email']], subject, body)
        logger.info(f"Waitlist slot notification sent to {waitlist_data['email']}")
        
    except Exception as e:
        logger.error(f"Failed to send waitlist slot notification: {e}", exc_info=True)


async def send_waitlist_position_email(waitlist_data: dict, position: int, background_tasks=None):
    """Send waitlist position update email."""
    try:
        subject = "Waitlist Position Update - My Hibachi Chef"
        
        body = f"""Dear {waitlist_data['name']},

Your waitlist position has been updated.

New position: #{position}
Preferred date: {waitlist_data['preferred_date']}
Preferred time: {waitlist_data['preferred_time']}

We will notify you when a slot becomes available.

Best regards,
My Hibachi Chef Team
"""
        
        email_service._send_email([waitlist_data['email']], subject, body)
        logger.info(f"Waitlist position update sent to {waitlist_data['email']}")
        
    except Exception as e:
        logger.error(f"Failed to send waitlist position update: {e}", exc_info=True)


async def send_deposit_confirmation_email(booking_data: dict, background_tasks=None):
    """Send deposit confirmation email (redirects to payment receipt)."""
    payment_data = {
        'customer_name': booking_data.get('name'),
        'customer_email': booking_data.get('email'),
        'receipt_number': booking_data.get('booking_id', 'N/A'),
        'payment_date': booking_data.get('date'),
        'payment_method': 'Credit Card',
        'payment_type': 'Deposit',
        'amount': booking_data.get('deposit_amount', 0),
        'booking_date': booking_data.get('date'),
        'booking_time': booking_data.get('time_slot'),
        'address': booking_data.get('address'),
        'city': booking_data.get('city'),
        'zipcode': booking_data.get('zipcode'),
    }
    await send_payment_receipt(payment_data, background_tasks)


async def send_booking_cancellation_email(booking_data: dict, reason: str, background_tasks=None):
    """Send booking cancellation email."""
    try:
        subject = f"Booking Cancelled - My Hibachi Chef"
        
        body = f"""Dear {booking_data['name']},

Your booking has been cancelled.

Original Booking Details:
- Date: {booking_data['date']}
- Time: {booking_data['time_slot']}

Reason: {reason}

If you have any questions or would like to rebook, please contact us:
📞 Phone: (916) 740-8768
📧 Email: cs@myhibachichef.com

Best regards,
My Hibachi Chef Team
"""
        
        email_service._send_email([booking_data['email']], subject, body)
        logger.info(f"Cancellation email sent to {booking_data['email']}")
        
    except Exception as e:
        logger.error(f"Failed to send cancellation email: {e}", exc_info=True)


async def send_newsletter(recipients: List[dict], subject: str, message: str, background_tasks=None):
    """
    Send newsletter to multiple recipients (batch processing).
    
    Note: For high-volume newsletters, consider using SMS via RingCentral instead.
    Email newsletters are low priority for this business.
    
    Args:
        recipients: List of dicts with 'email' key
        subject: Newsletter subject
        message: Newsletter body (plain text or HTML)
    """
    if not recipients:
        logger.warning("No recipients for newsletter")
        return
        
    # Extract valid emails
    emails = [r['email'] for r in recipients if r.get('email') and '@' in r.get('email', '')]
    
    if not emails:
        logger.warning("No valid email addresses found for newsletter")
        return
    
    try:
        # Send in batches to avoid overwhelming SMTP server
        batch_size = 20  # Conservative batch size for IONOS
        total_sent = 0
        
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i + batch_size]
            
            try:
                email_service._send_email(batch, subject, message)
                total_sent += len(batch)
                logger.info(f"Newsletter batch sent: {len(batch)} emails ({total_sent}/{len(emails)} total)")
                
                # Small delay between batches to avoid rate limiting
                if i + batch_size < len(emails):
                    import time
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Failed to send newsletter batch {i//batch_size + 1}: {e}")
                # Continue with next batch
        
        logger.info(f"Newsletter complete: {total_sent}/{len(emails)} emails sent")
        
    except Exception as e:
        logger.error(f"Newsletter sending failed: {e}", exc_info=True)
