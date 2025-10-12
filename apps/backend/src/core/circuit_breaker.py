"""
Circuit Breaker Pattern - Prevent Cascade Failures
Protects external service calls (Stripe, RingCentral, etc.) from cascade failures
"""
from typing import Optional, Callable, Any
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Circuit is open, requests fail immediately
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls
    
    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: After timeout, allow test requests to check recovery
    
    Example:
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=httpx.HTTPError
        )
        
        @breaker.call
        async def call_external_api():
            response = await httpx.get("https://api.example.com")
            return response.json()
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type that counts as failure
            success_threshold: Successful calls needed in HALF_OPEN before closing
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.utcnow()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Async function to call
            *args, **kwargs: Arguments to pass to function
        
        Returns:
            Function result
        
        Raises:
            CircuitBreakerError: If circuit is open
        """
        # Check if we should attempt the call
        if self.state == CircuitState.OPEN:
            if not self._should_attempt_reset():
                raise CircuitBreakerError(
                    f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}. "
                    f"Will retry after {self.recovery_timeout}s"
                )
            else:
                # Transition to HALF_OPEN
                self._transition_to_half_open()
        
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Success - record it
            self._on_success()
            
            return result
            
        except self.expected_exception as e:
            # Expected failure - record it
            self._on_failure()
            raise
        
        except Exception as e:
            # Unexpected exception - don't count against circuit breaker
            logger.warning(f"Unexpected exception in circuit breaker: {type(e).__name__}")
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout
    
    def _transition_to_half_open(self):
        """Transition from OPEN to HALF_OPEN state"""
        logger.info("Circuit breaker transitioning to HALF_OPEN")
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.last_state_change = datetime.utcnow()
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(f"Circuit breaker success in HALF_OPEN: {self.success_count}/{self.success_threshold}")
            
            if self.success_count >= self.success_threshold:
                # Enough successes - close the circuit
                self._close_circuit()
        
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        logger.warning(f"Circuit breaker failure count: {self.failure_count}/{self.failure_threshold}")
        
        if self.state == CircuitState.HALF_OPEN:
            # Failed during recovery attempt - open circuit again
            self._open_circuit()
        
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                # Too many failures - open circuit
                self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit"""
        logger.error(f"Circuit breaker OPENING after {self.failure_count} failures")
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.utcnow()
    
    def _close_circuit(self):
        """Close the circuit"""
        logger.info("Circuit breaker CLOSING after successful recovery")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = datetime.utcnow()
    
    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change": self.last_state_change.isoformat(),
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }
    
    def reset(self):
        """Manually reset circuit breaker"""
        logger.info("Circuit breaker manually reset")
        self._close_circuit()


# Global circuit breakers for common services
_circuit_breakers = {}


def get_circuit_breaker(
    service_name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception
) -> CircuitBreaker:
    """
    Get or create a circuit breaker for a service
    
    Example:
        stripe_breaker = get_circuit_breaker(
            "stripe",
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=stripe.error.StripeError
        )
    """
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception
        )
    
    return _circuit_breakers[service_name]


def circuit_breaker(
    service_name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception
):
    """
    Decorator to add circuit breaker protection to async functions
    
    Example:
        @circuit_breaker("stripe", failure_threshold=5, recovery_timeout=60)
        async def charge_customer(amount):
            return await stripe.Charge.create(amount=amount)
    """
    def decorator(func: Callable):
        breaker = get_circuit_breaker(
            service_name,
            failure_threshold,
            recovery_timeout,
            expected_exception
        )
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        return wrapper
    
    return decorator


# Retry with exponential backoff (complements circuit breaker)
async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
):
    """
    Retry function with exponential backoff
    
    Use this INSIDE circuit breaker calls for transient failures
    
    Example:
        @circuit_breaker("external_api")
        async def call_api():
            return await retry_with_backoff(
                lambda: httpx.get("https://api.example.com"),
                max_retries=3
            )
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await func()
        
        except Exception as e:
            last_exception = e
            
            if attempt == max_retries - 1:
                # Last attempt - raise exception
                raise
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            
            logger.warning(
                f"Retry attempt {attempt + 1}/{max_retries} failed: {e}. "
                f"Retrying in {delay}s"
            )
            
            await asyncio.sleep(delay)
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


# Health check for all circuit breakers
def get_all_circuit_breakers_status() -> dict:
    """Get status of all registered circuit breakers"""
    return {
        name: breaker.get_state()
        for name, breaker in _circuit_breakers.items()
    }


# Example usage patterns
class ExternalServiceClient:
    """Example client with circuit breaker protection"""
    
    def __init__(self):
        self.stripe_breaker = get_circuit_breaker(
            "stripe",
            failure_threshold=5,
            recovery_timeout=60
        )
        self.ringcentral_breaker = get_circuit_breaker(
            "ringcentral",
            failure_threshold=3,
            recovery_timeout=30
        )
    
    async def charge_customer(self, amount: float) -> dict:
        """Charge customer with circuit breaker protection"""
        return await self.stripe_breaker.call(
            self._do_stripe_charge,
            amount
        )
    
    async def _do_stripe_charge(self, amount: float) -> dict:
        """Actual Stripe API call"""
        # Implementation here
        pass
    
    async def send_sms(self, phone: str, message: str) -> dict:
        """Send SMS with circuit breaker protection"""
        return await self.ringcentral_breaker.call(
            self._do_send_sms,
            phone,
            message
        )
    
    async def _do_send_sms(self, phone: str, message: str) -> dict:
        """Actual RingCentral API call"""
        # Implementation here
        pass
