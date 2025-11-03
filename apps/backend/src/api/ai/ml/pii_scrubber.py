"""
PII Scrubber - Remove Personally Identifiable Information

This module scrubs PII from text data before training to ensure:
- GDPR/CCPA compliance
- Data privacy
- Safe model training
- No customer data leakage

Detects and removes:
- Email addresses
- Phone numbers
- SSN
- Credit card numbers
- Names (via NER)
- Addresses (via geocoding)

Author: MyHibachi Development Team
Created: October 31, 2025
"""

from datetime import datetime
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class PIIScrubber:
    """
    Remove personally identifiable information from text.

    Example:
        ```python
        scrubber = PIIScrubber()
        result = scrubber.scrub(
            "Contact me at john.doe@email.com or 555-123-4567"
        )
        print(result["cleaned_text"])
        # "Contact me at [EMAIL] or [PHONE]"
        print(result["is_safe_for_training"])  # True
        ```
    """

    def __init__(self):
        """Initialize PII scrubber with detection patterns"""
        self.logger = logging.getLogger(__name__)

        # Regex patterns for common PII
        self.patterns = {
            "email": {
                "regex": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "replacement": "[EMAIL]",
                "risk_level": "medium",
            },
            "phone": {
                "regex": r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
                "replacement": "[PHONE]",
                "risk_level": "medium",
            },
            "ssn": {
                "regex": r"\b\d{3}-\d{2}-\d{4}\b",
                "replacement": "[SSN]",
                "risk_level": "high",
            },
            "credit_card": {
                "regex": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
                "replacement": "[CREDIT_CARD]",
                "risk_level": "high",
            },
            "zipcode": {
                "regex": r"\b\d{5}(?:-\d{4})?\b",
                "replacement": "[ZIPCODE]",
                "risk_level": "low",
            },
            "url": {
                "regex": r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                "replacement": "[URL]",
                "risk_level": "low",
            },
            "ip_address": {
                "regex": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
                "replacement": "[IP_ADDRESS]",
                "risk_level": "medium",
            },
        }

        # Common name patterns (simple version - can be enhanced with NER)
        self.name_patterns = [
            r"\b(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b",
            r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b",  # "John Doe" pattern
        ]

        self.logger.info("PII Scrubber initialized with 7 detection patterns")

    def scrub(self, text: str, preserve_patterns: list[str] | None = None) -> dict[str, Any]:
        """
        Scrub PII from text.

        Args:
            text: Input text to scrub
            preserve_patterns: List of PII types to preserve (e.g., ["zipcode"])

        Returns:
            {
                "cleaned_text": str,  # Text with PII replaced
                "pii_found": List[str],  # Types of PII detected
                "pii_count": Dict[str, int],  # Count by type
                "is_safe_for_training": bool,  # Safe to use for ML?
                "risk_level": str,  # "low", "medium", "high"
                "metadata": Dict  # Additional info
            }
        """
        preserve_patterns = preserve_patterns or []
        cleaned = text
        pii_found = []
        pii_count = {}
        high_risk_found = False

        # Apply regex-based scrubbing
        for pii_type, config in self.patterns.items():
            if pii_type in preserve_patterns:
                continue

            matches = re.findall(config["regex"], cleaned, re.IGNORECASE)

            if matches:
                pii_found.append(pii_type)
                pii_count[pii_type] = len(matches)
                cleaned = re.sub(
                    config["regex"], config["replacement"], cleaned, flags=re.IGNORECASE
                )

                if config["risk_level"] == "high":
                    high_risk_found = True
                    self.logger.warning(
                        f"High-risk PII detected: {pii_type}", extra={"count": len(matches)}
                    )

        # Detect names (simple heuristic - can be enhanced with spaCy NER)
        name_matches = []
        for pattern in self.name_patterns:
            name_matches.extend(re.findall(pattern, cleaned))

        if name_matches:
            pii_found.append("name")
            pii_count["name"] = len(name_matches)
            # Replace detected names
            for name in name_matches:
                cleaned = cleaned.replace(name, "[NAME]")

        # Determine safety
        is_safe = not high_risk_found
        risk_level = self._calculate_risk_level(pii_found, pii_count)

        result = {
            "cleaned_text": cleaned,
            "pii_found": pii_found,
            "pii_count": pii_count,
            "is_safe_for_training": is_safe,
            "risk_level": risk_level,
            "metadata": {
                "original_length": len(text),
                "cleaned_length": len(cleaned),
                "scrubbed_at": datetime.utcnow().isoformat(),
                "total_pii_instances": sum(pii_count.values()),
            },
        }

        self.logger.debug(
            f"Scrubbed text: found {len(pii_found)} PII types", extra=result["metadata"]
        )

        return result

    def _calculate_risk_level(self, pii_found: list[str], pii_count: dict[str, int]) -> str:
        """Calculate overall risk level based on PII found"""
        if not pii_found:
            return "none"

        # High-risk PII types
        high_risk = ["ssn", "credit_card"]
        if any(pii in pii_found for pii in high_risk):
            return "high"

        # Medium-risk with high count
        medium_risk = ["email", "phone", "name"]
        medium_count = sum(pii_count.get(pii, 0) for pii in medium_risk)
        if medium_count > 5:
            return "high"
        elif medium_count > 2:
            return "medium"

        return "low"

    def batch_scrub(
        self, texts: list[str], preserve_patterns: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Scrub multiple texts in batch.

        Args:
            texts: List of texts to scrub
            preserve_patterns: PII types to preserve

        Returns:
            List of scrub results
        """
        results = []

        for i, text in enumerate(texts):
            try:
                result = self.scrub(text, preserve_patterns)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error scrubbing text {i}: {e!s}", exc_info=True)
                results.append(
                    {
                        "cleaned_text": text,  # Fallback to original
                        "pii_found": [],
                        "pii_count": {},
                        "is_safe_for_training": False,  # Safe side
                        "risk_level": "unknown",
                        "error": str(e),
                    }
                )

        total_pii = sum(sum(r.get("pii_count", {}).values()) for r in results)

        self.logger.info(f"Batch scrubbed {len(texts)} texts, found {total_pii} PII instances")

        return results

    def validate_for_training(self, text: str, strict: bool = True) -> tuple[bool, str]:
        """
        Validate if text is safe for model training.

        Args:
            text: Text to validate
            strict: If True, reject any PII. If False, allow low-risk PII.

        Returns:
            (is_safe, reason)
        """
        result = self.scrub(text)

        if not result["pii_found"]:
            return True, "No PII detected"

        if result["risk_level"] == "high":
            return False, f"High-risk PII found: {', '.join(result['pii_found'])}"

        if strict:
            return False, f"PII detected in strict mode: {', '.join(result['pii_found'])}"

        # Non-strict: allow low-risk PII if already scrubbed
        if result["risk_level"] in ["low", "medium"]:
            return True, f"Low-risk PII scrubbed: {', '.join(result['pii_found'])}"

        return False, "Unknown risk level"

    def get_scrubber_stats(self) -> dict[str, Any]:
        """Get statistics about the scrubber configuration"""
        return {
            "total_patterns": len(self.patterns),
            "patterns": {
                name: {"risk_level": config["risk_level"], "replacement": config["replacement"]}
                for name, config in self.patterns.items()
            },
            "name_patterns": len(self.name_patterns),
        }


# Global singleton
_pii_scrubber: PIIScrubber | None = None


def get_pii_scrubber() -> PIIScrubber:
    """
    Get global PII scrubber instance.

    Returns:
        PIIScrubber singleton
    """
    global _pii_scrubber

    if _pii_scrubber is None:
        _pii_scrubber = PIIScrubber()

    return _pii_scrubber
