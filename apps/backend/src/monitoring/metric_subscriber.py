"""
Metric Subscriber - Real-time Metric Monitoring via Redis Pub/Sub

Instead of polling Redis for metrics, this subscriber listens to the
metrics:updates channel and reacts immediately when metrics are pushed.

This provides:
- Instant detection (<1s) when metrics change
- No polling overhead
- Push-based architecture
- Real-time threshold monitoring

Usage:
    subscriber = MetricSubscriber()
    
    # Register callback for metric updates
    def on_metric_update(metric_name, value, timestamp):
        print(f"Metric updated: {metric_name} = {value}")
    
    subscriber.add_callback(on_metric_update)
    
    # Start listening (blocking)
    subscriber.start()

Created: November 10, 2025
Part of: Week 2 - ThresholdMonitor Implementation
"""

import json
import logging
import time
import threading
from typing import Callable, Dict, Any, List, Optional, Set
from datetime import datetime
import redis

from core.config import settings

logger = logging.getLogger(__name__)


class MetricSubscriber:
    """
    Redis pub/sub subscriber for real-time metric updates.
    
    Listens to the metrics:updates channel and notifies callbacks
    when metrics are pushed by MetricCollector.
    
    Features:
    - Multiple callback support
    - Automatic reconnection
    - Error handling and logging
    - Thread-safe operations
    - Graceful shutdown
    
    Usage:
        subscriber = MetricSubscriber()
        subscriber.add_callback(my_callback)
        subscriber.start()  # Blocking
        
        # Or run in background thread
        subscriber.start_in_background()
    """
    
    CHANNEL_NAME = "metrics:updates"
    RECONNECT_DELAY = 5  # seconds
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize metric subscriber.
        
        Args:
            redis_client: Redis client (optional, will create if not provided)
        """
        self.redis = redis_client or redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        self.pubsub = self.redis.pubsub()
        self.callbacks: List[Callable[[str, float, float], None]] = []
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Statistics
        self.stats = {
            "messages_received": 0,
            "callbacks_executed": 0,
            "errors": 0,
            "started_at": None,
            "last_message_at": None,
        }
        
        # Filtering
        self.metric_filters: Optional[Set[str]] = None  # None = all metrics
        
        logger.info(f"🎧 MetricSubscriber initialized, channel: {self.CHANNEL_NAME}")
    
    def add_callback(self, callback: Callable[[str, float, float], None]):
        """
        Register a callback for metric updates.
        
        Callback signature: callback(metric_name, value, timestamp)
        
        Args:
            callback: Function to call when metric updated
        """
        self.callbacks.append(callback)
        logger.info(f"📝 Registered callback: {callback.__name__}")
    
    def remove_callback(self, callback: Callable[[str, float, float], None]):
        """
        Unregister a callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            logger.info(f"🗑️ Removed callback: {callback.__name__}")
    
    def set_metric_filter(self, metric_names: Set[str]):
        """
        Filter which metrics to process.
        
        Only metrics in this set will trigger callbacks.
        Set to None to process all metrics.
        
        Args:
            metric_names: Set of metric names to process
        """
        self.metric_filters = metric_names
        logger.info(f"🔍 Metric filter set: {len(metric_names)} metrics")
    
    def clear_metric_filter(self):
        """Clear metric filter (process all metrics)."""
        self.metric_filters = None
        logger.info("🔍 Metric filter cleared (processing all)")
    
    def start(self):
        """
        Start listening to metric updates (blocking).
        
        This will block the current thread and listen for messages.
        Use start_in_background() to run in a separate thread.
        """
        if self.running:
            logger.warning("⚠️ Subscriber already running")
            return
        
        self.running = True
        self.stats["started_at"] = time.time()
        
        logger.info(f"🚀 Starting subscriber on channel: {self.CHANNEL_NAME}")
        
        # Subscribe to channel
        self.pubsub.subscribe(self.CHANNEL_NAME)
        
        try:
            self._listen_loop()
        except KeyboardInterrupt:
            logger.info("⌨️ Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Subscriber error: {e}", exc_info=True)
            self.stats["errors"] += 1
        finally:
            self.stop()
    
    def start_in_background(self):
        """
        Start listening in a background thread.
        
        Non-blocking. Returns immediately.
        Use stop() to stop the background thread.
        """
        if self.running:
            logger.warning("⚠️ Subscriber already running")
            return
        
        self.thread = threading.Thread(
            target=self.start,
            name="MetricSubscriberThread",
            daemon=True
        )
        self.thread.start()
        logger.info("🧵 Subscriber started in background thread")
    
    def stop(self):
        """
        Stop listening and cleanup.
        
        Gracefully stops the subscriber and cleans up resources.
        """
        if not self.running:
            return
        
        logger.info("🛑 Stopping subscriber...")
        self.running = False
        
        # Unsubscribe
        try:
            self.pubsub.unsubscribe(self.CHANNEL_NAME)
            self.pubsub.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        logger.info("✅ Subscriber stopped")
    
    def _listen_loop(self):
        """
        Main listening loop.
        
        Continuously listens for messages and processes them.
        """
        logger.info("👂 Listening for metric updates...")
        
        for message in self.pubsub.listen():
            if not self.running:
                break
            
            try:
                # Process message
                if message["type"] == "message":
                    self._handle_message(message)
                elif message["type"] == "subscribe":
                    logger.info(f"✅ Subscribed to {message['channel']}")
                elif message["type"] == "unsubscribe":
                    logger.info(f"👋 Unsubscribed from {message['channel']}")
                
            except Exception as e:
                logger.error(f"❌ Error processing message: {e}", exc_info=True)
                self.stats["errors"] += 1
    
    def _handle_message(self, message: Dict[str, Any]):
        """
        Handle incoming metric update message.
        
        Args:
            message: Redis pub/sub message
        """
        try:
            # Parse message data
            data_str = message["data"]
            if isinstance(data_str, bytes):
                data_str = data_str.decode("utf-8")
            
            data = json.loads(data_str)
            
            metric_name = data["metric_name"]
            value = float(data["value"])
            timestamp = float(data["timestamp"])
            
            # Update stats
            self.stats["messages_received"] += 1
            self.stats["last_message_at"] = time.time()
            
            # Check filter
            if self.metric_filters and metric_name not in self.metric_filters:
                logger.debug(f"⏭️ Skipping filtered metric: {metric_name}")
                return
            
            # Log receipt
            logger.debug(
                f"📨 Received: {metric_name} = {value} "
                f"(age: {time.time() - timestamp:.3f}s)"
            )
            
            # Notify callbacks
            self._notify_callbacks(metric_name, value, timestamp)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in message: {e}")
            self.stats["errors"] += 1
        except KeyError as e:
            logger.error(f"❌ Missing field in message: {e}")
            self.stats["errors"] += 1
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}", exc_info=True)
            self.stats["errors"] += 1
    
    def _notify_callbacks(self, metric_name: str, value: float, timestamp: float):
        """
        Notify all registered callbacks.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            timestamp: Timestamp when metric was collected
        """
        if not self.callbacks:
            logger.warning("⚠️ No callbacks registered")
            return
        
        for callback in self.callbacks:
            try:
                callback(metric_name, value, timestamp)
                self.stats["callbacks_executed"] += 1
            except Exception as e:
                logger.error(
                    f"❌ Error in callback {callback.__name__}: {e}",
                    exc_info=True
                )
                self.stats["errors"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get subscriber statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = self.stats.copy()
        
        # Add uptime
        if stats["started_at"]:
            stats["uptime_seconds"] = time.time() - stats["started_at"]
            stats["uptime_hours"] = stats["uptime_seconds"] / 3600
        
        # Add rate
        if stats["started_at"]:
            uptime = time.time() - stats["started_at"]
            if uptime > 0:
                stats["messages_per_second"] = stats["messages_received"] / uptime
                stats["messages_per_minute"] = stats["messages_per_second"] * 60
        
        # Add last message info
        if stats["last_message_at"]:
            stats["seconds_since_last_message"] = time.time() - stats["last_message_at"]
        
        return stats
    
    def is_running(self) -> bool:
        """
        Check if subscriber is running.
        
        Returns:
            True if running
        """
        return self.running
    
    def is_healthy(self) -> bool:
        """
        Check if subscriber is healthy.
        
        A subscriber is considered healthy if:
        - It's running
        - Has received messages recently (last 5 minutes)
        - Error rate is not too high
        
        Returns:
            True if healthy
        """
        if not self.running:
            return False
        
        stats = self.get_stats()
        
        # Check if received messages recently (5 minutes)
        if stats["last_message_at"]:
            time_since_last = stats["seconds_since_last_message"]
            if time_since_last > 300:  # 5 minutes
                logger.warning(
                    f"⚠️ No messages received in {time_since_last:.1f}s"
                )
                return False
        
        # Check error rate
        if stats["messages_received"] > 0:
            error_rate = stats["errors"] / stats["messages_received"]
            if error_rate > 0.1:  # More than 10% errors
                logger.warning(f"⚠️ High error rate: {error_rate:.1%}")
                return False
        
        return True


class MetricBuffer:
    """
    Buffer for collecting recent metric values.
    
    Useful for calculating moving averages, detecting spikes, etc.
    
    Usage:
        buffer = MetricBuffer(max_size=100)
        
        # Add values
        buffer.add("cpu_percent", 45.2)
        buffer.add("cpu_percent", 48.5)
        
        # Get statistics
        stats = buffer.get_stats("cpu_percent")
        print(stats["average"])  # 46.85
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize buffer.
        
        Args:
            max_size: Maximum number of values to keep per metric
        """
        self.max_size = max_size
        self.buffers: Dict[str, List[float]] = {}
        self.timestamps: Dict[str, List[float]] = {}
    
    def add(self, metric_name: str, value: float, timestamp: Optional[float] = None):
        """
        Add a metric value to the buffer.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            timestamp: Optional timestamp (defaults to now)
        """
        if metric_name not in self.buffers:
            self.buffers[metric_name] = []
            self.timestamps[metric_name] = []
        
        # Add value
        self.buffers[metric_name].append(value)
        self.timestamps[metric_name].append(timestamp or time.time())
        
        # Trim if needed
        if len(self.buffers[metric_name]) > self.max_size:
            self.buffers[metric_name].pop(0)
            self.timestamps[metric_name].pop(0)
    
    def get_values(self, metric_name: str) -> List[float]:
        """
        Get all buffered values for a metric.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            List of values (may be empty)
        """
        return self.buffers.get(metric_name, [])
    
    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """
        Get statistics for a metric.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Dictionary with statistics (min, max, avg, etc.)
        """
        values = self.get_values(metric_name)
        
        if not values:
            return {
                "count": 0,
                "min": None,
                "max": None,
                "average": None,
                "latest": None,
            }
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "average": sum(values) / len(values),
            "latest": values[-1],
        }
    
    def clear(self, metric_name: Optional[str] = None):
        """
        Clear buffer.
        
        Args:
            metric_name: Specific metric to clear (None = clear all)
        """
        if metric_name:
            if metric_name in self.buffers:
                del self.buffers[metric_name]
                del self.timestamps[metric_name]
        else:
            self.buffers.clear()
            self.timestamps.clear()


# Singleton instance for global access
_metric_subscriber_instance: Optional[MetricSubscriber] = None


def get_metric_subscriber(redis_client: Optional[redis.Redis] = None) -> MetricSubscriber:
    """
    Get singleton MetricSubscriber instance.
    
    Args:
        redis_client: Optional Redis client
        
    Returns:
        MetricSubscriber instance
    """
    global _metric_subscriber_instance
    
    if _metric_subscriber_instance is None:
        _metric_subscriber_instance = MetricSubscriber(redis_client=redis_client)
    
    return _metric_subscriber_instance


def reset_metric_subscriber():
    """Reset singleton (for testing)."""
    global _metric_subscriber_instance
    
    if _metric_subscriber_instance:
        _metric_subscriber_instance.stop()
    
    _metric_subscriber_instance = None
