"""
Availability Service Module

Handles availability calendar and booking capacity checks.
Provides AI agents with real-time availability information.

Created: 2025-11-12
"""
import logging
from datetime import date, time, timedelta
from typing import Dict, List, Optional, Any

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.knowledge_base import AvailabilityCalendar

logger = logging.getLogger(__name__)


class AvailabilityService:
    """Service for managing availability calendar"""
    
    def __init__(self, db: AsyncSession, station_id: Optional[str] = None):
        self.db = db
        self.station_id = station_id
    
    async def check_availability(
        self,
        event_date: date,
        time_slot: Optional[time] = None,
        guest_count: int = 1
    ) -> Dict[str, Any]:
        """
        Check availability for a date/time
        
        Args:
            event_date: Requested date
            time_slot: Optional time slot
            guest_count: Number of guests
            
        Returns:
            Availability information
        """
        try:
            conditions = [
                AvailabilityCalendar.date == event_date,
                or_(
                    AvailabilityCalendar.station_id == self.station_id,
                    AvailabilityCalendar.station_id == None
                )
            ]
            
            if time_slot:
                conditions.append(AvailabilityCalendar.time_slot == time_slot)
            
            stmt = select(AvailabilityCalendar).where(and_(*conditions))
            
            result = await self.db.execute(stmt)
            slots = result.scalars().all()
            
            if not slots:
                # No calendar entry = available (default behavior)
                return {
                    "available": True,
                    "capacity": 50,  # Default capacity
                    "message": "Available"
                }
            
            # Check each slot
            available_slots = []
            for slot in slots:
                if not slot.is_available:
                    continue
                
                available_capacity = slot.max_capacity - slot.booked_capacity
                if available_capacity >= guest_count:
                    available_slots.append({
                        "time": slot.time_slot.isoformat() if slot.time_slot else None,
                        "capacity": available_capacity,
                        "max_capacity": slot.max_capacity
                    })
            
            if available_slots:
                return {
                    "available": True,
                    "slots": available_slots,
                    "message": f"Available - {len(available_slots)} time slot(s)"
                }
            else:
                return {
                    "available": False,
                    "message": "Fully booked for this date"
                }
        
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return {
                "available": True,  # Fail open
                "message": "Unable to check availability"
            }
    
    async def get_next_available_dates(
        self, 
        days_ahead: int = 30, 
        limit: int = 10
    ) -> List[date]:
        """
        Get next available dates
        
        Args:
            days_ahead: How many days to look ahead
            limit: Maximum number of dates to return
            
        Returns:
            List of available dates
        """
        try:
            start_date = date.today()
            end_date = start_date + timedelta(days=days_ahead)
            
            stmt = select(AvailabilityCalendar).where(
                and_(
                    AvailabilityCalendar.date >= start_date,
                    AvailabilityCalendar.date <= end_date,
                    AvailabilityCalendar.is_available == True,
                    AvailabilityCalendar.booked_capacity < AvailabilityCalendar.max_capacity
                )
            ).order_by(AvailabilityCalendar.date).limit(limit)
            
            result = await self.db.execute(stmt)
            slots = result.scalars().all()
            
            # Get unique dates
            available_dates = list(set(slot.date for slot in slots))
            available_dates.sort()
            
            return available_dates[:limit]
        
        except Exception as e:
            logger.error(f"Error fetching next available dates: {e}")
            return []
