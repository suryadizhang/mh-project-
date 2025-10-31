"""
Chef Availability & Dynamic Slot Management Service
Handles real-time availability based on chef schedules and existing bookings
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, or_

# Import models (will need to create chef-related models)
from api.app.models.core import Booking

logger = logging.getLogger(__name__)


class ChefAvailabilityService:
    """
    Dynamic chef availability system that calculates real-time booking slots
    
    Features:
    - Configure chef count per date/time slot
    - Multiple bookings per slot (one per chef)
    - Holiday/special date overrides
    - Real-time availability checking
    - Station-based slot management
    
    Example: December 24, 2025
    - 4 time slots: 12pm, 3pm, 6pm, 9pm
    - Only 1 chef available = max 1 booking per slot (total 4 bookings)
    - 3 chefs but only 2 at 6pm = 3 bookings at 12/3/9, but only 2 at 6pm
    """
    
    # Standard time slots (24-hour format)
    STANDARD_SLOTS = [
        "12:00",  # 12 PM
        "15:00",  # 3 PM
        "18:00",  # 6 PM
        "21:00",  # 9 PM
    ]
    
    # Default chef capacity (if not configured)
    DEFAULT_CHEFS_PER_SLOT = 3
    
    def __init__(self, db: Session, station_id: Optional[str] = None):
        """
        Initialize availability service
        
        Args:
            db: SQLAlchemy database session
            station_id: Station ID for multi-tenant support (optional)
        """
        self.db = db
        self.station_id = station_id
    
    def get_available_slots(
        self,
        target_date: date,
        location_zone: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get available booking slots for a specific date
        
        Args:
            target_date: Date to check availability
            location_zone: Optional location zone for chef filtering
        
        Returns:
            List of available slots with chef capacity
        """
        available_slots = []
        
        for slot_time in self.STANDARD_SLOTS:
            # Get chef capacity for this date/time
            chef_capacity = self._get_chef_capacity(target_date, slot_time)
            
            # Get current bookings for this slot
            current_bookings = self._get_bookings_count(target_date, slot_time)
            
            # Calculate availability
            available_count = chef_capacity - current_bookings
            is_available = available_count > 0
            
            slot_info = {
                "date": target_date.isoformat(),
                "time": slot_time,
                "display_time": self._format_time_display(slot_time),
                "chef_capacity": chef_capacity,
                "current_bookings": current_bookings,
                "available_slots": available_count,
                "is_available": is_available,
                "is_full": not is_available,
                "booking_ids": self._get_booking_ids(target_date, slot_time) if current_bookings > 0 else []
            }
            
            available_slots.append(slot_info)
        
        return available_slots
    
    def check_slot_available(
        self,
        target_date: date,
        slot_time: str,
        location_zone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if a specific slot is available for booking
        
        Args:
            target_date: Date to check
            slot_time: Time slot (e.g., "18:00")
            location_zone: Optional location zone
        
        Returns:
            Dict with availability status
        """
        chef_capacity = self._get_chef_capacity(target_date, slot_time)
        current_bookings = self._get_bookings_count(target_date, slot_time)
        available_count = chef_capacity - current_bookings
        
        return {
            "available": available_count > 0,
            "capacity": chef_capacity,
            "booked": current_bookings,
            "remaining": available_count,
            "date": target_date.isoformat(),
            "time": slot_time,
            "display_time": self._format_time_display(slot_time),
            "reason": self._get_unavailable_reason(chef_capacity, current_bookings) if available_count <= 0 else None
        }
    
    def find_next_available_slots(
        self,
        start_date: date,
        count: int = 5,
        location_zone: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find next available booking slots starting from a date
        
        Args:
            start_date: Date to start searching
            count: Number of available slots to find
            location_zone: Optional location zone
        
        Returns:
            List of next available slots
        """
        available_slots = []
        current_date = start_date
        max_days_ahead = 90  # Search up to 3 months ahead
        days_checked = 0
        
        while len(available_slots) < count and days_checked < max_days_ahead:
            day_slots = self.get_available_slots(current_date, location_zone)
            
            for slot in day_slots:
                if slot["is_available"]:
                    available_slots.append(slot)
                    
                    if len(available_slots) >= count:
                        break
            
            current_date += timedelta(days=1)
            days_checked += 1
        
        return available_slots
    
    def suggest_alternative_dates(
        self,
        requested_date: date,
        requested_time: str,
        alternatives_count: int = 3
    ) -> Dict[str, Any]:
        """
        Suggest alternative dates/times if requested slot is unavailable
        
        Args:
            requested_date: Originally requested date
            requested_time: Originally requested time slot
            alternatives_count: Number of alternatives to suggest
        
        Returns:
            Dict with availability status and alternatives
        """
        slot_check = self.check_slot_available(requested_date, requested_time)
        
        if slot_check["available"]:
            return {
                "requested_available": True,
                "slot": slot_check,
                "alternatives": []
            }
        
        # Find alternatives
        alternatives = []
        
        # 1. Try same day, different times
        same_day_slots = self.get_available_slots(requested_date)
        for slot in same_day_slots:
            if slot["is_available"] and slot["time"] != requested_time:
                alternatives.append({
                    "type": "same_day_different_time",
                    "date": slot["date"],
                    "time": slot["time"],
                    "display_time": slot["display_time"],
                    "available_slots": slot["available_slots"]
                })
        
        # 2. Try next week, same day of week, same time
        if len(alternatives) < alternatives_count:
            next_week = requested_date + timedelta(weeks=1)
            next_week_check = self.check_slot_available(next_week, requested_time)
            if next_week_check["available"]:
                alternatives.append({
                    "type": "next_week_same_time",
                    "date": next_week.isoformat(),
                    "time": requested_time,
                    "display_time": self._format_time_display(requested_time),
                    "available_slots": next_week_check["remaining"]
                })
        
        # 3. Try next available slots
        if len(alternatives) < alternatives_count:
            next_available = self.find_next_available_slots(
                requested_date + timedelta(days=1),
                count=alternatives_count - len(alternatives)
            )
            
            for slot in next_available:
                alternatives.append({
                    "type": "next_available",
                    "date": slot["date"],
                    "time": slot["time"],
                    "display_time": slot["display_time"],
                    "available_slots": slot["available_slots"]
                })
        
        return {
            "requested_available": False,
            "requested_slot": slot_check,
            "reason": slot_check["reason"],
            "alternatives": alternatives[:alternatives_count]
        }
    
    def _get_chef_capacity(self, target_date: date, slot_time: str) -> int:
        """
        Get chef capacity for a specific date/time
        
        This will query the chef_schedule table (to be created)
        For now, returns default capacity
        
        Args:
            target_date: Date to check
            slot_time: Time slot
        
        Returns:
            int: Number of chefs available
        """
        # TODO: Query chef_schedule table when created
        # Example query:
        # SELECT chef_count FROM chef_schedule
        # WHERE date = target_date AND time_slot = slot_time
        # AND station_id = self.station_id
        
        # For now, return default
        # Special handling for holidays (example: Christmas Eve)
        if target_date.month == 12 and target_date.day == 24:
            # Christmas Eve - reduced capacity
            return 1
        
        return self.DEFAULT_CHEFS_PER_SLOT
    
    def _get_bookings_count(self, target_date: date, slot_time: str) -> int:
        """
        Get count of confirmed bookings for a date/time slot
        
        Args:
            target_date: Date to check
            slot_time: Time slot
        
        Returns:
            int: Number of bookings
        """
        try:
            # Convert date and time to datetime for comparison
            target_datetime = datetime.combine(target_date, datetime.strptime(slot_time, "%H:%M").time())
            
            # Query bookings
            query = select(func.count(Booking.id)).where(
                and_(
                    Booking.date >= target_datetime,
                    Booking.date < target_datetime + timedelta(hours=1),
                    Booking.slot == slot_time,
                    or_(
                        Booking.status == "confirmed",
                        Booking.status == "deposit_pending"
                    ),
                    Booking.cancelled_at == None
                )
            )
            
            if self.station_id:
                query = query.where(Booking.station_id == self.station_id)
            
            result = self.db.execute(query).scalar()
            return result or 0
            
        except Exception as e:
            logger.error(f"Error counting bookings: {e}")
            return 0
    
    def _get_booking_ids(self, target_date: date, slot_time: str) -> List[str]:
        """
        Get IDs of bookings for a date/time slot
        
        Args:
            target_date: Date to check
            slot_time: Time slot
        
        Returns:
            List of booking IDs
        """
        try:
            target_datetime = datetime.combine(target_date, datetime.strptime(slot_time, "%H:%M").time())
            
            query = select(Booking.id).where(
                and_(
                    Booking.date >= target_datetime,
                    Booking.date < target_datetime + timedelta(hours=1),
                    Booking.slot == slot_time,
                    or_(
                        Booking.status == "confirmed",
                        Booking.status == "deposit_pending"
                    ),
                    Booking.cancelled_at == None
                )
            )
            
            if self.station_id:
                query = query.where(Booking.station_id == self.station_id)
            
            result = self.db.execute(query).scalars().all()
            return [str(booking_id) for booking_id in result]
            
        except Exception as e:
            logger.error(f"Error fetching booking IDs: {e}")
            return []
    
    def _format_time_display(self, time_24h: str) -> str:
        """
        Convert 24-hour time to 12-hour display format
        
        Args:
            time_24h: Time in HH:MM format (e.g., "18:00")
        
        Returns:
            str: Formatted time (e.g., "6:00 PM")
        """
        try:
            time_obj = datetime.strptime(time_24h, "%H:%M").time()
            return time_obj.strftime("%-I:%M %p" if hasattr(time, 'strftime') else "%I:%M %p")
        except Exception:
            return time_24h
    
    def _get_unavailable_reason(self, capacity: int, current_bookings: int) -> str:
        """
        Generate human-readable reason for unavailability
        
        Args:
            capacity: Chef capacity
            current_bookings: Current booking count
        
        Returns:
            str: Reason message
        """
        if capacity == 0:
            return "No chefs scheduled for this date/time"
        elif current_bookings >= capacity:
            return f"Fully booked ({current_bookings}/{capacity} slots filled)"
        else:
            return "Slot unavailable"


# Singleton instance
_availability_service_instance: Optional[ChefAvailabilityService] = None


def get_availability_service(db: Session, station_id: Optional[str] = None) -> ChefAvailabilityService:
    """
    Get or create availability service instance
    
    Args:
        db: SQLAlchemy database session
        station_id: Optional station ID
    
    Returns:
        ChefAvailabilityService instance
    """
    global _availability_service_instance
    
    # Always create new instance with DB session
    # (DB sessions shouldn't be reused across requests)
    return ChefAvailabilityService(db, station_id)


# Example usage
if __name__ == "__main__":
    from datetime import date
    
    # Example: Check Christmas Eve 2025
    print("=== CHECKING CHRISTMAS EVE AVAILABILITY ===")
    print("Date: December 24, 2025")
    print("Slots: 12pm, 3pm, 6pm, 9pm")
    print("Chef Capacity: 1 (reduced for holiday)")
    print("\nResult: Only 1 booking per slot = maximum 4 bookings total")
    print("\nIf customer requests 6pm and it's full:")
    print("- Suggest 12pm, 3pm, or 9pm on same day")
    print("- Or suggest December 26 (day after Christmas)")
