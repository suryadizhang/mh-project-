"""
SQLAlchemy Base Class - Import Facade
======================================

DEPRECATED: This module is now an import facade for backward compatibility.

All models MUST use the unified Base from core.database to avoid metadata fragmentation.
This facade ensures old imports still work during migration.

Enterprise Pattern: Single Source of Truth
- ONE canonical Base: core.database.Base
- ALL models share same metadata registry
- Import facades provide backward compatibility

Migration Path:
- OLD: from db.base_class import Base  # DEPRECATED
- NEW: from core.database import Base  # RECOMMENDED

Why This Matters:
- Prevents "NoReferencedTableError" in alembic migrations
- Ensures foreign keys resolve across schemas
- Maintains single metadata object for SQLAlchemy
- Industry standard (Google, Uber, Shopify pattern)
"""

# CRITICAL: Import facade - redirects to unified Base
# DO NOT define a new Base class here - it causes metadata fragmentation
from core.database import Base

# Re-export for backward compatibility
__all__ = ["Base"]
