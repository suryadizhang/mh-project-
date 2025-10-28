"""
RingCentral utility functions for setup, management, and testing.
Enhanced to work with existing RingCentralSMSService architecture.
"""

import os
import jwt
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

from core.config import get_settings

settings = get_settings()
from api.app.services.ringcentral_sms import RingCentralSMSService, send_sms_notification

logger = logging.getLogger(__name__)


def generate_jwt_token(
    app_key: str,
    app_secret: str,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
    expires_in: int = 3600
) -> str:
    """
    Generate JWT token for RingCentral authentication.
    
    Args:
        app_key: RingCentral application key
        app_secret: RingCentral application secret
        issuer: JWT issuer (defaults to app_key)
        audience: JWT audience (defaults to RingCentral API)
        expires_in: Token expiration in seconds (default 1 hour)
    
    Returns:
        JWT token string
    """
    now = datetime.utcnow()
    payload = {
        'iss': issuer or app_key,
        'aud': audience or 'https://platform.ringcentral.com',
        'exp': now + timedelta(seconds=expires_in),
        'iat': now,
        'jti': f"{app_key}_{int(now.timestamp())}"
    }
    
    return jwt.encode(payload, app_secret, algorithm='HS256')


async def register_webhooks(
    base_url: str,
    events: Optional[List[str]] = None,
    sms_service: Optional[RingCentralSMSService] = None
) -> Dict[str, Any]:
    """
    Register RingCentral webhooks for the application.
    
    Args:
        base_url: Base URL of the application (e.g., https://yourdomain.com)
        events: List of events to subscribe to
        sms_service: RingCentral SMS service instance (optional)
    
    Returns:
        Subscription details
    """
    if not sms_service:
        sms_service = RingCentralSMSService()
    
    if not events:
        events = ["message-store"]  # Focus on SMS events
    
    # Webhook URLs
    webhook_urls = {
        "sms": urljoin(base_url, "/api/webhooks/ringcentral/sms"),
        "voice": urljoin(base_url, "/api/webhooks/ringcentral/voice")
    }
    
    subscriptions = {}
    
    try:
        async with sms_service:
            # Register SMS webhook using existing service method
            sms_webhook_result = await sms_service.setup_webhook(
                webhook_urls["sms"],
                ["message-store"]
            )
            subscriptions["sms"] = {
                "success": sms_webhook_result, 
                "url": webhook_urls["sms"],
                "events": ["message-store"]
            }
        
        logger.info(f"Successfully registered SMS webhook")
        return {
            "status": "success",
            "subscriptions": subscriptions,
            "webhook_urls": webhook_urls,
            "registered_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to register webhooks: {e}")
        return {
            "status": "error",
            "error": str(e),
            "attempted_urls": webhook_urls
        }


async def list_webhooks(sms_service: Optional[RingCentralSMSService] = None) -> List[Dict[str, Any]]:
    """
    List webhook subscriptions using the health check and service info.
    
    Args:
        sms_service: RingCentral SMS service instance (optional)
    
    Returns:
        List of webhook information
    """
    if not sms_service:
        sms_service = RingCentralSMSService()
    
    try:
        async with sms_service:
            # Use health check to get service status
            health_info = await sms_service.health_check()
            
            webhook_info = [{
                "service": "sms",
                "status": health_info.get("status", "unknown"),
                "authentication": health_info.get("authentication", "unknown"),
                "auth_method": health_info.get("auth_method", "unknown"),
                "account_name": health_info.get("account_name", "Unknown"),
                "timestamp": health_info.get("timestamp")
            }]
            
            return webhook_info
        
    except Exception as e:
        logger.error(f"Failed to list webhooks: {e}")
        return []


async def cleanup_webhooks(sms_service: Optional[RingCentralSMSService] = None) -> Dict[str, Any]:
    """
    Webhook cleanup is handled by RingCentral automatically.
    This function provides a status report.
    
    Args:
        sms_service: RingCentral SMS service instance (optional)
    
    Returns:
        Cleanup results
    """
    cleanup_results = {
        "message": "Webhook cleanup handled by RingCentral platform",
        "recommendation": "Use RingCentral console to manage webhook subscriptions",
        "service_status": "unknown"
    }
    
    if not sms_service:
        sms_service = RingCentralSMSService()
    
    try:
        async with sms_service:
            health_info = await sms_service.health_check()
            cleanup_results["service_status"] = health_info.get("status", "unknown")
            cleanup_results["timestamp"] = datetime.now().isoformat()
        
    except Exception as e:
        cleanup_results["error"] = str(e)
    
    return cleanup_results


