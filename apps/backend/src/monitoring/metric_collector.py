"""
MetricCollector - Gather metrics from all sources

Collects metrics from:
1. System (CPU, memory, disk, network)
2. Database (query duration, connections, locks)
3. Application (API response times, error rates)
4. Business (bookings, revenue, conversions)

Stores metrics in Redis with TTL and publishes to pub/sub channel.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.config import settings
from core.database import SessionLocal

logger = logging.getLogger(__name__)


class MetricCollector:
    """
    Collects metrics from various sources and stores in Redis
    
    Features:
    - System metrics (CPU, memory, disk)
    - Database metrics (query performance, connections)
    - Application metrics (API response times, errors)
    - Business metrics (bookings, revenue)
    - Redis storage with TTL
    - Pub/sub notifications for real-time monitoring
    """
    
    METRIC_TTL = 300  # 5 minutes
    REDIS_CHANNEL = "metrics:updates"
    
    def __init__(self, db: Optional[Session] = None, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis = redis_client or redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def collect_all_metrics(self) -> Dict[str, float]:
        """
        Collect all available metrics
        
        Returns:
            Dictionary of metric_name: value
        """
        metrics = {}
        
        try:
            metrics.update(self.collect_system_metrics())
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
        
        try:
            metrics.update(self.collect_database_metrics())
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
        
        try:
            metrics.update(self.collect_application_metrics())
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
        
        try:
            metrics.update(self.collect_business_metrics())
        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}")
        
        try:
            metrics.update(self.collect_ai_metrics())
        except Exception as e:
            logger.error(f"Error collecting AI metrics: {e}")
        
        # Store all metrics in Redis
        for metric_name, value in metrics.items():
            self.push_metric(metric_name, value)
        
        return metrics
    
    def collect_critical_metrics_only(self) -> Dict[str, float]:
        """
        Collect only critical metrics (for IDLE state)
        
        Critical metrics:
        - System health (CPU, memory)
        - Database availability
        - Service availability
        
        Returns:
            Dictionary of metric_name: value
        """
        metrics = {}
        
        try:
            # System basics
            metrics["cpu_percent"] = psutil.cpu_percent(interval=1)
            metrics["memory_percent"] = psutil.virtual_memory().percent
            
            # Database availability
            if self.db:
                try:
                    self.db.execute(text("SELECT 1"))
                    metrics["database_available"] = 1.0
                except:
                    metrics["database_available"] = 0.0
            
        except Exception as e:
            logger.error(f"Error collecting critical metrics: {e}")
        
        # Store metrics
        for metric_name, value in metrics.items():
            self.push_metric(metric_name, value)
        
        return metrics
    
    def push_metric(self, metric_name: str, value: float):
        """
        Store metric in Redis and publish to channel
        
        Args:
            metric_name: Name of the metric (e.g., "cpu_percent")
            value: Metric value
        """
        try:
            # Store metric with TTL
            key = f"metric:{metric_name}"
            self.redis.setex(key, self.METRIC_TTL, str(value))
            
            # Publish to channel for real-time monitoring
            message = json.dumps({
                "metric_name": metric_name,
                "value": value,
                "timestamp": time.time()
            })
            self.redis.publish(self.REDIS_CHANNEL, message)
            
            # Update metric history (for pattern analysis)
            self._update_metric_history(metric_name, value)
            
        except Exception as e:
            logger.error(f"Error pushing metric {metric_name}: {e}")
    
    def get_metric_value(self, metric_name: str) -> Optional[float]:
        """
        Get current metric value from Redis
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Metric value or None if not found
        """
        try:
            key = f"metric:{metric_name}"
            value = self.redis.get(key)
            return float(value) if value else None
        except Exception as e:
            logger.error(f"Error getting metric {metric_name}: {e}")
            return None
    
    # ========================================================================
    # SYSTEM METRICS
    # ========================================================================
    
    def collect_system_metrics(self) -> Dict[str, float]:
        """
        Collect system resource metrics
        
        Returns:
            Dictionary of system metrics
        """
        metrics = {}
        
        try:
            # CPU
            metrics["cpu_percent"] = psutil.cpu_percent(interval=1)
            metrics["cpu_count"] = psutil.cpu_count()
            
            # Load average (Unix-like systems)
            if hasattr(psutil, "getloadavg"):
                load_avg = psutil.getloadavg()
                metrics["load_average_1m"] = load_avg[0]
                metrics["load_average_5m"] = load_avg[1]
                metrics["load_average_15m"] = load_avg[2]
            
            # Memory
            memory = psutil.virtual_memory()
            metrics["memory_percent"] = memory.percent
            metrics["memory_used_gb"] = memory.used / (1024 ** 3)
            metrics["memory_available_gb"] = memory.available / (1024 ** 3)
            
            # Disk
            disk = psutil.disk_usage('/')
            metrics["disk_percent"] = disk.percent
            metrics["disk_used_gb"] = disk.used / (1024 ** 3)
            metrics["disk_free_gb"] = disk.free / (1024 ** 3)
            
            # Network
            net_io = psutil.net_io_counters()
            metrics["network_sent_mb"] = net_io.bytes_sent / (1024 ** 2)
            metrics["network_recv_mb"] = net_io.bytes_recv / (1024 ** 2)
            
            # Process count
            metrics["process_count"] = len(psutil.pids())
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
        
        return metrics
    
    # ========================================================================
    # DATABASE METRICS
    # ========================================================================
    
    def collect_database_metrics(self) -> Dict[str, float]:
        """
        Collect database performance metrics
        
        Returns:
            Dictionary of database metrics
        """
        metrics = {}
        
        if not self.db:
            return metrics
        
        try:
            # Database availability
            self.db.execute(text("SELECT 1"))
            metrics["database_available"] = 1.0
            
            # Connection pool usage (from SQLAlchemy)
            pool = self.db.get_bind().pool
            metrics["db_connection_pool_size"] = pool.size()
            metrics["db_connection_pool_checked_out"] = pool.checkedout()
            pool_usage = (pool.checkedout() / pool.size() * 100) if pool.size() > 0 else 0
            metrics["db_connection_pool_usage_percent"] = pool_usage
            
            # Active connections
            result = self.db.execute(text("""
                SELECT count(*) as active_connections
                FROM pg_stat_activity
                WHERE state = 'active'
            """))
            row = result.fetchone()
            metrics["db_active_connections"] = float(row[0]) if row else 0
            
            # Slow queries (queries running > 1 second)
            result = self.db.execute(text("""
                SELECT count(*) as slow_queries
                FROM pg_stat_activity
                WHERE state = 'active'
                AND query_start < NOW() - INTERVAL '1 second'
                AND query NOT LIKE '%pg_stat_activity%'
            """))
            row = result.fetchone()
            metrics["db_slow_queries_count"] = float(row[0]) if row else 0
            
            # Lock waits
            result = self.db.execute(text("""
                SELECT count(*) as lock_waits
                FROM pg_stat_activity
                WHERE wait_event_type = 'Lock'
            """))
            row = result.fetchone()
            metrics["db_lock_waits"] = float(row[0]) if row else 0
            
            # Database size
            result = self.db.execute(text("""
                SELECT pg_database_size(current_database()) / (1024.0 * 1024.0) as size_mb
            """))
            row = result.fetchone()
            metrics["db_size_mb"] = float(row[0]) if row else 0
            
            # Transaction rate (commits + rollbacks per second)
            result = self.db.execute(text("""
                SELECT
                    xact_commit + xact_rollback as transactions
                FROM pg_stat_database
                WHERE datname = current_database()
            """))
            row = result.fetchone()
            if row:
                # Store for rate calculation
                prev_key = "metric:db_transactions_prev"
                prev_value = self.redis.get(prev_key)
                current_value = float(row[0])
                
                if prev_value:
                    # Calculate rate (transactions per second)
                    rate = (current_value - float(prev_value)) / 30  # 30s interval
                    metrics["db_transactions_per_second"] = max(0, rate)
                
                self.redis.setex(prev_key, 60, str(current_value))
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            metrics["database_available"] = 0.0
        
        return metrics
    
    # ========================================================================
    # APPLICATION METRICS
    # ========================================================================
    
    def collect_application_metrics(self) -> Dict[str, float]:
        """
        Collect application performance metrics
        
        Returns:
            Dictionary of application metrics
        """
        metrics = {}
        
        try:
            # API response times (from Redis tracking)
            response_times = self._get_response_time_stats()
            metrics.update(response_times)
            
            # Error rate
            error_rate = self._get_error_rate()
            metrics["api_error_rate_percent"] = error_rate
            
            # Request rate
            request_rate = self._get_request_rate()
            metrics["api_requests_per_minute"] = request_rate
            
            # Active sessions (if tracked in Redis)
            active_sessions = self.redis.scard("active_sessions") or 0
            metrics["active_sessions"] = float(active_sessions)
            
            # Cache hit rate (if using Redis cache)
            cache_hits = float(self.redis.get("cache:hits") or 0)
            cache_misses = float(self.redis.get("cache:misses") or 0)
            total_requests = cache_hits + cache_misses
            cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
            metrics["cache_hit_rate_percent"] = cache_hit_rate
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
        
        return metrics
    
    def _get_response_time_stats(self) -> Dict[str, float]:
        """Get response time statistics from Redis"""
        metrics = {}
        
        try:
            # Get response times from last minute
            times_key = "metrics:response_times:minute"
            times = self.redis.lrange(times_key, 0, -1)
            
            if times:
                times_float = [float(t) for t in times]
                times_float.sort()
                
                count = len(times_float)
                metrics["api_response_time_avg_ms"] = sum(times_float) / count
                metrics["api_response_time_min_ms"] = times_float[0]
                metrics["api_response_time_max_ms"] = times_float[-1]
                
                # Percentiles
                p50_idx = int(count * 0.50)
                p95_idx = int(count * 0.95)
                p99_idx = int(count * 0.99)
                
                metrics["api_response_time_p50_ms"] = times_float[p50_idx]
                metrics["api_response_time_p95_ms"] = times_float[p95_idx]
                metrics["api_response_time_p99_ms"] = times_float[p99_idx]
            
        except Exception as e:
            logger.error(f"Error calculating response time stats: {e}")
        
        return metrics
    
    def _get_error_rate(self) -> float:
        """Calculate error rate from Redis counters"""
        try:
            errors = float(self.redis.get("metrics:errors:minute") or 0)
            requests = float(self.redis.get("metrics:requests:minute") or 0)
            
            if requests > 0:
                return (errors / requests) * 100
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating error rate: {e}")
            return 0.0
    
    def _get_request_rate(self) -> float:
        """Get request rate from Redis counter"""
        try:
            requests = float(self.redis.get("metrics:requests:minute") or 0)
            return requests
            
        except Exception as e:
            logger.error(f"Error getting request rate: {e}")
            return 0.0
    
    # ========================================================================
    # BUSINESS METRICS
    # ========================================================================
    
    def collect_business_metrics(self) -> Dict[str, float]:
        """
        Collect business performance metrics
        
        Returns:
            Dictionary of business metrics
        """
        metrics = {}
        
        if not self.db:
            return metrics
        
        try:
            # Bookings in last hour
            result = self.db.execute(text("""
                SELECT COUNT(*) as booking_count
                FROM bookings
                WHERE created_at > NOW() - INTERVAL '1 hour'
            """))
            row = result.fetchone()
            metrics["bookings_last_hour"] = float(row[0]) if row else 0
            
            # Booking conversion rate (bookings / sessions * 100)
            sessions = float(self.redis.get("metrics:sessions:hour") or 1)
            bookings = metrics.get("bookings_last_hour", 0)
            metrics["booking_conversion_rate_percent"] = (bookings / sessions * 100) if sessions > 0 else 0
            
            # Revenue in last hour
            result = self.db.execute(text("""
                SELECT COALESCE(SUM(total_amount), 0) as revenue
                FROM bookings
                WHERE created_at > NOW() - INTERVAL '1 hour'
                AND status = 'confirmed'
            """))
            row = result.fetchone()
            metrics["revenue_last_hour"] = float(row[0]) if row else 0
            
            # Active customers (logged in last 15 minutes)
            result = self.db.execute(text("""
                SELECT COUNT(DISTINCT user_id) as active_users
                FROM user_sessions
                WHERE last_activity > NOW() - INTERVAL '15 minutes'
            """))
            row = result.fetchone()
            metrics["active_users"] = float(row[0]) if row else 0
            
            # Pending bookings (waiting confirmation)
            result = self.db.execute(text("""
                SELECT COUNT(*) as pending_bookings
                FROM bookings
                WHERE status = 'pending'
            """))
            row = result.fetchone()
            metrics["pending_bookings"] = float(row[0]) if row else 0
            
        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}")
        
        return metrics
    
    def collect_ai_metrics(self) -> Dict[str, float]:
        """
        Collect AI-specific metrics
        
        Metrics:
        - AI API cost (hourly, daily, monthly)
        - AI request count and rate
        - AI average latency
        - AI error rate
        - AI token usage (input, output)
        - AI escalation rate (to humans)
        - AI quality metrics (confidence, accuracy)
        
        Returns:
            Dictionary of AI metrics
        """
        metrics = {}
        
        try:
            if not self.db:
                return metrics
            
            # Get hourly AI usage (last 60 minutes)
            result = self.db.execute(text("""
                SELECT 
                    COUNT(*) as request_count,
                    COALESCE(SUM(cost_usd), 0) as total_cost,
                    COALESCE(AVG(input_tokens + output_tokens), 0) as avg_tokens,
                    COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                    COALESCE(SUM(output_tokens), 0) as total_output_tokens
                FROM ai_usage
                WHERE created_at >= NOW() - INTERVAL '1 hour'
            """))
            row = result.fetchone()
            
            if row:
                metrics["ai_requests_last_hour"] = float(row[0])
                metrics["ai_cost_per_hour_usd"] = float(row[1])
                metrics["ai_avg_tokens_per_request"] = float(row[2])
                metrics["ai_input_tokens_per_hour"] = float(row[3])
                metrics["ai_output_tokens_per_hour"] = float(row[4])
                
                # Calculate requests per minute
                if row[0] > 0:
                    metrics["ai_requests_per_minute"] = float(row[0]) / 60.0
                else:
                    metrics["ai_requests_per_minute"] = 0.0
            
            # Get daily AI cost
            result = self.db.execute(text("""
                SELECT COALESCE(SUM(cost_usd), 0) as daily_cost
                FROM ai_usage
                WHERE DATE(created_at) = CURRENT_DATE
            """))
            row = result.fetchone()
            metrics["ai_cost_today_usd"] = float(row[0]) if row else 0.0
            
            # Get monthly AI cost
            result = self.db.execute(text("""
                SELECT COALESCE(SUM(cost_usd), 0) as monthly_cost
                FROM ai_usage
                WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)
            """))
            row = result.fetchone()
            metrics["ai_cost_month_usd"] = float(row[0]) if row else 0.0
            
            # Get AI conversation metrics (last hour)
            result = self.db.execute(text("""
                SELECT 
                    COUNT(DISTINCT conversation_id) as conversation_count,
                    COUNT(DISTINCT customer_id) as unique_customers
                FROM ai_usage
                WHERE created_at >= NOW() - INTERVAL '1 hour'
                AND conversation_id IS NOT NULL
            """))
            row = result.fetchone()
            if row:
                metrics["ai_active_conversations_hour"] = float(row[0])
                metrics["ai_unique_customers_hour"] = float(row[1])
            
            # Get AI model distribution (last hour)
            result = self.db.execute(text("""
                SELECT model, COUNT(*) as count
                FROM ai_usage
                WHERE created_at >= NOW() - INTERVAL '1 hour'
                GROUP BY model
            """))
            model_counts = {}
            for row in result:
                model_name = row[0].replace('-', '_').replace('.', '_')
                model_counts[model_name] = float(row[1])
            
            # Add individual model counts
            for model, count in model_counts.items():
                metrics[f"ai_model_{model}_count"] = count
            
            # Get AI escalation rate (human escalations)
            result = self.db.execute(text("""
                SELECT 
                    COUNT(*) as total_conversations,
                    COALESCE(SUM(CASE WHEN escalated_to_human = true THEN 1 ELSE 0 END), 0) as escalated_count
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '1 hour'
            """))
            row = result.fetchone()
            if row and row[0] > 0:
                metrics["ai_escalation_rate_percent"] = (float(row[1]) / float(row[0])) * 100.0
                metrics["ai_escalations_last_hour"] = float(row[1])
            else:
                metrics["ai_escalation_rate_percent"] = 0.0
                metrics["ai_escalations_last_hour"] = 0.0
            
            # Get AI response quality metrics from Redis (if available)
            try:
                # Average confidence scores (stored by AI system)
                confidence_key = "ai:metrics:avg_confidence:hour"
                avg_confidence = self.redis.get(confidence_key)
                if avg_confidence:
                    metrics["ai_avg_confidence_percent"] = float(avg_confidence)
                
                # AI error rate (from Redis counter)
                ai_errors = self.redis.get("ai:errors:hour") or "0"
                ai_requests = self.redis.get("ai:requests:hour") or "1"
                if int(ai_requests) > 0:
                    metrics["ai_error_rate_percent"] = (float(ai_errors) / float(ai_requests)) * 100.0
                else:
                    metrics["ai_error_rate_percent"] = 0.0
                
                # AI latency metrics (from Redis)
                latency_key = "ai:metrics:avg_latency_ms:hour"
                avg_latency = self.redis.get(latency_key)
                if avg_latency:
                    metrics["ai_avg_latency_ms"] = float(avg_latency)
                
            except Exception as e:
                logger.debug(f"AI Redis metrics not available: {e}")
            
            logger.debug(f"Collected {len(metrics)} AI metrics")
            
        except Exception as e:
            logger.error(f"Error collecting AI metrics: {e}")
        
        return metrics
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _update_metric_history(self, metric_name: str, value: float):
        """
        Update metric history for pattern analysis
        
        Stores last 100 values in Redis sorted set
        """
        try:
            history_key = f"metric:history:{metric_name}"
            timestamp = time.time()
            
            # Add to sorted set (score = timestamp)
            self.redis.zadd(history_key, {str(value): timestamp})
            
            # Keep only last 100 values
            self.redis.zremrangebyrank(history_key, 0, -101)
            
            # Set TTL (24 hours)
            self.redis.expire(history_key, 86400)
            
        except Exception as e:
            logger.error(f"Error updating metric history: {e}")
    
    def get_metric_history(self, metric_name: str, limit: int = 100) -> List[tuple]:
        """
        Get metric history
        
        Args:
            metric_name: Name of the metric
            limit: Maximum number of values to return
            
        Returns:
            List of (value, timestamp) tuples
        """
        try:
            history_key = f"metric:history:{metric_name}"
            data = self.redis.zrange(history_key, -limit, -1, withscores=True)
            return [(float(value), timestamp) for value, timestamp in data]
            
        except Exception as e:
            logger.error(f"Error getting metric history: {e}")
            return []
    
    def get_baseline_value(self, metric_name: str) -> Optional[float]:
        """
        Get baseline (average) value for a metric
        
        Uses last 24 hours of data
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Baseline value or None
        """
        try:
            baseline_key = f"metric:baseline:{metric_name}"
            value = self.redis.get(baseline_key)
            return float(value) if value else None
            
        except Exception as e:
            logger.error(f"Error getting baseline: {e}")
            return None
    
    def update_baseline(self, metric_name: str):
        """
        Update baseline value for a metric
        
        Calculates average from last 24 hours
        """
        try:
            history = self.get_metric_history(metric_name, limit=288)  # 24h @ 5min intervals
            
            if history:
                values = [value for value, _ in history]
                avg_value = sum(values) / len(values)
                
                baseline_key = f"metric:baseline:{metric_name}"
                self.redis.setex(baseline_key, 86400, str(avg_value))  # 24h TTL
                
                logger.info(f"Updated baseline for {metric_name}: {avg_value:.2f}")
                
        except Exception as e:
            logger.error(f"Error updating baseline: {e}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def push_metric_update(metric_name: str, value: float):
    """
    Helper function to push metric update from anywhere in the app
    
    Args:
        metric_name: Name of the metric
        value: Metric value
    """
    try:
        collector = MetricCollector()
        collector.push_metric(metric_name, value)
    except Exception as e:
        logger.error(f"Error pushing metric update: {e}")


def track_response_time(duration_ms: float):
    """
    Track API response time
    
    Args:
        duration_ms: Response time in milliseconds
    """
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        # Add to list for percentile calculation
        redis_client.lpush("metrics:response_times:minute", str(duration_ms))
        redis_client.expire("metrics:response_times:minute", 60)
        redis_client.ltrim("metrics:response_times:minute", 0, 999)  # Keep last 1000
        
        # Increment request counter
        redis_client.incr("metrics:requests:minute")
        redis_client.expire("metrics:requests:minute", 60)
        
        # Push metric for real-time monitoring
        push_metric_update("api_response_time_ms", duration_ms)
        
    except Exception as e:
        logger.error(f"Error tracking response time: {e}")


def track_error():
    """Track API error occurrence"""
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        redis_client.incr("metrics:errors:minute")
        redis_client.expire("metrics:errors:minute", 60)
        
    except Exception as e:
        logger.error(f"Error tracking error: {e}")
