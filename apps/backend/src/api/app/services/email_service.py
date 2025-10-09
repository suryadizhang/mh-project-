"""
Email service for sending booking confirmations, notifications, and newsletters.
Compatible with the source backend email functionality.
"""
import logging
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import List, Optional

from api.app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for handling all email communications."""
    
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user or settings.email_user
        self.smtp_password = settings.smtp_password or settings.email_pass
        self.from_email = settings.from_email
        self.enabled = not settings.disable_email and bool(self.smtp_user)
        
    def _send_email(self, to_emails: List[str], subject: str, body: str, html_body: Optional[str] = None):
        """Send email using SMTP."""
        if not self.enabled:
            logger.info(f"Email disabled, skipping: {subject} to {to_emails}")
            return
            
        try:
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            
            # Add plain text part
            text_part = MimeText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MimeText(html_body, 'html')
                msg.attach(html_part)
                
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                
            logger.info(f"Email sent successfully: {subject} to {to_emails}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise


email_service = EmailService()


# Email sending functions (compatible with source backend)
async def send_booking_email(booking_data: dict, background_tasks=None):
    """Send booking confirmation email to customer."""
    subject = f"Booking Confirmation - My Hibachi Catering ({booking_data['date']})"
    
    body = f"""
Dear {booking_data['name']},

Thank you for booking My Hibachi catering service!

Booking Details:
- Date: {booking_data['date']}
- Time: {booking_data['time_slot']}
- Address: {booking_data['address']}, {booking_data['city']}, {booking_data['zipcode']}
- Contact: {booking_data['phone']}

We will contact you via {booking_data['contact_preference']} to confirm details and payment.

Best regards,
My Hibachi Catering Team
"""
    
    email_service._send_email([booking_data['email']], subject, body)


async def send_customer_confirmation(booking_data: dict, background_tasks=None):
    """Send customer confirmation email."""
    await send_booking_email(booking_data, background_tasks)


async def send_waitlist_confirmation(waitlist_data: dict, position: int, background_tasks=None):
    """Send waitlist confirmation email."""
    subject = "Added to My Hibachi Waitlist"
    
    body = f"""
Dear {waitlist_data['name']},

You have been added to our waitlist for {waitlist_data['preferred_date']} at {waitlist_data['preferred_time']}.

Your position: #{position}

We will notify you as soon as a slot becomes available.

Best regards,
My Hibachi Catering Team
"""
    
    email_service._send_email([waitlist_data['email']], subject, body)


async def send_waitlist_slot_opened(waitlist_data: dict, background_tasks=None):
    """Send notification when a waitlist slot opens."""
    subject = "Slot Available - My Hibachi Waitlist"
    
    body = f"""
Dear {waitlist_data['name']},

Great news! A slot has opened for {waitlist_data['preferred_date']} at {waitlist_data['preferred_time']}.

Please contact us immediately to confirm your booking.

Phone: {settings.admin_phone}
Email: {settings.admin_email}

Best regards,
My Hibachi Catering Team
"""
    
    email_service._send_email([waitlist_data['email']], subject, body)


async def send_waitlist_position_email(waitlist_data: dict, position: int, background_tasks=None):
    """Send waitlist position update email."""
    subject = "Waitlist Position Update - My Hibachi"
    
    body = f"""
Dear {waitlist_data['name']},

Your waitlist position has been updated.

New position: #{position}
Preferred date: {waitlist_data['preferred_date']}
Preferred time: {waitlist_data['preferred_time']}

We will notify you when a slot becomes available.

Best regards,
My Hibachi Catering Team
"""
    
    email_service._send_email([waitlist_data['email']], subject, body)


async def send_deposit_confirmation_email(booking_data: dict, background_tasks=None):
    """Send deposit confirmation email."""
    subject = f"Deposit Confirmed - My Hibachi ({booking_data['date']})"
    
    body = f"""
Dear {booking_data['name']},

Your deposit has been confirmed!

Booking Details:
- Date: {booking_data['date']}
- Time: {booking_data['time_slot']}
- Address: {booking_data['address']}

Your booking is now fully confirmed. We look forward to serving you!

Best regards,
My Hibachi Catering Team
"""
    
    email_service._send_email([booking_data['email']], subject, body)


async def send_booking_cancellation_email(booking_data: dict, reason: str, background_tasks=None):
    """Send booking cancellation email."""
    subject = f"Booking Cancelled - My Hibachi ({booking_data['date']})"
    
    body = f"""
Dear {booking_data['name']},

Your booking has been cancelled.

Original Booking Details:
- Date: {booking_data['date']}
- Time: {booking_data['time_slot']}

Reason: {reason}

If you have any questions or would like to rebook, please contact us.

Best regards,
My Hibachi Catering Team
"""
    
    email_service._send_email([booking_data['email']], subject, body)


async def send_newsletter(recipients: List[dict], subject: str, message: str, background_tasks=None):
    """Send newsletter to multiple recipients."""
    if not recipients:
        return
        
    emails = [recipient['email'] for recipient in recipients if recipient.get('email')]
    
    if not emails:
        logger.warning("No valid email addresses found for newsletter")
        return
    
    # Send in batches to avoid overwhelming the SMTP server
    batch_size = 50
    for i in range(0, len(emails), batch_size):
        batch = emails[i:i + batch_size]
        email_service._send_email(batch, subject, message)
        logger.info(f"Newsletter batch sent: {len(batch)} emails")