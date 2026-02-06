"""
RingCentral Integration Service
Wrapper for RingCentral API operations: SMS, calls, recordings
"""

import logging
import os
from datetime import datetime
from typing import Optional
from ringcentral import SDK

logger = logging.getLogger(__name__)


class RingCentralService:
    """Service for interacting with RingCentral API"""

    def __init__(self):
        """Initialize RingCentral SDK"""
        self.client_id = os.getenv("RINGCENTRAL_CLIENT_ID")
        self.client_secret = os.getenv("RINGCENTRAL_CLIENT_SECRET")
        self.server_url = os.getenv("RINGCENTRAL_SERVER_URL", "https://platform.ringcentral.com")
        self.jwt_token = os.getenv("RINGCENTRAL_JWT_TOKEN")
        self.from_phone = os.getenv("RINGCENTRAL_FROM_PHONE")  # Your business phone number

        if not all([self.client_id, self.client_secret, self.jwt_token]):
            logger.warning("RingCentral credentials not configured")
            self.sdk = None
            return

        try:
            self.sdk = SDK(self.client_id, self.client_secret, self.server_url)
            self.platform = self.sdk.platform()
            # Authenticate with JWT
            self.platform.login(jwt=self.jwt_token)
            logger.info("RingCentral SDK initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RingCentral SDK: {str(e)}")
            self.sdk = None

    def is_configured(self) -> bool:
        """Check if RingCentral is properly configured"""
        return self.sdk is not None and self.platform.logged_in()

    def send_sms(self, to_phone: str, message: str, metadata: Optional[dict] = None) -> dict:
        """
        Send SMS message via RingCentral

        Args:
            to_phone: Recipient phone number (E.164 format preferred)
            message: SMS message content (max 1600 chars)
            metadata: Optional metadata to track with the message

        Returns:
            dict with message_id, status, sent_at

        Raises:
            RuntimeError: If SMS send fails
        """
        if not self.is_configured():
            raise RuntimeError("RingCentral not configured")

        try:
            # Normalize phone number (remove spaces, dashes)
            to_phone = to_phone.replace(" ", "").replace("-", "")
            if not to_phone.startswith("+"):
                to_phone = f"+1{to_phone}"  # Assume US number

            # Truncate message if needed
            if len(message) > 1600:
                message = message[:1597] + "..."
                logger.warning(f"SMS message truncated to 1600 chars for {to_phone}")

            # Send via RingCentral API
            response = self.platform.post(
                "/restapi/v1.0/account/~/extension/~/sms",
                {
                    "from": {"phoneNumber": self.from_phone},
                    "to": [{"phoneNumber": to_phone}],
                    "text": message,
                },
            )

            result = response.json()
            message_id = result.get("id")

            logger.info(f"SMS sent successfully to {to_phone}, message_id: {message_id}")

            return {
                "message_id": str(message_id),
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat(),
                "to_phone": to_phone,
                "from_phone": self.from_phone,
            }

        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone}: {str(e)}")
            raise RuntimeError(f"SMS send failed: {str(e)}")

    def initiate_call(self, to_phone: str, from_phone: Optional[str] = None) -> dict:
        """
        Initiate outbound call via RingCentral

        Args:
            to_phone: Phone number to call
            from_phone: Optional caller ID (defaults to business number)

        Returns:
            dict with call_id, status

        Raises:
            RuntimeError: If call initiation fails
        """
        if not self.is_configured():
            raise RuntimeError("RingCentral not configured")

        try:
            # Normalize phone number
            to_phone = to_phone.replace(" ", "").replace("-", "")
            if not to_phone.startswith("+"):
                to_phone = f"+1{to_phone}"

            from_phone = from_phone or self.from_phone

            # Initiate call via RingOut API
            response = self.platform.post(
                "/restapi/v1.0/account/~/extension/~/ring-out",
                {
                    "from": {"phoneNumber": from_phone},
                    "to": {"phoneNumber": to_phone},
                    "playPrompt": False,  # Don't play prompt
                },
            )

            result = response.json()
            call_id = result.get("id")

            logger.info(f"Call initiated to {to_phone}, call_id: {call_id}")

            return {
                "call_id": str(call_id),
                "status": result.get("status", {}).get("callStatus", "initiated"),
                "to_phone": to_phone,
                "from_phone": from_phone,
            }

        except Exception as e:
            logger.error(f"Failed to initiate call to {to_phone}: {str(e)}")
            raise RuntimeError(f"Call initiation failed: {str(e)}")

    def get_recording(self, recording_id: str) -> bytes:
        """
        Download call recording content from RingCentral

        Args:
            recording_id: RingCentral recording ID

        Returns:
            bytes: Recording audio file content

        Raises:
            RuntimeError: If recording download fails
        """
        if not self.is_configured():
            raise RuntimeError("RingCentral not configured")

        try:
            # Get recording content
            response = self.platform.get(
                f"/restapi/v1.0/account/~/recording/{recording_id}/content"
            )

            content = response.response().content

            logger.info(f"Recording {recording_id} downloaded, size: {len(content)} bytes")

            return content

        except Exception as e:
            logger.error(f"Failed to download recording {recording_id}: {str(e)}")
            raise RuntimeError(f"Recording download failed: {str(e)}")

    def get_recording_metadata(self, recording_id: str) -> dict:
        """
        Get recording metadata from RingCentral

        Args:
            recording_id: RingCentral recording ID

        Returns:
            dict with recording metadata

        Raises:
            RuntimeError: If metadata fetch fails
        """
        if not self.is_configured():
            raise RuntimeError("RingCentral not configured")

        try:
            response = self.platform.get(f"/restapi/v1.0/account/~/recording/{recording_id}")

            metadata = response.json()

            return {
                "recording_id": metadata.get("id"),
                "duration": metadata.get("duration"),
                "content_type": metadata.get("contentType", "audio/mpeg"),
                "uri": metadata.get("contentUri"),
            }

        except Exception as e:
            logger.error(f"Failed to get recording metadata {recording_id}: {str(e)}")
            raise RuntimeError(f"Recording metadata fetch failed: {str(e)}")

    def get_call_transcript(self, call_session_id: str) -> dict:
        """
        Get AI-generated transcript from RingCentral AI Insights.

        RingCentral AI provides automatic transcription with:
        - Full transcript with timestamps
        - Speaker separation
        - Confidence scores
        - AI insights (sentiment, topics, action items)

        Args:
            call_session_id: RingCentral call session ID

        Returns:
            dict with transcript and AI insights:
            - full_text: Complete transcript
            - confidence: Average confidence score (0-100)
            - segments: List of transcript segments with timestamps
            - insights: AI-extracted insights (sentiment, topics, etc)

        Raises:
            RuntimeError: If transcript fetch fails
        """
        if not self.is_configured():
            raise RuntimeError("RingCentral not configured")

        try:
            # Get transcript from RC AI Insights API
            response = self.platform.get(
                f"/restapi/v1.0/account/~/call-log/{call_session_id}/transcript"
            )

            result = response.json()

            # Extract transcript segments
            segments = result.get("segments", [])
            full_transcript = " ".join([seg.get("text", "") for seg in segments])

            # Calculate average confidence
            confidences = [seg.get("confidence", 0) for seg in segments if seg.get("confidence")]
            avg_confidence = int(sum(confidences) / len(confidences) * 100) if confidences else 0

            # Extract AI insights if available
            insights = {
                "sentiment": result.get("sentiment", {}),
                "topics": result.get("topics", []),
                "action_items": result.get("actionItems", []),
                "intent": result.get("intent"),
                "speakers": result.get("speakers", []),
                "keywords": result.get("keywords", []),
            }

            logger.info(
                f"Transcript fetched for call {call_session_id}: "
                f"{len(full_transcript)} chars, {avg_confidence}% confidence"
            )

            return {
                "full_text": full_transcript,
                "confidence": avg_confidence,
                "segments": segments,
                "insights": insights,
                "fetched_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to fetch transcript for {call_session_id}: {str(e)}")
            # Return empty result if RC AI not available (graceful degradation)
            return {
                "full_text": "",
                "confidence": 0,
                "segments": [],
                "insights": {},
                "error": str(e),
            }

    def get_recording_stream_url(self, recording_id: str, expires_in: int = 3600) -> str:
        """
        Get temporary streaming URL for recording playback.

        Returns a time-limited URL to stream recording audio.
        No download needed - stream directly from RingCentral.

        Args:
            recording_id: RingCentral recording ID
            expires_in: URL expiration in seconds (default 1 hour)

        Returns:
            str: Streaming URL with embedded auth token

        Raises:
            RuntimeError: If URL generation fails
        """
        if not self.is_configured():
            raise RuntimeError("RingCentral not configured")

        try:
            # RingCentral API returns content URL directly
            response = self.platform.get(f"/restapi/v1.0/account/~/recording/{recording_id}")

            result = response.json()
            content_uri = result.get("contentUri")

            if not content_uri:
                raise ValueError("No content URI in recording metadata")

            # Return the content URI (already includes auth token)
            logger.info(f"Generated streaming URL for recording {recording_id}")

            return content_uri

        except Exception as e:
            logger.error(f"Failed to get streaming URL for {recording_id}: {str(e)}")
            raise RuntimeError(f"Stream URL generation failed: {str(e)}")

    def verify_webhook_signature(self, signature: str, body: bytes) -> bool:
        """
        Verify RingCentral webhook signature

        Args:
            signature: Signature from X-RingCentral-Signature header
            body: Raw request body bytes

        Returns:
            bool: True if signature is valid

        Note:
            Requires RINGCENTRAL_WEBHOOK_SECRET environment variable
        """
        import hmac
        import hashlib

        webhook_secret = os.getenv("RINGCENTRAL_WEBHOOK_SECRET")
        if not webhook_secret:
            logger.warning("RINGCENTRAL_WEBHOOK_SECRET not configured")
            return False

        try:
            expected_signature = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()

            is_valid = hmac.compare_digest(signature, expected_signature)

            if not is_valid:
                logger.warning("Invalid RingCentral webhook signature")

            return is_valid

        except Exception as e:
            logger.error(f"Failed to verify webhook signature: {str(e)}")
            return False


# Singleton instance
_ringcentral_service: Optional[RingCentralService] = None


def get_ringcentral_service() -> RingCentralService:
    """Get singleton RingCentral service instance"""
    global _ringcentral_service
    if _ringcentral_service is None:
        _ringcentral_service = RingCentralService()
    return _ringcentral_service
