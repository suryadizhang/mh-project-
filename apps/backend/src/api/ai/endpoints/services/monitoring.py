"""
Monitoring Service
Provides comprehensive observability for agent-aware AI system.
Handles logging, metrics, PII masking, audit trails, and performance monitoring.
"""

from datetime import datetime, timezone, timedelta
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class MonitoringService:
    """Comprehensive monitoring and observability service."""

    def __init__(self):
        self.audit_log = []
        self.metrics = {
            "requests": {"total": 0, "by_agent": {}, "by_model": {}, "by_hour": {}, "errors": 0},
            "performance": {
                "avg_response_time": 0.0,
                "total_response_time": 0.0,
                "request_count": 0,
            },
            "costs": {"total": 0.0, "by_agent": {}, "by_model": {}},
        }

        # PII patterns for masking
        self.pii_patterns = {
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
            "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "credit_card": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
            "address": re.compile(
                r"\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b",
                re.IGNORECASE,
            ),
        }

        # Circuit breaker states
        self.circuit_breakers = {}

        # Performance thresholds
        self.thresholds = {
            "response_time_warning": 5000,  # 5 seconds
            "response_time_critical": 10000,  # 10 seconds
            "error_rate_warning": 0.05,  # 5%
            "error_rate_critical": 0.10,  # 10%
            "cost_warning": 10.0,  # $10 per hour
            "cost_critical": 50.0,  # $50 per hour
        }

    async def log_request(
        self,
        message_id: str,
        agent: str,
        user_id: str | None,
        message: str,
        context: dict[str, Any] | None = None,
    ):
        """
        Log incoming request with PII masking.

        Args:
            message_id: Unique message identifier
            agent: Agent handling the request
            user_id: User identifier
            message: User message
            context: Additional context
        """
        try:
            # Mask PII in message
            masked_message = self.mask_pii(message)

            # Create audit log entry
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "request",
                "message_id": message_id,
                "agent": agent,
                "user_id": user_id,
                "message": masked_message,
                "message_length": len(message),
                "context": self._sanitize_context(context),
                "ip_address": context.get("ip_address") if context else None,
                "user_agent": context.get("user_agent") if context else None,
            }

            # Store in audit log
            self.audit_log.append(log_entry)

            # Update metrics
            self._update_request_metrics(agent)

            # Log to standard logger
            logger.info(f"Request logged: {message_id} from agent {agent}")

        except Exception as e:
            logger.exception(f"Error logging request: {e}")

    async def log_response(
        self, message_id: str, agent: str, response: Any, processing_time: float
    ):
        """
        Log AI response with performance metrics.

        Args:
            message_id: Message identifier
            agent: Agent that handled the request
            response: Response object
            processing_time: Processing time in seconds
        """
        try:
            # Extract response content safely
            response_content = ""
            if hasattr(response, "content"):
                response_content = str(response.content)
            elif isinstance(response, dict):
                response_content = response.get("content", "")
            else:
                response_content = str(response)

            # Mask PII in response
            masked_response = self.mask_pii(response_content)

            # Create audit log entry
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "response",
                "message_id": message_id,
                "agent": agent,
                "response": masked_response,
                "response_length": len(response_content),
                "processing_time_ms": processing_time * 1000,
                "model_used": getattr(response, "model_used", "unknown"),
                "confidence": getattr(response, "confidence", 0.0),
                "cost": getattr(response, "cost", {}),
            }

            # Store in audit log
            self.audit_log.append(log_entry)

            # Update performance metrics
            self._update_performance_metrics(processing_time)

            # Update cost metrics
            if hasattr(response, "cost") and response.cost:
                self._update_cost_metrics(
                    agent, getattr(response, "model_used", "unknown"), response.cost
                )

            # Check performance thresholds
            await self._check_performance_thresholds(processing_time)

            logger.info(f"Response logged: {message_id} processed in {processing_time:.3f}s")

        except Exception as e:
            logger.exception(f"Error logging response: {e}")

    async def log_error(
        self, message_id: str, agent: str, error: str, context: dict[str, Any] | None = None
    ):
        """
        Log error with context information.

        Args:
            message_id: Message identifier
            agent: Agent that encountered the error
            error: Error message
            context: Error context
        """
        try:
            # Create audit log entry
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "error",
                "message_id": message_id,
                "agent": agent,
                "error": error,
                "context": self._sanitize_context(context),
                "stack_trace": None,  # Could be added in production
            }

            # Store in audit log
            self.audit_log.append(log_entry)

            # Update error metrics
            self.metrics["requests"]["errors"] += 1

            # Check error rate thresholds
            await self._check_error_rate_thresholds()

            logger.error(f"Error logged for {message_id}: {error}")

        except Exception as e:
            logger.exception(f"Error logging error: {e}")

    def mask_pii(self, text: str) -> str:
        """
        Mask personally identifiable information in text.

        Args:
            text: Input text potentially containing PII

        Returns:
            Text with PII masked
        """
        try:
            masked_text = text

            # Apply PII masking patterns
            for pii_type, pattern in self.pii_patterns.items():
                if pii_type == "email":
                    masked_text = pattern.sub("[EMAIL_MASKED]", masked_text)
                elif pii_type == "phone":
                    masked_text = pattern.sub("[PHONE_MASKED]", masked_text)
                elif pii_type == "ssn":
                    masked_text = pattern.sub("[SSN_MASKED]", masked_text)
                elif pii_type == "credit_card":
                    masked_text = pattern.sub("[CARD_MASKED]", masked_text)
                elif pii_type == "address":
                    masked_text = pattern.sub("[ADDRESS_MASKED]", masked_text)

            return masked_text

        except Exception as e:
            logger.exception(f"PII masking error: {e}")
            return "[MASKING_ERROR]"

    def _sanitize_context(self, context: dict[str, Any] | None) -> dict[str, Any]:
        """Sanitize context to remove sensitive information."""
        if not context:
            return {}

        sanitized = {}
        sensitive_keys = ["password", "token", "secret", "key", "authorization"]

        for key, value in context.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str):
                sanitized[key] = self.mask_pii(value)
            else:
                sanitized[key] = value

        return sanitized

    def _update_request_metrics(self, agent: str):
        """Update request metrics."""
        self.metrics["requests"]["total"] += 1

        # By agent
        if agent not in self.metrics["requests"]["by_agent"]:
            self.metrics["requests"]["by_agent"][agent] = 0
        self.metrics["requests"]["by_agent"][agent] += 1

        # By hour
        current_hour = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:00")
        if current_hour not in self.metrics["requests"]["by_hour"]:
            self.metrics["requests"]["by_hour"][current_hour] = 0
        self.metrics["requests"]["by_hour"][current_hour] += 1

    def _update_performance_metrics(self, response_time: float):
        """Update performance metrics."""
        self.metrics["performance"]["total_response_time"] += response_time
        self.metrics["performance"]["request_count"] += 1
        self.metrics["performance"]["avg_response_time"] = (
            self.metrics["performance"]["total_response_time"]
            / self.metrics["performance"]["request_count"]
        )

    def _update_cost_metrics(self, agent: str, model: str, cost: dict[str, float]):
        """Update cost metrics."""
        total_cost = cost.get("total", 0.0)
        self.metrics["costs"]["total"] += total_cost

        # By agent
        if agent not in self.metrics["costs"]["by_agent"]:
            self.metrics["costs"]["by_agent"][agent] = 0.0
        self.metrics["costs"]["by_agent"][agent] += total_cost

        # By model
        if model not in self.metrics["costs"]["by_model"]:
            self.metrics["costs"]["by_model"][model] = 0.0
        self.metrics["costs"]["by_model"][model] += total_cost

    async def _check_performance_thresholds(self, response_time: float):
        """Check if performance thresholds are exceeded."""
        response_time_ms = response_time * 1000

        if response_time_ms > self.thresholds["response_time_critical"]:
            logger.critical(f"Critical response time: {response_time_ms}ms")
        elif response_time_ms > self.thresholds["response_time_warning"]:
            logger.warning(f"Slow response time: {response_time_ms}ms")

    async def _check_error_rate_thresholds(self):
        """Check if error rate thresholds are exceeded."""
        if self.metrics["requests"]["total"] > 0:
            error_rate = self.metrics["requests"]["errors"] / self.metrics["requests"]["total"]

            if error_rate > self.thresholds["error_rate_critical"]:
                logger.critical(f"Critical error rate: {error_rate:.2%}")
            elif error_rate > self.thresholds["error_rate_warning"]:
                logger.warning(f"High error rate: {error_rate:.2%}")

    async def get_metrics_summary(self, time_range: str | None = None) -> dict[str, Any]:
        """
        Get comprehensive metrics summary.

        Args:
            time_range: Optional time range filter (e.g., "1h", "24h", "7d")

        Returns:
            Metrics summary
        """
        try:
            # Calculate time filter
            cutoff_time = None
            if time_range:
                if time_range == "1h":
                    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
                elif time_range == "24h":
                    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
                elif time_range == "7d":
                    cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)

            # Filter audit log if time range specified
            filtered_logs = self.audit_log
            if cutoff_time:
                filtered_logs = [
                    log
                    for log in self.audit_log
                    if datetime.fromisoformat(log["timestamp"]) > cutoff_time
                ]

            # Calculate filtered metrics
            filtered_metrics = self._calculate_filtered_metrics(filtered_logs)

            # Get current system status
            system_status = await self._get_system_status()

            return {
                "summary": {
                    "total_requests": len(
                        [log for log in filtered_logs if log["event_type"] == "request"]
                    ),
                    "total_errors": len(
                        [log for log in filtered_logs if log["event_type"] == "error"]
                    ),
                    "error_rate": self._calculate_error_rate(filtered_logs),
                    "avg_response_time": filtered_metrics.get("avg_response_time", 0.0),
                    "total_cost": filtered_metrics.get("total_cost", 0.0),
                },
                "by_agent": filtered_metrics.get("by_agent", {}),
                "by_model": filtered_metrics.get("by_model", {}),
                "system_status": system_status,
                "time_range": time_range or "all",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.exception(f"Error generating metrics summary: {e}")
            return {"error": str(e), "generated_at": datetime.now(timezone.utc).isoformat()}

    def _calculate_filtered_metrics(self, logs: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate metrics from filtered logs."""
        by_agent = {}
        by_model = {}
        total_response_time = 0.0
        response_count = 0
        total_cost = 0.0

        for log in logs:
            if log["event_type"] == "request":
                agent = log["agent"]
                if agent not in by_agent:
                    by_agent[agent] = {"requests": 0, "errors": 0}
                by_agent[agent]["requests"] += 1

            elif log["event_type"] == "response":
                response_count += 1
                total_response_time += log.get("processing_time_ms", 0.0)

                model = log.get("model_used", "unknown")
                if model not in by_model:
                    by_model[model] = {"responses": 0, "total_cost": 0.0}
                by_model[model]["responses"] += 1

                cost = log.get("cost", {})
                if isinstance(cost, dict):
                    cost_value = cost.get("total", 0.0)
                    total_cost += cost_value
                    by_model[model]["total_cost"] += cost_value

            elif log["event_type"] == "error":
                agent = log["agent"]
                if agent not in by_agent:
                    by_agent[agent] = {"requests": 0, "errors": 0}
                by_agent[agent]["errors"] += 1

        return {
            "by_agent": by_agent,
            "by_model": by_model,
            "avg_response_time": total_response_time / max(response_count, 1),
            "total_cost": total_cost,
        }

    def _calculate_error_rate(self, logs: list[dict[str, Any]]) -> float:
        """Calculate error rate from logs."""
        requests = len([log for log in logs if log["event_type"] == "request"])
        errors = len([log for log in logs if log["event_type"] == "error"])

        if requests == 0:
            return 0.0

        return errors / requests

    async def _get_system_status(self) -> dict[str, Any]:
        """Get current system status."""
        try:
            # Calculate current metrics
            total_requests = self.metrics["requests"]["total"]
            total_errors = self.metrics["requests"]["errors"]
            error_rate = total_errors / max(total_requests, 1)
            avg_response_time = self.metrics["performance"]["avg_response_time"]

            # Determine status
            status = "healthy"
            issues = []

            if error_rate > self.thresholds["error_rate_critical"]:
                status = "critical"
                issues.append(f"Critical error rate: {error_rate:.2%}")
            elif error_rate > self.thresholds["error_rate_warning"]:
                status = "warning"
                issues.append(f"High error rate: {error_rate:.2%}")

            if avg_response_time * 1000 > self.thresholds["response_time_critical"]:
                status = "critical"
                issues.append(f"Critical response time: {avg_response_time * 1000:.0f}ms")
            elif avg_response_time * 1000 > self.thresholds["response_time_warning"]:
                if status != "critical":
                    status = "warning"
                issues.append(f"Slow response time: {avg_response_time * 1000:.0f}ms")

            return {
                "status": status,
                "issues": issues,
                "uptime": "unknown",  # Would be calculated from service start time
                "memory_usage": "unknown",  # Would be actual memory monitoring
                "cpu_usage": "unknown",  # Would be actual CPU monitoring
            }

        except Exception as e:
            return {
                "status": "error",
                "issues": [f"Status check error: {e!s}"],
                "uptime": "unknown",
                "memory_usage": "unknown",
                "cpu_usage": "unknown",
            }

    async def get_audit_trail(
        self,
        message_id: str | None = None,
        agent: str | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get audit trail with optional filtering.

        Args:
            message_id: Filter by message ID
            agent: Filter by agent
            user_id: Filter by user ID
            limit: Maximum number of entries

        Returns:
            Filtered audit trail entries
        """
        try:
            filtered_logs = self.audit_log

            # Apply filters
            if message_id:
                filtered_logs = [
                    log for log in filtered_logs if log.get("message_id") == message_id
                ]

            if agent:
                filtered_logs = [log for log in filtered_logs if log.get("agent") == agent]

            if user_id:
                filtered_logs = [log for log in filtered_logs if log.get("user_id") == user_id]

            # Sort by timestamp (newest first) and limit
            filtered_logs.sort(key=lambda x: x["timestamp"], reverse=True)

            return filtered_logs[:limit]

        except Exception as e:
            logger.exception(f"Error getting audit trail: {e}")
            return []

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on monitoring service."""
        try:
            return {
                "healthy": True,
                "audit_log_size": len(self.audit_log),
                "total_requests": self.metrics["requests"]["total"],
                "total_errors": self.metrics["requests"]["errors"],
                "last_check": datetime.now(timezone.utc),
            }

        except Exception as e:
            return {"healthy": False, "error": str(e), "last_check": datetime.now(timezone.utc)}
