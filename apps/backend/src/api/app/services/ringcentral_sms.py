"""RingCentral SMS integration service."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
import asyncio
from dataclasses import dataclass

from api.app.config import settings


logger = logging.getLogger(__name__)


@dataclass
class SMSMessage:
    """SMS message data structure."""
    id: str
    from_number: str
    to_number: str
    body: str
    direction: str  # 'Inbound' or 'Outbound'
    creation_time: datetime
    last_modified_time: datetime
    message_status: str
    conversation_id: Optional[str] = None


@dataclass
class SMSResponse:
    """SMS send response."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class RingCentralSMSService:
    """RingCentral SMS integration service."""

    def __init__(self):
        self.client_id = settings.ringcentral_client_id
        self.client_secret = settings.ringcentral_client_secret
        self.server_url = settings.ringcentral_server_url or "https://platform.ringcentral.com"
        self.username = settings.ringcentral_username
        self.extension = getattr(settings, 'ringcentral_extension', '101')
        self.password = settings.ringcentral_password
        # Enhanced configuration support
        self.jwt_token = getattr(settings, 'ringcentral_jwt_token', '')
        self.phone_number = getattr(settings, 'ringcentral_phone_number', settings.ringcentral_from_number)
        self.webhook_secret = getattr(settings, 'ringcentral_webhook_secret', '')
        self.sandbox_mode = getattr(settings, 'ringcentral_sandbox', True)
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=30.0)
        await self.authenticate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def authenticate(self) -> bool:
        """Authenticate with RingCentral using JWT token or username/password."""
        # Try JWT authentication first if token is available
        if self.jwt_token:
            return await self._authenticate_with_jwt()
        
        # Fall back to username/password authentication
        if not all([self.client_id, self.client_secret, self.username, self.password]):
            logger.error("RingCentral credentials not configured")
            return False

        try:
            auth_data = {
                "grant_type": "password",
                "username": self.username,
                "extension": self.extension,
                "password": self.password
            }

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            response = await self._client.post(
                f"{self.server_url}/restapi/oauth/token",
                data=auth_data,
                headers=headers,
                auth=(self.client_id, self.client_secret)
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                logger.info("RingCentral authentication successful")
                return True
            else:
                logger.error(f"RingCentral authentication failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"RingCentral authentication error: {str(e)}")
            return False

    async def _authenticate_with_jwt(self) -> bool:
        """Authenticate using JWT token."""
        try:
            auth_data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": self.jwt_token
            }

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            response = await self._client.post(
                f"{self.server_url}/restapi/oauth/token",
                data=auth_data,
                headers=headers,
                auth=(self.client_id, self.client_secret)
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                logger.info("RingCentral JWT authentication successful")
                return True
            else:
                logger.error(f"RingCentral JWT authentication failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"RingCentral JWT authentication error: {str(e)}")
            return False

    async def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid access token."""
        if not self.access_token or (self.token_expires_at and datetime.now() >= self.token_expires_at):
            return await self.authenticate()
        return True

    async def send_sms(self, to_number: str, message: str, from_number: Optional[str] = None) -> SMSResponse:
        """Send SMS message."""
        if not await self._ensure_authenticated():
            return SMSResponse(success=False, error="Authentication failed")

        try:
            sms_data = {
                "to": [{"phoneNumber": to_number}],
                "text": message
            }

            if from_number:
                sms_data["from"] = {"phoneNumber": from_number}

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            response = await self._client.post(
                f"{self.server_url}/restapi/v1.0/account/~/extension/~/sms",
                json=sms_data,
                headers=headers
            )

            if response.status_code in [200, 201]:
                result = response.json()
                return SMSResponse(
                    success=True,
                    message_id=str(result.get("id"))
                )
            else:
                error_msg = f"SMS send failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return SMSResponse(success=False, error=error_msg)

        except Exception as e:
            error_msg = f"SMS send error: {str(e)}"
            logger.error(error_msg)
            return SMSResponse(success=False, error=error_msg)

    async def get_messages(self, date_from: Optional[datetime] = None, 
                          date_to: Optional[datetime] = None,
                          message_type: str = "SMS",
                          direction: Optional[str] = None,
                          per_page: int = 100) -> List[SMSMessage]:
        """Get SMS messages from RingCentral."""
        if not await self._ensure_authenticated():
            return []

        try:
            params = {
                "messageType": message_type,
                "perPage": per_page
            }

            if date_from:
                params["dateFrom"] = date_from.isoformat()
            if date_to:
                params["dateTo"] = date_to.isoformat()
            if direction:
                params["direction"] = direction

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }

            response = await self._client.get(
                f"{self.server_url}/restapi/v1.0/account/~/extension/~/message-store",
                params=params,
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                messages = []
                
                for record in data.get("records", []):
                    # Parse creation time
                    creation_time = datetime.fromisoformat(
                        record["creationTime"].replace("Z", "+00:00")
                    )
                    last_modified = datetime.fromisoformat(
                        record["lastModifiedTime"].replace("Z", "+00:00")
                    )

                    # Get phone numbers
                    from_number = ""
                    to_number = ""
                    if record.get("from"):
                        from_number = record["from"].get("phoneNumber", "")
                    if record.get("to") and len(record["to"]) > 0:
                        to_number = record["to"][0].get("phoneNumber", "")

                    message = SMSMessage(
                        id=str(record["id"]),
                        from_number=from_number,
                        to_number=to_number,
                        body=record.get("subject", ""),
                        direction=record.get("direction", ""),
                        creation_time=creation_time,
                        last_modified_time=last_modified,
                        message_status=record.get("messageStatus", ""),
                        conversation_id=str(record.get("conversationId", ""))
                    )
                    messages.append(message)

                return messages
            else:
                logger.error(f"Get messages failed: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Get messages error: {str(e)}")
            return []

    async def get_conversation_messages(self, conversation_id: str) -> List[SMSMessage]:
        """Get all messages in a conversation."""
        if not await self._ensure_authenticated():
            return []

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }

            response = await self._client.get(
                f"{self.server_url}/restapi/v1.0/account/~/extension/~/message-store/{conversation_id}",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                # Process conversation data similar to get_messages
                # This is a simplified version - you may need to adapt based on actual API response
                return await self.get_messages()  # Fallback to general message retrieval
            else:
                logger.error(f"Get conversation failed: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Get conversation error: {str(e)}")
            return []

    async def setup_webhook(self, webhook_url: str, event_filters: List[str] = None) -> bool:
        """Setup webhook for real-time SMS notifications."""
        if not await self._ensure_authenticated():
            return False

        if event_filters is None:
            event_filters = [
                "/restapi/v1.0/account/~/extension/~/message-store/instant?type=SMS"
            ]

        try:
            webhook_data = {
                "targetUrl": webhook_url,
                "eventFilters": event_filters,
                "expiresIn": 604800  # 7 days
            }

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            response = await self._client.post(
                f"{self.server_url}/restapi/v1.0/subscription",
                json=webhook_data,
                headers=headers
            )

            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Webhook created: {result.get('id')}")
                return True
            else:
                logger.error(f"Webhook setup failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Webhook setup error: {str(e)}")
            return False

    async def handle_webhook_notification(self, payload: Dict[str, Any]) -> List[SMSMessage]:
        """Process incoming webhook notification."""
        messages = []
        
        try:
            body = payload.get("body", {})
            changes = body.get("changes", [])
            
            for change in changes:
                if change.get("type") == "SMS":
                    # Extract message data from webhook
                    new_messages = change.get("newMessages", [])
                    for msg_data in new_messages:
                        # Convert webhook message format to SMSMessage
                        creation_time = datetime.fromisoformat(
                            msg_data["creationTime"].replace("Z", "+00:00")
                        )
                        
                        message = SMSMessage(
                            id=str(msg_data["id"]),
                            from_number=msg_data.get("from", {}).get("phoneNumber", ""),
                            to_number=msg_data.get("to", [{}])[0].get("phoneNumber", "") if msg_data.get("to") else "",
                            body=msg_data.get("subject", ""),
                            direction=msg_data.get("direction", ""),
                            creation_time=creation_time,
                            last_modified_time=creation_time,
                            message_status=msg_data.get("messageStatus", ""),
                            conversation_id=str(msg_data.get("conversationId", ""))
                        )
                        messages.append(message)
        
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
        
        return messages

    async def get_account_info(self) -> Dict[str, Any]:
        """Get RingCentral account information."""
        if not await self._ensure_authenticated():
            return {}

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = await self._client.get(
                f"{self.server_url}/restapi/v1.0/account/~",
                headers=headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Account info failed: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"Account info error: {str(e)}")
            return {}

    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature for security."""
        if not self.webhook_secret or not signature:
            return False
        
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of RingCentral service."""
        health_status = {
            "service": "ringcentral_sms",
            "status": "unknown",
            "authentication": "failed",
            "configuration": "incomplete",
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Check configuration
            config_ok = bool(self.client_id and self.client_secret)
            auth_method = "jwt" if self.jwt_token else "password" if (self.username and self.password) else "none"
            
            health_status["configuration"] = "complete" if config_ok else "incomplete"
            health_status["auth_method"] = auth_method

            if config_ok and auth_method != "none":
                # Test authentication
                if await self._ensure_authenticated():
                    health_status["authentication"] = "successful"
                    health_status["status"] = "healthy"
                    
                    # Get account info for additional details
                    account_info = await self.get_account_info()
                    if account_info:
                        health_status["account_name"] = account_info.get("name", "Unknown")
                        health_status["account_status"] = account_info.get("status", "Unknown")
                else:
                    health_status["status"] = "unhealthy"
            else:
                health_status["status"] = "misconfigured"

        except Exception as e:
            health_status["status"] = "error"
            health_status["error"] = str(e)

        return health_status


# Service instance
ringcentral_sms = RingCentralSMSService()


async def send_sms_notification(phone_number: str, message: str) -> bool:
    """Send SMS notification using RingCentral."""
    async with ringcentral_sms as sms_service:
        response = await sms_service.send_sms(phone_number, message)
        return response.success


async def sync_sms_messages() -> List[SMSMessage]:
    """Sync recent SMS messages from RingCentral."""
    async with ringcentral_sms as sms_service:
        # Get messages from the last 24 hours
        date_from = datetime.now() - timedelta(days=1)
        return await sms_service.get_messages(date_from=date_from)