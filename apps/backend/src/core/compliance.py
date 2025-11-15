"""US Compliance Configuration for Lead Generation & Newsletter System
TCPA, CAN-SPAM, and Privacy Compliance

This module centralizes all compliance-related configuration and utilities
to ensure adherence to US regulations for SMS and email marketing.
"""

import hmac
import hashlib
from urllib.parse import urlencode
from datetime import datetime, timezone
from typing import Dict, Any
from pydantic import BaseModel, Field


class ComplianceConfig(BaseModel):
    """Centralized compliance configuration matching actual business data"""
    
    # Business Information (ACTUAL DATA from Terms & Privacy pages)
    business_name: str = "my Hibachi LLC"
    business_display_name: str = "My Hibachi Chef"
    business_phone: str = "+19167408768"  # E.164 format for APIs
    business_phone_formatted: str = "(916) 740-8768"  # Human-readable format
    business_email_support: str = "cs@myhibachichef.com"
    business_email_privacy: str = "privacy@myhibachichef.com"
    business_website: str = "https://myhibachichef.com"
    
    # Physical Address (Required by CAN-SPAM Act)
    business_address_line1: str = "Mobile Catering Service"
    business_address_city: str = "Sacramento"
    business_address_state: str = "CA"
    business_address_zip: str = ""  # Update with actual if available
    
    # Service Areas (From actual Terms page)
    service_areas: list[str] = [
        "Sacramento Metro Area",
        "San Francisco Bay Area", 
        "Central Valley Region"
    ]
    
    # Business Hours (From actual Terms page)
    business_hours: str = "Monday - Sunday: 12:00 PM - 9:00 PM PST"
    
    # Policy URLs (Actual routes from your app)
    privacy_policy_url: str = "https://myhibachichef.com/privacy"
    terms_conditions_url: str = "https://myhibachichef.com/terms"
    contact_us_url: str = "https://myhibachichef.com/contact"
    
    # TCPA Compliance (SMS)
    tcpa_consent_text: str = (
        "By providing your phone number, you consent to receive SMS messages "
        "from my Hibachi LLC. Message frequency varies based on your bookings. "
        "Message and data rates may apply. Reply STOP to opt out, HELP for assistance."
    )
    
    tcpa_opt_out_keywords: list[str] = ["STOP", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"]
    tcpa_opt_in_keywords: list[str] = ["START", "UNSTOP", "YES", "SUBSCRIBE"]
    tcpa_help_keywords: list[str] = ["HELP", "INFO", "SUPPORT"]
    
    # CAN-SPAM Compliance (Email)
    can_spam_from_name: str = "My Hibachi Chef"
    can_spam_from_email: str = "noreply@myhibachichef.com"
    can_spam_reply_to: str = "cs@myhibachichef.com"
    can_spam_unsubscribe_text: str = "Unsubscribe from marketing emails"
    
    # Data Retention (From actual Privacy Policy)
    retention_active_customers: str = "While you're an active customer"
    retention_booking_records: int = 2555  # 7 years in days (tax/business records)
    retention_communication_records: int = 1095  # 3 years in days
    retention_marketing_data: str = "Until opt-out or deletion request"
    
    # Privacy Response Times (From actual Privacy Policy)
    privacy_request_response_days: int = 30
    data_breach_notification_hours: int = 72
    opt_out_processing_hours: int = 24  # Immediate processing goal
    
    # Marketing Frequency Limits
    sms_max_per_month: int = 8  # Conservative limit
    email_max_per_week: int = 2
    
    # Consent Tracking
    consent_ip_tracking: bool = True
    consent_timestamp_required: bool = True
    consent_source_tracking: bool = True
    
    # CCPA Compliance (California Privacy Rights)
    ccpa_enabled: bool = True
    ccpa_do_not_sell_enabled: bool = True
    ccpa_data_portability_enabled: bool = True
    
    # GDPR Compliance (EU/UK visitors)
    gdpr_enabled: bool = True
    gdpr_cookie_consent_required: bool = True


class ConsentRecord(BaseModel):
    """Model for tracking user consent with full audit trail"""
    
    user_id: str | None = None
    phone: str | None = None
    email: str | None = None
    
    # Consent details
    consent_type: str = Field(..., description="sms, email, marketing, terms")
    consent_given: bool = True
    consent_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    consent_withdrawn_at: datetime | None = None
    
    # Audit trail
    consent_source: str = Field(..., description="Source where consent was captured")
    consent_ip_address: str | None = None
    consent_user_agent: str | None = None
    consent_text: str = Field(..., description="Exact consent text shown to user")
    
    # Method tracking
    consent_method: str = Field(..., description="checkbox, auto_subscribe, double_optin")
    consent_form_url: str | None = None
    
    # Additional context
    lead_source: str | None = None
    campaign_id: str | None = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ComplianceValidator:
    """Validates compliance requirements for lead capture and newsletter"""
    
    def __init__(self, config: ComplianceConfig = ComplianceConfig()):
        self.config = config
    
    def validate_sms_consent(
        self,
        phone: str,
        consent_text: str,
        consent_method: str,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> tuple[bool, str]:
        """
        Validate SMS consent meets TCPA requirements
        
        Returns:
            tuple[bool, str]: (is_valid, reason)
        """
        
        # TCPA requires explicit consent
        if consent_method not in ["checkbox", "double_optin", "auto_subscribe"]:
            return False, "Invalid consent method for TCPA compliance"
        
        # Auto-subscribe requires clear opt-out instructions
        if consent_method == "auto_subscribe":
            if "STOP" not in consent_text.upper():
                return False, "Auto-subscribe must include STOP opt-out instructions"
        
        # Must include key TCPA disclosures
        required_elements = ["message", "data rates may apply", "stop"]
        consent_lower = consent_text.lower()
        
        missing = [elem for elem in required_elements if elem not in consent_lower]
        if missing:
            return False, f"Missing required TCPA disclosures: {', '.join(missing)}"
        
        # IP tracking recommended for audit trail
        if self.config.consent_ip_tracking and not ip_address:
            return False, "IP address tracking required for consent audit trail"
        
        return True, "SMS consent meets TCPA requirements"
    
    def validate_email_consent(
        self,
        email: str,
        has_unsubscribe_link: bool,
        has_physical_address: bool,
        from_name: str
    ) -> tuple[bool, str]:
        """
        Validate email consent meets CAN-SPAM requirements
        
        Returns:
            tuple[bool, str]: (is_valid, reason)
        """
        
        # CAN-SPAM requires unsubscribe mechanism
        if not has_unsubscribe_link:
            return False, "CAN-SPAM requires unsubscribe link in all marketing emails"
        
        # Physical address required
        if not has_physical_address:
            return False, "CAN-SPAM requires physical business address in emails"
        
        # From name must be clear, not deceptive
        if not from_name or from_name.lower() in ["no-reply", "noreply"]:
            return False, "CAN-SPAM requires identifiable sender name"
        
        return True, "Email consent meets CAN-SPAM requirements"
    
    def get_sms_welcome_message(self, name: str | None = None) -> str:
        """Get TCPA-compliant welcome message"""
        
        greeting = f"Hi {name}! " if name else "Welcome! "
        
        return f"""{greeting}Thanks for subscribing to {self.config.business_display_name} updates.

You will receive:
- Booking updates
- Event reminders  
- Exclusive offers

Reply STOP to opt out anytime.
Reply HELP for assistance.

{self.config.business_phone_formatted}"""
    
    def get_sms_opt_out_confirmation(self) -> str:
        """Get TCPA-compliant opt-out confirmation"""
        
        return f"""You have been unsubscribed from {self.config.business_display_name} SMS messages.

You will not receive further texts.

Reply START to resubscribe.

Questions? Call {self.config.business_phone_formatted}"""
    
    def get_sms_help_message(self) -> str:
        """Get TCPA-compliant help message"""
        
        return f"""{self.config.business_display_name}

Call: {self.config.business_phone_formatted}
Email: {self.config.business_email_support}
Web: {self.config.business_website}

Reply STOP to unsubscribe.

{self.config.business_hours}"""
    
    def get_email_footer_html(self, unsubscribe_url: str) -> str:
        """Get CAN-SPAM compliant email footer"""
        
        return f"""
<div style="border-top: 1px solid #ddd; padding: 20px; margin-top: 30px; font-size: 12px; color: #666; text-align: center;">
    <p><strong>{self.config.business_display_name}</strong></p>
    <p>{self.config.business_address_line1}<br>
    {self.config.business_address_city}, {self.config.business_address_state}</p>
    
    <p>
        <a href="{unsubscribe_url}" style="color: #e74c3c; text-decoration: none;">Unsubscribe</a> | 
        <a href="{self.config.privacy_policy_url}" style="color: #3498db; text-decoration: none;">Privacy Policy</a> | 
        <a href="{self.config.contact_us_url}" style="color: #3498db; text-decoration: none;">Contact Us</a>
    </p>
    
    <p style="margin-top: 10px;">
        You are receiving this because you subscribed to {self.config.business_display_name} updates.
    </p>
    
    <p style="margin-top: 5px; font-size: 11px;">
        Copyright {datetime.now().year} {self.config.business_name}. All rights reserved.
    </p>
</div>
"""
    
    def create_consent_record(
        self,
        consent_type: str,
        consent_given: bool,
        consent_source: str,
        consent_text: str,
        consent_method: str,
        phone: str | None = None,
        email: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        lead_source: str | None = None,
        **kwargs
    ) -> ConsentRecord:
        """Create a consent record with full audit trail"""
        
        return ConsentRecord(
            phone=phone,
            email=email,
            consent_type=consent_type,
            consent_given=consent_given,
            consent_timestamp=datetime.now(timezone.utc),
            consent_source=consent_source,
            consent_ip_address=ip_address,
            consent_user_agent=user_agent,
            consent_text=consent_text,
            consent_method=consent_method,
            lead_source=lead_source,
            metadata=kwargs
        )
    
    def check_marketing_frequency_limit(
        self,
        contact: str,
        channel: str,
        messages_sent_period: int
    ) -> tuple[bool, str]:
        """
        Check if marketing frequency limits are exceeded
        
        Args:
            contact: Phone or email
            channel: 'sms' or 'email'
            messages_sent_period: Number of messages sent in current period
        
        Returns:
            tuple[bool, str]: (within_limit, reason)
        """
        
        if channel == "sms":
            max_allowed = self.config.sms_max_per_month
            period = "month"
        else:
            max_allowed = self.config.email_max_per_week
            period = "week"
        
        if messages_sent_period >= max_allowed:
            return False, f"Exceeded {max_allowed} {channel} messages per {period}"
        
        return True, f"Within frequency limit ({messages_sent_period}/{max_allowed} per {period})"
    
    def generate_unsubscribe_url(self, email: str, secret_key: str) -> str:
        """
        Generate secure unsubscribe URL with HMAC token for CAN-SPAM compliance.
        
        Args:
            email: Subscriber email address
            secret_key: Application secret key for HMAC generation
        
        Returns:
            Full unsubscribe URL with secure token
        
        Example:
            https://myhibachichef.com/api/v1/newsletter/unsubscribe?email=user@example.com&token=abc123def456
        """
        # Generate HMAC token to prevent unsubscribe link abuse
        secret = secret_key.encode()
        message = f"{email}|unsubscribe".encode()
        token = hmac.new(secret, message, hashlib.sha256).hexdigest()[:16]
        
        # Build URL with query parameters
        params = urlencode({"email": email, "token": token})
        return f"{self.config.business_website}/api/v1/newsletter/unsubscribe?{params}"
    
    def verify_unsubscribe_token(self, email: str, token: str, secret_key: str) -> bool:
        """
        Verify unsubscribe token is valid and has not been tampered with.
        
        Args:
            email: Subscriber email address from URL
            token: HMAC token from URL
            secret_key: Application secret key
        
        Returns:
            True if token is valid, False otherwise
        """
        secret = secret_key.encode()
        message = f"{email}|unsubscribe".encode()
        expected_token = hmac.new(secret, message, hashlib.sha256).hexdigest()[:16]
        
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(token, expected_token)


# Global compliance instance
compliance_config = ComplianceConfig()
compliance_validator = ComplianceValidator(compliance_config)


def get_compliance_config() -> ComplianceConfig:
    """Get the global compliance configuration"""
    return compliance_config


def get_compliance_validator() -> ComplianceValidator:
    """Get the global compliance validator"""
    return compliance_validator