def validate_configuration() -> Dict[str, Any]:
    """
    Validate RingCentral configuration settings.
    
    Returns:
        Validation results with missing or invalid settings
    """
    validation_results = {
        "valid": True,
        "missing": [],
        "invalid": [],
        "warnings": []
    }
    
    # Required settings
    required_settings = [
        ("RINGCENTRAL_CLIENT_ID", "ringcentral_client_id"),
        ("RINGCENTRAL_CLIENT_SECRET", "ringcentral_client_secret")
    ]
    
    for env_var, attr_name in required_settings:
        value = getattr(settings, attr_name, None) or os.getenv(env_var)
        if not value:
            validation_results["missing"].append(env_var)
            validation_results["valid"] = False
    
    # Check authentication method
    jwt_token = getattr(settings, 'ringcentral_jwt_token', None) or os.getenv('RINGCENTRAL_JWT_TOKEN')
    username = getattr(settings, 'ringcentral_username', None) or os.getenv('RINGCENTRAL_USERNAME')
    password = getattr(settings, 'ringcentral_password', None) or os.getenv('RINGCENTRAL_PASSWORD')
    
    if not jwt_token and not (username and password):
        validation_results["missing"].append("RINGCENTRAL_JWT_TOKEN or RINGCENTRAL_USERNAME/PASSWORD")
        validation_results["valid"] = False
    
    # Optional but recommended settings
    optional_settings = [
        ("RINGCENTRAL_WEBHOOK_SECRET", "ringcentral_webhook_secret"),
        ("RINGCENTRAL_PHONE_NUMBER", "ringcentral_phone_number"),
        ("RINGCENTRAL_SANDBOX", "ringcentral_sandbox")
    ]
    
    for env_var, attr_name in optional_settings:
        value = getattr(settings, attr_name, None) or os.getenv(env_var)
        if not value:
            validation_results["warnings"].append(f"{env_var} not set (optional)")
    
    # Validate phone number format
    phone_number = getattr(settings, 'ringcentral_phone_number', None) or os.getenv('RINGCENTRAL_PHONE_NUMBER')
    if phone_number and not phone_number.startswith('+'):
        validation_results["invalid"].append("RINGCENTRAL_PHONE_NUMBER should start with + (international format)")
        validation_results["valid"] = False
    
    return validation_results


async def test_connection(sms_service: Optional[RingCentralSMSService] = None) -> Dict[str, Any]:
    """
    Test RingCentral API connection and authentication.
    
    Args:
        sms_service: RingCentral SMS service instance (optional)
    
    Returns:
        Connection test results
    """
    if not sms_service:
        sms_service = RingCentralSMSService()
    
    try:
        async with sms_service:
            # Use the enhanced health check
            health_status = await sms_service.health_check()
            
            return {
                "connected": health_status["status"] == "healthy",
                "status": health_status["status"],
                "authentication": health_status["authentication"],
                "auth_method": health_status.get("auth_method", "unknown"),
                "account_info": {
                    "name": health_status.get("account_name", "Unknown"),
                    "status": health_status.get("account_status", "Unknown")
                },
                "capabilities": {
                    "sms_ready": bool(getattr(settings, 'ringcentral_phone_number', None) or 
                                     getattr(settings, 'ringcentral_from_number', None)),
                    "phone_number": getattr(settings, 'ringcentral_phone_number', None) or 
                                   getattr(settings, 'ringcentral_from_number', None)
                },
                "timestamp": health_status["timestamp"]
            }
        
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def create_environment_template() -> str:
    """
    Create environment variable template for RingCentral configuration.
    
    Returns:
        Environment template string
    """
    template = """
# RingCentral Configuration
# Required Settings
RINGCENTRAL_CLIENT_ID=your_client_id_here
RINGCENTRAL_CLIENT_SECRET=your_client_secret_here

# Authentication Method 1: JWT Token (Recommended)
RINGCENTRAL_JWT_TOKEN=your_jwt_token_here

# Authentication Method 2: Username/Password (Alternative)
RINGCENTRAL_USERNAME=your_username_here
RINGCENTRAL_PASSWORD=your_password_here

# Phone Number for SMS
RINGCENTRAL_PHONE_NUMBER=+1234567890  # International format
# OR (legacy support)
RINGCENTRAL_FROM_NUMBER=+1234567890

# Optional Settings
RINGCENTRAL_WEBHOOK_SECRET=your_webhook_secret_here
RINGCENTRAL_SANDBOX=true  # Set to false for production
RINGCENTRAL_SERVER_URL=https://platform.ringcentral.com  # Default

# Webhook URLs (automatically constructed)
# SMS Webhook: https://yourdomain.com/api/webhooks/ringcentral/sms
# Voice Webhook: https://yourdomain.com/api/webhooks/ringcentral/voice
"""
    return template.strip()


