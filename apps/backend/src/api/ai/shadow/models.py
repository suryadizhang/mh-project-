"""
Shadow Learning Database Models - DEPRECATED

⚠️ CRITICAL: This file contained duplicate model definitions that caused SQLAlchemy errors:
  "Multiple classes found for path 'AIRLHFScore' in the registry of this declarative base"

MIGRATED TO: db.models.ai.shadow_learning
- AITutorPair → Use db.models.ai.AITutorPair
- AIRLHFScore → Use db.models.ai.AIRLHFScore
- AIExportJob → Use db.models.ai.AIExportJob

This file now re-exports from canonical location for backward compatibility.
"""

import warnings

warnings.warn(
    "api.ai.shadow.models is deprecated. Use db.models.ai instead. "
    "This module will be removed to prevent SQLAlchemy duplicate class errors.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from canonical location to maintain backward compatibility
from db.models.ai import AITutorPair, AIRLHFScore, AIExportJob, ExportStatus


__all__ = ["AITutorPair", "AIRLHFScore", "AIExportJob", "ExportStatus"]
