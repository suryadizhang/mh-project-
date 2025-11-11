"""
PII Masking Logging Filter
Redacts sensitive information from logs to protect customer privacy
"""

import re
import logging


class PIIMaskingFilter(logging.Filter):
    """
    Logging filter that masks Personally Identifiable Information (PII)
    in log messages before they are written to log files or console.

    Masks:
    - Phone numbers (US format: +1, 1-, (xxx) formats)
    - Email addresses
    - Credit card numbers (basic pattern)
    - SSN (xxx-xx-xxxx)
    - API keys and tokens (common patterns)
    """

    # Regex patterns for PII detection
    PHONE_PATTERNS = [
        # E.164 format: +1234567890
        re.compile(r"\+1\d{10}"),
        # US format with separators: (123) 456-7890, 123-456-7890, 123.456.7890
        re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"),
        # International format: +XX XXXX XXXXXX
        re.compile(r"\+\d{1,3}\s?\d{4,14}"),
    ]

    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    # Credit card pattern (basic - matches 13-19 digit sequences)
    CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4,7}\b")

    # SSN pattern: xxx-xx-xxxx
    SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    # API keys and tokens (common patterns)
    API_KEY_PATTERNS = [
        # Stripe keys: sk_test_..., pk_test_...
        re.compile(r"\b(sk|pk)_(test|live)_[A-Za-z0-9]{24,}\b"),
        # OpenAI keys: sk-...
        re.compile(r"\bsk-[A-Za-z0-9]{48}\b"),
        # JWT tokens (basic pattern)
        re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
        # Generic API keys (32+ alphanumeric)
        re.compile(r"\b[A-Za-z0-9]{32,}\b(?=\s*(key|token|secret|password))"),
    ]

    # Replacement strings
    PHONE_MASK = "***-***-****"
    EMAIL_MASK = "***@***.***"
    CARD_MASK = "****-****-****-****"
    SSN_MASK = "***-**-****"
    API_KEY_MASK = "***REDACTED***"

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record by masking PII in the message

        Args:
            record: LogRecord to filter

        Returns:
            True (always process the record, just mask PII first)
        """
        # Mask PII in the main log message
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = self._mask_pii(record.msg)

        # Mask PII in log record arguments
        if hasattr(record, "args") and record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._mask_pii(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._mask_pii(str(arg)) if isinstance(arg, str) else arg for arg in record.args
                )

        return True

    def _mask_pii(self, text: str) -> str:
        """
        Mask all PII patterns in the given text

        Args:
            text: Text that may contain PII

        Returns:
            Text with PII masked
        """
        # Mask phone numbers
        for pattern in self.PHONE_PATTERNS:
            text = pattern.sub(self.PHONE_MASK, text)

        # Mask emails
        text = self.EMAIL_PATTERN.sub(self.EMAIL_MASK, text)

        # Mask credit cards
        text = self.CREDIT_CARD_PATTERN.sub(self.CARD_MASK, text)

        # Mask SSN
        text = self.SSN_PATTERN.sub(self.SSN_MASK, text)

        # Mask API keys
        for pattern in self.API_KEY_PATTERNS:
            text = pattern.sub(self.API_KEY_MASK, text)

        return text


def configure_pii_masking_for_logger(logger: logging.Logger) -> None:
    """
    Add PII masking filter to a logger

    Args:
        logger: Logger instance to configure

    Example:
        import logging
        logger = logging.getLogger(__name__)
        configure_pii_masking_for_logger(logger)
    """
    pii_filter = PIIMaskingFilter()
    logger.addFilter(pii_filter)


def configure_pii_masking_globally() -> None:
    """
    Add PII masking to the root logger (affects all loggers)

    Call this in application startup to mask PII across all logs.

    Example:
        # In main.py or app initialization
        from core.logging.pii_masking import configure_pii_masking_globally
        configure_pii_masking_globally()
    """
    root_logger = logging.getLogger()
    pii_filter = PIIMaskingFilter()
    root_logger.addFilter(pii_filter)

    # Also add to all handlers to ensure masking happens
    for handler in root_logger.handlers:
        handler.addFilter(pii_filter)


# Example usage:
if __name__ == "__main__":
    # Configure logging with PII masking
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Enable PII masking globally
    configure_pii_masking_globally()

    logger = logging.getLogger(__name__)

    # Test PII masking
    logger.info("Customer called from +19167408768")
    logger.info("Email received: customer@example.com")
    logger.info("Processing payment with card 4111-1111-1111-1111")
    logger.info("SSN verification: 123-45-6789")
    logger.info("Using API key: sk_test_EXAMPLE_KEY_NOT_REAL")
    logger.info("Customer phone: (916) 740-8768, email: test@myhibachi.com")

    # Output should show masked values
    # Customer called from ***-***-****
    # Email received: ***@***.***
    # Processing payment with card ****-****-****-****
    # SSN verification: ***-**-****
    # Using API key: ***REDACTED***