async def send_test_sms(
    to_number: str,
    message: Optional[str] = None,
    sms_service: Optional[RingCentralSMSService] = None
) -> Dict[str, Any]:
    """
    Send a test SMS message to verify configuration.
    
    Args:
        to_number: Phone number to send test message to
        message: Custom test message (optional)
        sms_service: RingCentral SMS service instance (optional)
    
    Returns:
        Send results
    """
    if not message:
        message = f"Test message from My Hibachi Chef CRM - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    try:
        # Use the utility function that leverages the existing service
        success = await send_sms_notification(to_number, message)
        
        return {
            "success": success,
            "to": to_number,
            "message": message,
            "sent_at": datetime.now().isoformat(),
            "service": "ringcentral_sms"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "to": to_number,
            "attempted_at": datetime.now().isoformat(),
            "service": "ringcentral_sms"
        }


def get_setup_checklist() -> Dict[str, Any]:
    """
    Get RingCentral setup checklist with current status.
    
    Returns:
        Setup checklist with completion status
    """
    config_validation = validate_configuration()
    
    checklist = {
        "setup_complete": config_validation["valid"],
        "steps": [
            {
                "step": 1,
                "title": "RingCentral Developer Account",
                "description": "Create account at https://developers.ringcentral.com",
                "completed": True,  # Assume completed if checking
                "required": True
            },
            {
                "step": 2,
                "title": "Application Registration",
                "description": "Create app with SMS/Voice permissions",
                "completed": bool(getattr(settings, 'ringcentral_client_id', None)),
                "required": True
            },
            {
                "step": 3,
                "title": "Environment Configuration", 
                "description": "Set RINGCENTRAL_* environment variables",
                "completed": len(config_validation["missing"]) == 0,
                "required": True,
                "missing": config_validation["missing"]
            },
            {
                "step": 4,
                "title": "Authentication Setup",
                "description": "Configure JWT token or username/password",
                "completed": bool(getattr(settings, 'ringcentral_jwt_token', None) or 
                                (getattr(settings, 'ringcentral_username', None) and 
                                 getattr(settings, 'ringcentral_password', None))),
                "required": True
            },
            {
                "step": 5,
                "title": "Phone Number Assignment",
                "description": "Assign phone number for SMS sending",
                "completed": bool(getattr(settings, 'ringcentral_phone_number', None) or 
                                getattr(settings, 'ringcentral_from_number', None)),
                "required": True
            },
            {
                "step": 6,
                "title": "Webhook Registration",
                "description": "Register webhook endpoints",
                "completed": False,  # Requires API check
                "required": False
            },
            {
                "step": 7,
                "title": "Test Configuration",
                "description": "Send test SMS and verify webhooks",
                "completed": False,  # Requires actual testing
                "required": False
            }
        ],
        "next_actions": []
    }
    
    # Add next actions based on missing steps
    for step in checklist["steps"]:
        if not step["completed"] and step["required"]:
            checklist["next_actions"].append(step["description"])
    
    return checklist