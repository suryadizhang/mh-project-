"""
SystemEvent Model

Stores all system events for analytics, auditing, and debugging.
Used by EventService for centralized event tracking.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base
import uuid


class SystemEvent(Base):
    """
    System event tracking for analytics and audit trails.
    
    Stores events from all services including:
    - User actions (login, profile updates, etc.)
    - Business events (lead created, booking confirmed, etc.)
    - System events (errors, warnings, etc.)
    - Audit trail for compliance
    
    Indexed for efficient querying by:
    - entity_type + entity_id (get all events for a specific entity)
    - user_id (get all events for a user)
    - service + action (analytics by service/action)
    - timestamp (chronological queries)
    - severity (error tracking)
    """
    
    __tablename__ = "system_events"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Event identification
    service = Column(String(100), nullable=False, index=True, comment="Service that logged the event (e.g., 'LeadService', 'BookingService')")
    action = Column(String(100), nullable=False, index=True, comment="Action performed (e.g., 'lead_created', 'booking_confirmed')")
    
    # Entity reference (what was acted upon)
    entity_type = Column(String(50), nullable=True, index=True, comment="Type of entity (e.g., 'lead', 'booking', 'user')")
    entity_id = Column(Integer, nullable=True, index=True, comment="ID of the entity")
    
    # User reference (who performed the action)
    user_id = Column(Integer, nullable=True, index=True, comment="User who triggered the event")
    
    # Event data
    metadata = Column(JSON, nullable=False, default=dict, comment="Additional JSON data about the event")
    
    # Event severity
    severity = Column(
        String(20), 
        nullable=False, 
        default="info",
        index=True,
        comment="Event severity: debug, info, warning, error, critical"
    )
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True, comment="When the event occurred")
    
    # Composite indexes for common queries
    __table_args__ = (
        # Get all events for a specific entity
        Index('ix_system_events_entity_lookup', 'entity_type', 'entity_id', 'timestamp'),
        
        # Get all events for a specific user
        Index('ix_system_events_user_timeline', 'user_id', 'timestamp'),
        
        # Analytics: events by service and action
        Index('ix_system_events_service_action', 'service', 'action', 'timestamp'),
        
        # Error tracking: get errors by severity
        Index('ix_system_events_severity_time', 'severity', 'timestamp'),
        
        # Audit trail: chronological events
        Index('ix_system_events_chronological', 'timestamp', 'service'),
    )
    
    def __repr__(self):
        return (
            f"<SystemEvent(id={self.id}, service='{self.service}', "
            f"action='{self.action}', entity_type='{self.entity_type}', "
            f"entity_id={self.entity_id}, timestamp={self.timestamp})>"
        )
    
    def to_dict(self):
        """Convert event to dictionary for API responses."""
        return {
            "id": self.id,
            "service": self.service,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
