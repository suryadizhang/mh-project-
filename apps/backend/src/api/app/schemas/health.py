"""
Enhanced health check response schemas for comprehensive monitoring.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Enhanced basic health check response."""

    status: str = Field(..., description="Overall health status")
    service: str = Field(..., description="Service name")
    environment: str = Field(..., description="Environment (dev/staging/prod)")
    version: str = Field(..., description="Service version")
    timestamp: datetime | None = Field(None, description="Check timestamp")
    uptime_seconds: float | None = Field(None, description="Service uptime in seconds")
    database_status: str | None = Field(None, description="Database connection status")
    database_response_time_ms: float | None = Field(None, description="Database response time")
    checks: dict[str, Any] | None = Field(default_factory=dict, description="Detailed checks")


class ReadinessResponse(BaseModel):
    """Enhanced readiness check response."""

    status: str = Field(..., description="Readiness status")
    service: str = Field(..., description="Service name")
    environment: str = Field(..., description="Environment")
    ready: bool | None = Field(None, description="Service is ready to accept traffic")
    timestamp: datetime | None = Field(None, description="Check timestamp")
    checks: dict[str, Any] = Field(default_factory=dict, description="Individual checks")
    database_connected: bool = Field(..., description="Database connectivity")
    stripe_configured: bool = Field(..., description="Stripe configuration status")
    email_configured: bool = Field(..., description="Email configuration status")


class DetailedHealthResponse(BaseModel):
    """Comprehensive health check with system metrics."""

    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Check timestamp")
    environment: str = Field(..., description="Environment")
    version: str = Field(..., description="Service version")
    uptime_seconds: float = Field(..., description="Service uptime")
    database: dict[str, Any] = Field(..., description="Database health details")
    redis: dict[str, Any] | None = Field(None, description="Redis health details")
    external_services: dict[str, Any] = Field(
        default_factory=dict, description="External service checks"
    )
    system_metrics: dict[str, Any] = Field(
        default_factory=dict, description="System performance metrics"
    )


class DatabaseHealth(BaseModel):
    """Database health check details."""

    status: str = Field(..., description="Database status")
    response_time_ms: float | None = Field(None, description="Query response time")
    connection_pool: dict[str, Any] | None = Field(None, description="Connection pool status")
    details: str = Field(..., description="Health check details")


class SystemMetrics(BaseModel):
    """System performance metrics."""

    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    memory: dict[str, float] = Field(..., description="Memory usage details")
    disk: dict[str, float] = Field(..., description="Disk usage details")
    network: dict[str, Any] | None = Field(None, description="Network statistics")


class ExternalServiceHealth(BaseModel):
    """External service health check."""

    status: str = Field(..., description="Service status")
    response_time_ms: float | None = Field(None, description="Response time")
    last_check: datetime = Field(..., description="Last check timestamp")
    details: str | None = Field(None, description="Additional details")
    error: str | None = Field(None, description="Error message if unhealthy")
