"""
Availability Service Module

Handles availability calendar and booking capacity checks.
Provides AI agents with real-time availability information.

Uses AvailabilityEngine for accurate chef availability counts.

Created: 2025-11-12
Updated: 2025-01-30 - Integrated with AvailabilityEngine for real chef counts
"""

import logging
from datetime import date, time, timedelta
from typing import Dict, List, Optional, Any

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

# MIGRATED: from models.knowledge_base → db.models.knowledge_base
from db.models.knowledge_base import AvailabilityCalendar

logger = logging.getLogger(__name__)


class AvailabilityService:
    """Service for managing availability calendar"""

    def __init__(self, db: AsyncSession, station_id: Optional[str] = None):
        self.db = db
        self.station_id = station_id

    async def check_availability(
        self, event_date: date, time_slot: Optional[time] = None, guest_count: int = 1
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
                    AvailabilityCalendar.station_id == None,
                ),
            ]

            if time_slot:
                conditions.append(AvailabilityCalendar.time_slot == time_slot)

            stmt = select(AvailabilityCalendar).where(and_(*conditions))

            result = await self.db.execute(stmt)
            slots = result.scalars().all()

            if not slots:
                # No calendar entry exists - get real capacity from chef availability
                capacity = await self._get_chef_capacity(event_date, time_slot)
                return {
                    "available": True,
                    "capacity": capacity,
                    "message": "Available",
                }

            # Check each slot
            available_slots = []
            for slot in slots:
                if not slot.is_available:
                    continue

                available_capacity = slot.max_capacity - slot.booked_capacity
                if available_capacity >= guest_count:
                    available_slots.append(
                        {
                            "time": slot.time_slot.isoformat() if slot.time_slot else None,
                            "capacity": available_capacity,
                            "max_capacity": slot.max_capacity,
                        }
                    )

            if available_slots:
                return {
                    "available": True,
                    "slots": available_slots,
                    "message": f"Available - {len(available_slots)} time slot(s)",
                }
            else:
                return {"available": False, "message": "Fully booked for this date"}

        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return {"available": True, "message": "Unable to check availability"}  # Fail open

    async def get_next_available_dates(self, days_ahead: int = 30, limit: int = 10) -> List[date]:
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

            stmt = (
                select(AvailabilityCalendar)
                .where(
                    and_(
                        AvailabilityCalendar.date >= start_date,
                        AvailabilityCalendar.date <= end_date,
                        AvailabilityCalendar.is_available == True,
                        AvailabilityCalendar.booked_capacity < AvailabilityCalendar.max_capacity,
                    )
                )
                .order_by(AvailabilityCalendar.date)
                .limit(limit)
            )

            result = await self.db.execute(stmt)
            slots = result.scalars().all()

            # Get unique dates
            available_dates = list(set(slot.date for slot in slots))
            available_dates.sort()

            return available_dates[:limit]

        except Exception as e:
            logger.error(f"Error fetching next available dates: {e}")
            return []

    async def _get_chef_capacity(self, event_date: date, time_slot: Optional[time] = None) -> int:
        """
        Get capacity based on available chefs for a given date/time.

        Queries the ops.chef_availability and ops.chef_timeoff tables
        to determine how many chefs can work on the requested date/time.

        Args:
            event_date: The date to check availability for
            time_slot: Optional specific time slot to check

        Returns:
            Number of available chefs (capacity)
        """
        from db.models.ops import (
            Chef,
            ChefAvailability,
            ChefTimeOff,
            ChefStatus,
            DayOfWeek,
            TimeOffStatus,
        )
        from sqlalchemy import not_

        try:
            # Map Python weekday (0=Monday) to our DayOfWeek enum
            day_names = [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]
            day_of_week = DayOfWeek(day_names[event_date.weekday()])

            # Base query: active chefs with availability on this day of week
            availability_query = (
                select(ChefAvailability.chef_id)
                .join(Chef, Chef.id == ChefAvailability.chef_id)
                .where(
                    and_(
                        Chef.status == ChefStatus.ACTIVE,
                        Chef.is_active == True,
                        ChefAvailability.day_of_week == day_of_week,
                        ChefAvailability.is_available == True,
                    )
                )
            )

            # If time_slot specified, filter by time range
            if time_slot:
                availability_query = availability_query.where(
                    and_(
                        ChefAvailability.start_time <= time_slot,
                        ChefAvailability.end_time >= time_slot,
                    )
                )

            # Get chefs who have approved time off on this date
            timeoff_subquery = select(ChefTimeOff.chef_id).where(
                and_(
                    ChefTimeOff.start_date <= event_date,
                    ChefTimeOff.end_date >= event_date,
                    ChefTimeOff.status == TimeOffStatus.APPROVED,
                )
            )

            # Exclude chefs with approved time off
            final_query = availability_query.where(
                not_(ChefAvailability.chef_id.in_(timeoff_subquery))
            ).distinct()

            result = await self.db.execute(final_query)
            available_chef_ids = result.scalars().all()

            capacity = len(available_chef_ids)
            logger.debug(f"Chef capacity for {event_date} {time_slot}: {capacity} chefs available")

            return capacity if capacity > 0 else 1  # Return at least 1 to avoid division issues

        except Exception as e:
            logger.error(f"Error getting chef capacity: {e}")
            # Fallback to a reasonable default if query fails
            return 3
