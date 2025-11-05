# Models package init
"""
Unified database models with single declarative base.

This module provides a single declarative_base() instance that all models
must use to avoid cross-Base relationship issues and mapper initialization errors.

Architecture:
- Single Base for all models across all schemas (core, identity, public, lead, newsletter)
- Schema isolation via __table_args__ = {"schema": "schema_name"}
- Proper ForeignKey references using fully qualified names (schema.table.column)

IMPORTANT: Models are NOT automatically imported here to avoid circular imports.
Import them directly from their modules as needed:
  - from api.app.auth.station_models import Station
  - from api.app.auth.models import User
  - from api.app.models.core import Customer, Booking, Payment
  - etc.
"""

# Only export Base - do NOT import model classes here
from .declarative_base import Base

__all__ = ["Base"]
