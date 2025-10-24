"""
Unified SQLAlchemy declarative base for all models.

This file MUST NOT import any other model files to avoid circular imports.
Import Base from THIS file in all model files, not from __init__.py.
"""
from sqlalchemy.orm import declarative_base

# Single unified Base for ALL models across all schemas
# This eliminates the multiple declarative_base() issue that caused mapper errors
Base = declarative_base()
