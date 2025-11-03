"""
Alert Manager for Cost and Growth Monitoring

Sends alerts via Slack and Email when thresholds are crossed.
"""

import logging
import os
import ssl
import smtplib
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx

logger = logging.getLogger(__name__)


class AlertManager:
    """Manage alerts via Slack and Email"""
    
    def __init__(self):
        # Slack configuration
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        
        # Email configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.alert_email_to = os.getenv("ALERT_EMAIL_TO", "founder@myhibachichef.com")
        self.alert_email_from = os.getenv("ALERT_EMAIL_FROM", self.smtp_user)
        
        self.logger = logger
    
    async def send_slack_alert(self, message: str) -> bool:
        """
        Send alert to Slack via webhook.
        
        Args:
            message: Alert message (markdown supported)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.slack_webhook_url:
            self.logger.warning("SLACK_WEBHOOK_URL not configured, skipping Slack alert")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.slack_webhook_url,
                    json={
                        "text": message,
                        "username": "MyHibachi AI Monitor",
                        "icon_emoji": ":robot_face:"
                    }
                )
                response.raise_for_status()
            
            self.logger.info("Slack alert sent successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    async def send_email_alert(self, subject: str, body: str) -> bool:
        """
        Send alert via email.
        
        Args:
            subject: Email subject
            body: Email body (plain text)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.smtp_user or not self.smtp_password:
            self.logger.warning("SMTP credentials not configured, skipping email alert")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.alert_email_from
            msg["To"] = self.alert_email_to
            
            # Add plain text body
            text_part = MIMEText(body, "plain")
            msg.attach(text_part)
            
            # Add HTML body (formatted)
            html_body = self._convert_to_html(body)
            html_part = MIMEText(html_body, "html")
            msg.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(
                    self.alert_email_from,
                    [self.alert_email_to],
                    msg.as_string()
                )
            
            self.logger.info(f"Email alert sent successfully to {self.alert_email_to}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False
    
    def _convert_to_html(self, text: str) -> str:
        """Convert plain text to basic HTML."""
        html = text.replace("\n", "<br>")
        html = html.replace("**", "<strong>").replace("**", "</strong>")
        html = html.replace("🔥", "🔥").replace("⚠️", "⚠️").replace("💡", "💡")
        
        return f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .alert {{ padding: 20px; border-left: 4px solid #ff6b6b; background: #fff5f5; }}
                </style>
            </head>
            <body>
                <div class="alert">
                    {html}
                </div>
            </body>
        </html>
        """


# Global alert manager instance
alert_manager = AlertManager()


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    return alert_manager
