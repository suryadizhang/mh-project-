"""
Channel Manager for handling webhooks and outbound messaging
Supports RingCentral SMS/Voice, Meta (Facebook/Instagram), and Website chat
"""

import hashlib
import hmac
import os
from typing import Any, Optional

import httpx
from fastapi import HTTPException

from api.ai.endpoints.schemas import ChannelType


class ChannelManager:
    """Manages multi-channel communication (RingCentral, Meta, Website)"""

    def __init__(self):
        # RingCentral configuration
        self.rc_client_id = os.getenv("RINGCENTRAL_CLIENT_ID")
        self.rc_client_secret = os.getenv("RINGCENTRAL_CLIENT_SECRET")
        self.rc_jwt = os.getenv("RINGCENTRAL_JWT")
        self.rc_webhook_secret = os.getenv("RINGCENTRAL_WEBHOOK_SECRET")
        self.rc_server_url = os.getenv(
            "RINGCENTRAL_SERVER_URL", "https://platform.ringcentral.com"
        )

        # Meta configuration
        self.meta_app_id = os.getenv("META_APP_ID")
        self.meta_app_secret = os.getenv("META_APP_SECRET")
        self.meta_page_access_token = os.getenv("META_PAGE_ACCESS_TOKEN")
        self.meta_verify_token = os.getenv(
            "META_VERIFY_TOKEN", "myhibachi_verify_2024"
        )

        # HTTP client for API calls
        self.http_client = httpx.AsyncClient()

    # RingCentral SMS/Voice Handlers
    def validate_ringcentral_webhook(
        self, body: bytes, signature: str
    ) -> bool:
        """Validate RingCentral webhook signature"""
        if not self.rc_webhook_secret:
            return True  # Skip validation if no secret configured

        expected_signature = hmac.new(
            self.rc_webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def parse_ringcentral_sms(
        self, webhook_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Parse RingCentral SMS webhook data"""
        try:
            message = webhook_data.get("body", {})

            # Extract SMS details
            from_number = message.get("from", {}).get("phoneNumber", "")
            to_number = message.get("to", [{}])[0].get("phoneNumber", "")
            text = message.get("subject", "")

            return {
                "channel": ChannelType.SMS,
                "user_id": from_number,
                "thread_id": f"sms-{from_number.replace('+', '')}",
                "text": text,
                "metadata": {
                    "from_number": from_number,
                    "to_number": to_number,
                    "message_id": message.get("id"),
                    "timestamp": message.get("creationTime"),
                },
            }
        except Exception as e:
            print(f"Error parsing RingCentral SMS: {e}")
            raise HTTPException(
                status_code=400, detail="Invalid SMS webhook data"
            )

    def parse_ringcentral_voice(
        self, webhook_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Parse RingCentral voice webhook data"""
        try:
            event_type = webhook_data.get("event")
            telephony_status = webhook_data.get("body", {}).get(
                "telephonyStatus"
            )

            if (
                event_type
                == "/restapi/v1.0/account/~/extension/~/telephony/sessions"
                and telephony_status in ["Answered", "Disconnected"]
            ):
                session = webhook_data.get("body", {})
                parties = session.get("parties", [])

                # Find customer party
                customer_party = None
                for party in parties:
                    if party.get("direction") == "Inbound":
                        customer_party = party
                        break

                if customer_party:
                    from_number = customer_party.get("from", {}).get(
                        "phoneNumber", ""
                    )

                    return {
                        "channel": ChannelType.VOICE,
                        "user_id": from_number,
                        "thread_id": f"voice-{from_number.replace('+', '')}",
                        "text": f"Voice call {telephony_status.lower()}",
                        "metadata": {
                            "session_id": session.get("sessionId"),
                            "telephony_status": telephony_status,
                            "from_number": from_number,
                            "timestamp": session.get("creationTime"),
                        },
                    }

            return None  # Not a relevant voice event

        except Exception as e:
            print(f"Error parsing RingCentral voice: {e}")
            return None

    async def send_sms(self, to_number: str, message: str) -> bool:
        """Send SMS via RingCentral"""
        try:
            # Get access token (simplified - in production, implement proper OAuth)
            if not self.rc_jwt:
                print("RingCentral JWT not configured")
                return False

            headers = {
                "Authorization": f"Bearer {self.rc_jwt}",
                "Content-Type": "application/json",
            }

            payload = {
                "from": {
                    "phoneNumber": os.getenv(
                        "RINGCENTRAL_FROM_NUMBER", "+1234567890"
                    )
                },
                "to": [{"phoneNumber": to_number}],
                "text": message,
            }

            url = (
                f"{self.rc_server_url}/restapi/v1.0/account/~/extension/~/sms"
            )
            response = await self.http_client.post(
                url, headers=headers, json=payload
            )

            if response.status_code == 200:
                print(f"SMS sent to {to_number}")
                return True
            else:
                print(
                    f"Failed to send SMS: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            print(f"Error sending SMS: {e}")
            return False

    # Meta (Facebook/Instagram) Handlers
    def validate_meta_webhook(self, body: str, signature: str) -> bool:
        """Validate Meta webhook signature"""
        if not self.meta_app_secret:
            return True

        expected_signature = hmac.new(
            self.meta_app_secret.encode(), body.encode(), hashlib.sha1
        ).hexdigest()

        return hmac.compare_digest(signature, f"sha1={expected_signature}")

    def verify_meta_webhook(
        self, mode: str, token: str, challenge: str
    ) -> Optional[str]:
        """Verify Meta webhook subscription"""
        if mode == "subscribe" and token == self.meta_verify_token:
            return challenge
        return None

    def parse_meta_webhook(
        self, webhook_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Parse Meta webhook data for messages"""
        messages = []

        try:
            for entry in webhook_data.get("entry", []):
                # Handle Messenger messages
                for messaging in entry.get("messaging", []):
                    if "message" in messaging:
                        sender_id = messaging["sender"]["id"]
                        recipient_id = messaging["recipient"]["id"]
                        message_text = messaging["message"].get("text", "")

                        if message_text:  # Only process text messages for now
                            messages.append(
                                {
                                    "channel": ChannelType.FACEBOOK,
                                    "user_id": sender_id,
                                    "thread_id": f"fb-{sender_id}",
                                    "text": message_text,
                                    "metadata": {
                                        "platform": "facebook",
                                        "sender_id": sender_id,
                                        "recipient_id": recipient_id,
                                        "timestamp": messaging.get(
                                            "timestamp"
                                        ),
                                    },
                                }
                            )

                # Handle Instagram messages
                for messaging in entry.get("messaging", []):
                    if "message" in messaging and "instagram" in str(
                        entry.get("id", "")
                    ):
                        sender_id = messaging["sender"]["id"]
                        message_text = messaging["message"].get("text", "")

                        if message_text:
                            messages.append(
                                {
                                    "channel": ChannelType.INSTAGRAM,
                                    "user_id": sender_id,
                                    "thread_id": f"ig-{sender_id}",
                                    "text": message_text,
                                    "metadata": {
                                        "platform": "instagram",
                                        "sender_id": sender_id,
                                        "timestamp": messaging.get(
                                            "timestamp"
                                        ),
                                    },
                                }
                            )

                # Handle comment replies (both FB and IG)
                for change in entry.get("changes", []):
                    if (
                        change.get("field") == "feed"
                        and change.get("value", {}).get("item") == "comment"
                    ):
                        comment_data = change["value"]
                        comment_text = comment_data.get("message", "")
                        sender_id = comment_data.get("sender_id")
                        post_id = comment_data.get("post_id")
                        comment_id = comment_data.get("comment_id")

                        if comment_text and sender_id:
                            messages.append(
                                {
                                    "channel": ChannelType.FACEBOOK,
                                    "user_id": sender_id,
                                    "thread_id": f"comment-{post_id}-{comment_id}",
                                    "text": comment_text,
                                    "metadata": {
                                        "platform": "facebook",
                                        "type": "comment",
                                        "post_id": post_id,
                                        "comment_id": comment_id,
                                        "sender_id": sender_id,
                                    },
                                }
                            )

        except Exception as e:
            print(f"Error parsing Meta webhook: {e}")

        return messages

    async def send_facebook_message(
        self, recipient_id: str, message: str
    ) -> bool:
        """Send message via Facebook Messenger"""
        try:
            if not self.meta_page_access_token:
                print("Meta page access token not configured")
                return False

            url = "https://graph.facebook.com/v18.0/me/messages"
            params = {"access_token": self.meta_page_access_token}

            payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": message},
            }

            response = await self.http_client.post(
                url, params=params, json=payload
            )

            if response.status_code == 200:
                print(f"Facebook message sent to {recipient_id}")
                return True
            else:
                print(
                    f"Failed to send Facebook message: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            print(f"Error sending Facebook message: {e}")
            return False

    async def reply_to_comment(self, comment_id: str, message: str) -> bool:
        """Reply to a Facebook/Instagram comment"""
        try:
            if not self.meta_page_access_token:
                print("Meta page access token not configured")
                return False

            url = f"https://graph.facebook.com/v18.0/{comment_id}/comments"
            params = {"access_token": self.meta_page_access_token}

            payload = {"message": message}

            response = await self.http_client.post(
                url, params=params, json=payload
            )

            if response.status_code == 200:
                print(f"Comment reply sent to {comment_id}")
                return True
            else:
                print(
                    f"Failed to reply to comment: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            print(f"Error replying to comment: {e}")
            return False

    # Unified outbound messaging
    async def send_message(
        self,
        channel: ChannelType,
        recipient_id: str,
        message: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Send message through appropriate channel"""
        try:
            if channel == ChannelType.SMS:
                return await self.send_sms(recipient_id, message)
            elif channel == ChannelType.FACEBOOK:
                if metadata and metadata.get("type") == "comment":
                    return await self.reply_to_comment(
                        metadata["comment_id"], message
                    )
                else:
                    return await self.send_facebook_message(
                        recipient_id, message
                    )
            elif channel == ChannelType.INSTAGRAM:
                return await self.send_facebook_message(recipient_id, message)
            else:
                print(f"Unsupported channel for outbound messaging: {channel}")
                return False

        except Exception as e:
            print(f"Error sending message via {channel}: {e}")
            return False

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# Global instance
channel_manager = ChannelManager()
