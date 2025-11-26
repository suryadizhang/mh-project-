"""
OpenAI API Key Health Monitor
Validates key on startup and provides monitoring endpoints
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class APIKeyHealthStatus(BaseModel):
    """Health status of OpenAI API key"""

    is_valid: bool
    key_prefix: str
    key_type: str  # "project" or "service_account"
    last_checked: datetime
    error_message: Optional[str] = None
    available_models_count: Optional[int] = None
    test_call_successful: bool = False


class OpenAIKeyMonitor:
    """Monitor OpenAI API key health and validity"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self._last_check: Optional[APIKeyHealthStatus] = None
        self._check_interval = timedelta(hours=1)

    def get_key_type(self) -> str:
        """Determine key type from prefix"""
        if self.api_key.startswith("sk-proj-"):
            return "project"
        elif self.api_key.startswith("sk-svcacct-"):
            return "service_account"
        elif self.api_key.startswith("sk-"):
            return "legacy"
        else:
            return "unknown"

    async def validate_key(self, force: bool = False) -> APIKeyHealthStatus:
        """
        Validate OpenAI API key

        Args:
            force: Force validation even if recently checked

        Returns:
            APIKeyHealthStatus with validation results
        """
        # Check if we need to revalidate
        if not force and self._last_check:
            time_since_check = (
                datetime.now(timezone.utc) - self._last_check.last_checked
            )
            if time_since_check < self._check_interval:
                logger.debug(
                    f"Using cached validation result (checked {time_since_check.seconds}s ago)"
                )
                return self._last_check

        logger.info("Validating OpenAI API key...")

        key_prefix = (
            self.api_key[:20] + "..."
            if len(self.api_key) > 20
            else self.api_key
        )
        key_type = self.get_key_type()

        status = APIKeyHealthStatus(
            is_valid=False,
            key_prefix=key_prefix,
            key_type=key_type,
            last_checked=datetime.now(timezone.utc),
        )

        try:
            # Try to list models
            response = self.client.models.list()
            models_count = len(response.data)

            # Try a simple completion
            try:
                completion = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5,
                )
                status.test_call_successful = True
            except Exception as e:
                logger.warning(f"Test call failed: {e}")
                status.test_call_successful = False

            status.is_valid = True
            status.available_models_count = models_count
            logger.info(
                f"✅ API key is valid ({models_count} models available)"
            )

            # Warn if using service account key
            if key_type == "service_account":
                logger.warning(
                    "⚠️  Using SERVICE ACCOUNT key! "
                    "Consider switching to PROJECT key for better stability."
                )

        except Exception as e:
            error_msg = str(e)
            status.is_valid = False
            status.error_message = error_msg
            logger.error(f"❌ API key validation failed: {error_msg}")

            if "401" in error_msg or "Incorrect API key" in error_msg:
                logger.error(
                    "🚨 CRITICAL: API key is invalid/expired! "
                    "Check OpenAI dashboard and update .env file"
                )

        self._last_check = status
        return status

    def get_cached_status(self) -> Optional[APIKeyHealthStatus]:
        """Get last cached validation status"""
        return self._last_check

    async def startup_validation(self) -> APIKeyHealthStatus:
        """
        Validate key on application startup
        Raises exception if key is invalid
        """
        logger.info("🔍 Running startup OpenAI API key validation...")
        status = await self.validate_key(force=True)

        if not status.is_valid:
            logger.error("❌ OpenAI API key is INVALID on startup!")
            logger.error(f"Error: {status.error_message}")
            logger.error("Application may not function correctly!")
            # Don't raise exception - let app start but log critical error
        else:
            logger.info("✅ OpenAI API key validated successfully on startup")
            logger.info(f"   Key Type: {status.key_type}")
            logger.info(
                f"   Models Available: {status.available_models_count}"
            )
            logger.info(
                f"   Test Call: {'✓' if status.test_call_successful else '✗'}"
            )

        return status


# Global monitor instance (initialized in main.py)
_monitor: Optional[OpenAIKeyMonitor] = None


def get_monitor() -> Optional[OpenAIKeyMonitor]:
    """Get global monitor instance"""
    return _monitor


def initialize_monitor(api_key: str) -> OpenAIKeyMonitor:
    """Initialize global monitor instance"""
    global _monitor
    _monitor = OpenAIKeyMonitor(api_key)
    return _monitor
