"""
Station model re-export for backward compatibility.
"""

from core.auth.station_models import Station, StationUser

__all__ = ["Station", "StationUser"]
